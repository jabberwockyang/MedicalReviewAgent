import argparse
import json
import time
import os
import glob
import random
import shutil
from enum import Enum

from multiprocessing import Process, Value

import gradio as gr
import pytoml
from loguru import logger

from huixiangdou.service import Worker, llm_serve, ArticleRetrieval, CacheRetriever, FeatureStore, FileOperation

class PARAM_CODE(Enum):
    """Parameter code."""
    SUCCESS = 0
    FAILED = 1
    ERROR = 2

def parse_args():
    """Parse args."""
    parser = argparse.ArgumentParser(description='Worker.')
    parser.add_argument('--work_dir',
                        type=str,
                        default='workdir',
                        help='Working directory.')
    parser.add_argument('--repo_dir',
                        type=str,
                        default='repodir',
                        help='Repository directory.')
    parser.add_argument(
        '--config_path',
        default='config.ini',
        type=str,
        help='Worker configuration path. Default value is config.ini')
    parser.add_argument('--standalone',
                        action='store_true',
                        default=True,
                        help='Auto deploy required Hybrid LLM Service.')
    args = parser.parse_args()
    return args

def get_ready(query:str,chunksize=None,k=None):
    
    with open(CONFIG_PATH, encoding='utf8') as f:
        config = pytoml.load(f)
    workdir = config['feature_store']['work_dir']
    repodir = config['feature_store']['repo_dir']

    if query == 'repo_work': # no need to return assistant
        return repodir, workdir, config

    with open(os.path.join(config['feature_store']['repo_dir'],'config.json'), 'r') as f:
        repo_config = json.load(f)
    theme = ' '.join(repo_config['keywords'])

    if query == 'annotation':
        if not chunksize or not k:
            raise ValueError('chunksize or k not provided')
        chunkdir = os.path.join(workdir, f'chunksize_{chunksize}')
        clusterdir = os.path.join(chunkdir, 'cluster_features', f'cluster_features_{k}')
        assistant = Worker(work_dir=chunkdir, config_path=CONFIG_PATH,language='en')
        samples_json = os.path.join(clusterdir,'samples.json')
        with open(samples_json, 'r') as f:
            samples = json.load(f)
            f.close()
        return clusterdir, samples, assistant, theme
    
    elif query == 'inspiration':
        if not chunksize or not k:
            raise ValueError('chunksize or k not provided')
        
        chunkdir = os.path.join(workdir, f'chunksize_{chunksize}')
        clusterdir = os.path.join(chunkdir, 'cluster_features', f'cluster_features_{k}')
        assistant = Worker(work_dir=chunkdir, config_path=CONFIG_PATH,language='en')
        annofile = os.path.join(clusterdir,'annotation.jsonl')
        with open(annofile, 'r') as f:
            annoresult = f.readlines()

            f.close()
        annoresult = [json.loads(obj) for obj in annoresult]
        return clusterdir, annoresult, assistant, theme
    elif query == 'summarize': # no need for params k
        if not chunksize:
            raise ValueError('chunksize not provided')
        chunkdir = os.path.join(workdir, f'chunksize_{chunksize}')
        assistant = Worker(work_dir=chunkdir, config_path=CONFIG_PATH,language='en')
        return assistant,theme

    else:
        raise ValueError('query not recognized')
            


def update_repo_info():
    with open(CONFIG_PATH, encoding='utf8') as f:
        config = pytoml.load(f)
    repodir = config['feature_store']['repo_dir']
    if os.path.exists(repodir):
        with open(os.path.join(repodir,'config.json'), 'r') as f:
            repo_config = json.load(f)

        keywords = repo_config['keywords']
        len = repo_config['len']
        retmax = repo_config['retmax']
        
        return keywords,len,retmax
    else:
        return None,None,None
               
   
def generate_articles_repo(keywords:str,retmax:int):
    keys= [k.strip() for k in keywords.split('\n')]
    repodir, workdir, _ = get_ready('repo_work')
    # 文献库只生成一次 所以每次生成文献库都要删除之前的文献库和数据库
    if os.path.exists(repodir):
        shutil.rmtree(repodir)
    if os.path.exists(workdir):
        shutil.rmtree(workdir)

    articelfinder = ArticleRetrieval(keywords = keys,
                                     repo_dir = repodir,
                                     retmax = retmax)
    articelfinder.initiallize()
    keys,len,retmax = update_repo_info()
    newinfo = f"关键词: {keys}\n文献数量: {len}\n获取上限: {retmax}"
    return gr.Textbox(label="文献库概况",lines =1,
                      value = newinfo,visible = True)
def delete_articles_repo():
    # 在这里运行生成数据库的函数
    repodir, workdir, _ = get_ready('repo_work')
    if os.path.exists(repodir):
        shutil.rmtree(repodir)
    if os.path.exists(workdir):
        shutil.rmtree(workdir)

    return gr.Textbox(label="文献库概况",lines =3,
                      value = '文献库和相关数据库已删除',
                      visible = True)

def update_repo():
    keys,len,retmax = update_repo_info()
    if keys:
        newinfo = f"关键词: {keys}\n文献数量: {len}\n获取上限: {retmax}"
    else:
        newinfo = '目前还没有文献库'
    return gr.Textbox(label="文献库概况",lines =1,
                      value = newinfo,
                      visible = True)

def update_database_info():
    with open(CONFIG_PATH, encoding='utf8') as f:
        config = pytoml.load(f)
    workdir = config['feature_store']['work_dir']
    chunkdirs = glob.glob(os.path.join(workdir, 'chunksize_*'))
    chunkdirs.sort()
    list_of_chunksize = [int(chunkdir.split('_')[-1]) for chunkdir in chunkdirs]
    # print(list_of_chunksize)
    jsonobj = {}
    for chunkdir in chunkdirs:
        k_dir = glob.glob(os.path.join(chunkdir, 'cluster_features','cluster_features_*'))
        k_dir.sort()
        list_of_k = [int(k.split('_')[-1]) for k in k_dir]
        jsonobj[int(chunkdir.split('_')[-1])] = list_of_k
        

    new_options = [f"chunksize:{chunksize}, k:{k}" for chunksize in list_of_chunksize for k in jsonobj[chunksize]]
    return new_options, jsonobj


def generate_database(chunksize:int,nclusters:str|list[str]):
    # 在这里运行生成数据库的函数
    repodir, workdir, _ = get_ready('repo_work')
    if not os.path.exists(repodir):
        return gr.Textbox(label="数据库已生成",value = '请先生成文献库',visible = True)
    nclusters = [int(i) for i in nclusters]
    # 文献库和数据库的覆盖删除逻辑待定 
    # 理论上 文献库只能生成一次 所以每次生成文献库都要删除之前的文献库和数据库
    # 数据库可以根据文献库多次生成 暂不做删除 目前没有节省算力的逻辑 重复计算后覆盖 以后优化 
    # 不同的chunksize和nclusters会放在不同的文件夹下 不会互相覆盖
    # if os.path.exists(workdir):
    #     shutil.rmtree(workdir)

    cache = CacheRetriever(config_path=CONFIG_PATH)
    fs_init = FeatureStore(embeddings=cache.embeddings,
                           reranker=cache.reranker,
                            chunk_size=chunksize,
                            n_clusters=nclusters,
                           config_path=CONFIG_PATH)

    # walk all files in repo dir
    file_opr = FileOperation()
    files = file_opr.scan_dir(repo_dir=repodir)
    fs_init.initialize(files=files, work_dir=workdir)
    file_opr.summarize(files)
    del fs_init
    cache.pop('default')
    texts, _ = update_database_info()
    return gr.Textbox(label="数据库概况",value = '\n'.join(texts) ,visible = True)

def delete_database():
    _, workdir, _ = get_ready('repo_work')
    if os.path.exists(workdir):
        shutil.rmtree(workdir)

    return  gr.Textbox(label="数据库概况",lines =3,value = '数据库已删除',visible = True)
def update_database_textbox():
    texts, _ = update_database_info()
    return gr.Textbox(label="数据库概况",value = '\n'.join(texts),visible = True)

def update_chunksize_dropdown():
    _, jsonobj = update_database_info()
    return gr.Dropdown(choices= jsonobj.keys())

def update_ncluster_dropdown(chunksize:int):
    _, jsonobj = update_database_info()
    nclusters = jsonobj[chunksize]
    return gr.Dropdown(choices= nclusters)

def annotation(n,chunksize:int,nclusters:int):
    '''
    use llm to annotate cluster
    n: percentage of clusters to annotate
    '''
    
    clusterdir, samples, assistant, theme = get_ready('annotation',chunksize,nclusters)
    new_obj_list = []
    n = round(n * len(samples.keys()))
    for cluster_no in random.sample(samples.keys(), n):
        chunk = '\n'.join(samples[cluster_no]['samples'][:10])

        code, reply, cluster_no = assistant.annotate_cluster(
                                                theme = theme,
                                                cluster_no=cluster_no,
                                                chunk=chunk,
                                                history=[],
                                                groupname='')
        references = f"cluster_no: {cluster_no}"
        new_obj = {
            'cluster_no': cluster_no,
            'chunk': chunk,
            'annotation': reply
        }
        new_obj_list.append(new_obj)
        logger.info(f'{code}, {query}, {reply}, {references}')

        with open(os.path.join(clusterdir, 'annotation.jsonl'), 'a') as f:
            json.dump(new_obj, f, ensure_ascii=False)
            f.write('\n')
            
    return '\n\n'.join([obj['annotation'] for obj in new_obj_list])


def inspiration(annotation:str,chunksize:int,nclusters:int):

    clusterdir, annoresult, assistant, theme = get_ready('inspiration',chunksize,nclusters)
    new_obj_list = []

    if annotation is not None: # if the user wants to get inspiration from specific clusters only  
        annoresult = [obj for obj in annoresult if obj['annotation'] in [txt.strip() for txt in annotation.split('\n')]]
    
    for index in random.sample(range(len(annoresult)), min(5, len(annoresult))):
        cluster_no = [annoresult[index]['cluster_no']]
        chunks = [annoresult[index]['annotation']]
        chunks = '\n'.join(chunks)
        code, reply = assistant.getinspiration(
                                                theme = theme,
                                                annotations = chunks,
                                                history=[], 
                                                groupname='')
        new_obj = {
            'inspiration': reply,
            'cluster_no': cluster_no
        }
        new_obj_list.append(new_obj)
        logger.info(f'{code}, {query}, {cluster_no},{reply}')

        with open(os.path.join(clusterdir, 'inspiration.jsonl'), 'a') as f:
            json.dump(new_obj, f, ensure_ascii=False)
        with open(os.path.join(clusterdir, 'inspiration.txt'), 'a') as f:
            f.write(f'{reply}\n')
            
    return '\n\n'.join([obj['inspiration'] for obj in new_obj_list])


def getpmcurls(references):
    urls = []
    for ref in references:
        refid = ref.replace('.txt','')
        urls.append(f'https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{refid}/')
    return urls

def summarize_text(query,chunksize:int):

    assistant,_ = get_ready('summarize',chunksize=chunksize,k=None)
    code, reply, references = assistant.generate(query=query,
                                                history=[],
                                                groupname='')
      
    logger.info(f'{code}, {query}, {reply}, {references}')
    urls = getpmcurls(references)
    mds = '\n'.join([f'[{ref}]({url})' for ref,url in zip(references,urls)])
    return reply,mds 

# start service
if __name__ == '__main__':
    args = parse_args()
    CONFIG_PATH = args.config_path
    if args.standalone is True:
        # hybrid llm serve
        server_ready = Value('i', 0)
        server_process = Process(target=llm_serve,
                                args=(args.config_path, server_ready))
        server_process.start()
        while True:
            if server_ready.value == 0:
                logger.info('waiting for server to be ready..')
                time.sleep(3)
            elif server_ready.value == 1:
                break
            else:
                logger.error('start local LLM server failed, quit.')
                raise Exception('local LLM path')
        logger.info('Hybrid LLM Server start.')


    with gr.Blocks() as demo:
        with gr.Tab("文献查找+数据库生成"):
            gr.Markdown("这里可以查找文献，生成数据库")
            input_keys = gr.Textbox(label="感兴趣的关键词",
                                            lines = 3)
            retmax = gr.Slider(
                    minimum=0,
                    maximum=1000,
                    value=500,
                    interactive=True,
                    label="查多少",
                )
            with gr.Row():
                generate_repo_button = gr.Button("生成文献库")
                delete_repo_button = gr.Button("删除文献库")
                update_repo_button = gr.Button("更新文献库情况")

            repo_summary =gr.Textbox(label= '文献库概况', value="目前还没有文献库")
        
            generate_repo_button.click(generate_articles_repo, 
                                inputs=[input_keys,retmax],
                                outputs = [repo_summary])
            
            
            delete_repo_button.click(delete_articles_repo, inputs=None,
                                outputs = repo_summary)
            update_repo_button.click(update_repo, inputs=None,
                                outputs = repo_summary)
            with gr.Accordion("数据库构建参数", open=True):
                gr.Markdown("[如何选择数据库构建参数]('https://github.com/jabberwockyang/MedicalReviewAgent/tree/main')")
                chunksize = gr.Slider(label="Chunk Size",
                                      info= 'How long you want the chunk to be?',
                                        minimum=128, maximum=4096,value=1024,step=1,
                                        interactive=True)
                ncluster = gr.CheckboxGroup(["10", "20", "50", '100','200','500','1000'], 
                                            # default=["20", "50", '100'],
                                            label="Number of Clusters", 
                                            info="How many Clusters you want to generate")

            with gr.Row():
                gene_database_button = gr.Button("生成数据库")
                delete_database_button = gr.Button("删除数据库")
                update_database_button = gr.Button("更新数据库情况")

            database_summary = gr.Textbox(label="数据库概况",lines = 1,value="目前还没有数据库")
            

            gene_database_button.click(generate_database, inputs=[chunksize,ncluster],
                                outputs = database_summary)
            
            update_database_button.click(update_database_textbox,inputs=None,
                                outputs = [database_summary])
                                         
            delete_database_button.click(delete_database, inputs=None,
                                outputs = database_summary)
        with gr.Tab("写综述"):
            gr.Markdown("""
            1. 如果没啥想法 可以依次点击 读读文献 和 获取灵感
            2. 如果有想法 直接输入到 想写什么 点击写综述
            """)

            with gr.Accordion("聚类标注相关参数", open=True):
                with gr.Row():
                    update_options = gr.Button("更新数据库情况", scale=0)
                    chunksize = gr.Dropdown([], label="选择块大小", scale=0)
                    nclusters = gr.Dropdown([], label="选择聚类数", scale=0)
                    ntoread = gr.Slider(
                            minimum=0,maximum=1,value=0.5,
                            interactive=True,
                            label="抽样标注比例",
                        )

            annotation_button = gr.Button("抽样标注文章聚类")
            annotation_output =  gr.Textbox(label="文章聚类标注/片段摘要",
                                            lines = 5, 
                                            interactive= True,
                                            show_copy_button=True)
            inspiration_button = gr.Button("获取灵感")
            inspiration_output = gr.Textbox(label="灵光一现",
                                            lines = 5,
                                            show_copy_button=True)


            query = gr.Textbox(label="想写什么")
            
            write_button = gr.Button("写综述")
            output_text = gr.Textbox(label="看看",lines=10)
            output_references = gr.Textbox(label="参考文献",lines=1)
            
            update_options.click(update_chunksize_dropdown,
                                outputs=[chunksize])
            
            chunksize.change(update_ncluster_dropdown, 
                             inputs=[chunksize],
                             outputs= [nclusters])
            
            annotation_button.click(annotation, 
                                    inputs = [ntoread, chunksize, nclusters],
                                    outputs=[annotation_output])
            
            inspiration_button.click(inspiration, 
                                     inputs= [annotation_output, chunksize, nclusters],
                                     outputs=[inspiration_output])
            
            write_button.click(summarize_text,
                                inputs=[query, chunksize],
                                outputs =[output_text,output_references])


    demo.launch(share=False, server_name='0.0.0.0', debug=True,show_error=True)
