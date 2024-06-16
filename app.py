import argparse
import json
import time
import os
import glob
import random
import shutil
from enum import Enum
from threading import Thread
from multiprocessing import Process, Value

import gradio as gr
import pytoml
from loguru import logger
import spaces

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
    parser.add_argument("--model_downloaded",
                        type=bool,
                        default=False,
                        help="If the model has been downloaded in the root/models folder. Default is False.")
    args = parser.parse_args()
    return args

def update_remote_buttons(remote):
    if remote:
        return [
                gr.Markdown("[如何配置API]('https://github.com/jabberwockyang/MedicalReviewAgent/blob/main/README.md')",
                            visible=True),
                gr.Dropdown(["kimi", "deepseek", "zhipuai",'gpt'],
                                                label="选择大模型提供商",
                                                interactive=True,visible=True),
                gr.Textbox(label="您的API",lines = 1,
                        interactive=True,visible=True),
                gr.Textbox(label="base url",lines = 1,
                        interactive=True,visible=True),
                gr.Dropdown([],label="选择模型",
                            interactive=True,visible=True)
        ]
    else:
        return [
                gr.Markdown("[如何配置API]('https://github.com/jabberwockyang/MedicalReviewAgent/blob/main/README.md')",
                            visible=False),
                gr.Dropdown(["kimi", "deepseek", "zhipuai",'gpt'],
                                                label="选择大模型提供商",
                                                interactive=False,visible=False),
                gr.Textbox(label="您的API",lines = 1,
                        interactive=False,visible=False),
                gr.Dropdown([],label="选择模型",
                            interactive=False,visible=False)
        ]

def udate_model_dropdown(remote_company):
    model_choices = {
        'kimi': ['moonshot-v1-128k'],
        'deepseek': ['deepseek-chat'],
        'zhipuai': ['glm-4'],
        'gpt': ['gpt-4-32k-0613','gpt-3.5-turbo']
    }
    return gr.Dropdown(choices= model_choices[remote_company])

def update_remote_config(remote_ornot,remote_company = None,api = None,baseurl = None, model = None):
    with open(CONFIG_PATH, encoding='utf8') as f:
        config = pytoml.load(f)
         
        if remote_ornot:
            if remote_company == None or api == None or model == None:
                raise ValueError('remote_company, api, model not provided')
            config['llm']['enable_local'] = 0
            config['llm']['enable_remote'] = 1
            config['llm']['server']['remote_type'] = remote_company
            config['llm']['server']['remote_api_key'] = api
            config['llm']['server']['remote_base_url'] = baseurl
            config['llm']['server']['remote_llm_model'] = model
        else:
            config['llm']['enable_local'] = 1
            config['llm']['enable_remote'] = 0
    with open(CONFIG_PATH, 'w') as f:
        pytoml.dump(config, f)
    return gr.Button("配置已保存")

# @spaces.GPU(duration=120)
def get_ready(query:str,chunksize=None,k=None,use_abstract=False):
    
    with open(CONFIG_PATH, encoding='utf8') as f:
        config = pytoml.load(f)
    workdir = config['feature_store']['work_dir']
    repodir = config['feature_store']['repo_dir']

    if query == 'repo_work': # no need to return assistant
        return repodir, workdir, config
    theme = ''
    try:
        with open(os.path.join(config['feature_store']['repo_dir'],'info.json'), 'r') as f:
            repo_info = json.load(f)
        theme = ' '.join(repo_info['keywords'])
    except:
        pass


    if use_abstract:
        workdir = workdir + '_ab'
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
        pdffiles = glob.glob(os.path.join(repodir, '*.pdf'))
        number_of_pdf = len(pdffiles)
        # 判断info.json是否存在
        if os.path.exists(os.path.join(repodir,'info.json')):
                
            with open(os.path.join(repodir,'info.json'), 'r') as f:
                repo_info = json.load(f)

            keywords = repo_info['keywords']
            retmax = repo_info['retmax']
            search_len = len(repo_info['search_pmids'])
            import_len = len(repo_info['import_pmids'])
            failed_pmid_len = len(repo_info['failed_pmids'])

            pmc_success = repo_info['pmc_success_d']
            scihub_success = repo_info['scihub_success_d']
            failed_download = repo_info['failed_download']
            abstract_success = repo_info['abstract_success']
            failed_abstract = repo_info['failed_abstract']

            number_of_upload = number_of_pdf-scihub_success
            return keywords, retmax, search_len, import_len, failed_pmid_len, pmc_success, scihub_success, number_of_pdf, failed_download, number_of_upload, abstract_success, failed_abstract, number_of_pdf
        else:
            return None,None,None,None,None,None,None,None,None,number_of_pdf
    else:
        return None,None,None,None,None,None,None,None,None,None
               
def upload_file(files):
    repodir, workdir, _ = get_ready('repo_work')
    if not os.path.exists(repodir):
        os.makedirs(repodir)

    for file in files:
        destination_path = os.path.join(repodir, os.path.basename(file.name))

        shutil.copy(file.name, destination_path)
    

    return files

def generate_articles_repo(keys:str,pmids,retmax:int):
    
    keys = [k.strip() for k in keys.split('\n')]
    pmids = [k.strip() for k in pmids.split('\n')]
    pmids = [k for k in pmids if k.isdigit()]
    
    repodir, _, _ = get_ready('repo_work')

    articelfinder = ArticleRetrieval(keywords = keys,
                                     pmids = pmids,
                                     repo_dir = repodir,
                                     retmax = retmax)
    articelfinder.initiallize()
    return update_repo()

def delete_articles_repo():
    # 在这里运行生成数据库的函数
    repodir, workdir, _ = get_ready('repo_work')
    if os.path.exists(repodir):
        shutil.rmtree(repodir)
        shutil.rmtree(repodir + '_ab')

    if os.path.exists(workdir):
        shutil.rmtree(workdir)
        shutil.rmtree(workdir + '_ab')

    return gr.Textbox(label="文献库概况",lines =3,
                      value = '文献库和相关数据库已删除',
                      visible = True)

def update_repo():
    keys, retmax, search_len, import_len, _, pmc_success, scihub_success, pdflen, failed, abstract_success, failed_abstract, pdflen = update_repo_info()
    newinfo = ""
    if keys == None:
        newinfo += '无关键词搜索相关信息\n'
        newinfo += '无导入的PMID\n'
        if pdflen:
            newinfo += f'上传的PDF数量: {pdflen}\n'
        else:
            newinfo += '无上传的PDF\n'
    else:
        newinfo += f'关键词搜索:'
        newinfo += f'   关键词: {keys}\n'
        newinfo += f'   搜索上限: {retmax}\n'
        newinfo += f'   搜索到的PMID数量: {search_len}\n'
        newinfo += f'导入的PMID数量: {import_len}\n'
        newinfo += f'成功获取PMC全文数量: {pmc_success}\n'
        newinfo += f'成功获取SciHub全文数量: {scihub_success}\n'
        newinfo += f"下载失败的ID: {failed}\n"
        newinfo += f"成功获取摘要的数量: {abstract_success}\n"
        newinfo += f"获取摘要失败的数量: {failed_abstract}\n"
        newinfo += f'上传的PDF数量: {pdflen}\n'
   
    return gr.Textbox(label="文献库概况",lines =1,
                      value = newinfo,
                      visible = True)

def update_database_info():
    with open(CONFIG_PATH, encoding='utf8') as f:
        config = pytoml.load(f)
    workdir = config['feature_store']['work_dir']
    abworkdir = workdir + '_ab' 
    options = []
    total_json_obj = {}
    for dir in [workdir,abworkdir]:
        tag = 'Full Text' if '_ab' not in dir else 'Abstract'

        chunkdirs = glob.glob(os.path.join(dir, 'chunksize_*'))
        chunkdirs.sort()
        list_of_chunksize = [int(chunkdir.split('_')[-1]) for chunkdir in chunkdirs]
        # print(list_of_chunksize)
        jsonobj = {}
        for chunkdir in chunkdirs:
            k_dir = glob.glob(os.path.join(chunkdir, 'cluster_features','cluster_features_*'))
            k_dir.sort()
            list_of_k = [int(k.split('_')[-1]) for k in k_dir]
            jsonobj[int(chunkdir.split('_')[-1])] = list_of_k
        
        total_json_obj[dir] = jsonobj
        newoptions = [f"{tag}, chunksize:{chunksize}, k:{k}" for chunksize in list_of_chunksize for k in jsonobj[chunksize]]
        options.extend(newoptions)
    
    return options, total_json_obj

@spaces.GPU(duration=120)
def generate_database(chunksize:int,nclusters:str|list[str]):
    # 在这里运行生成数据库的函数
    repodir, workdir, _ = get_ready('repo_work')
    abrepodir = repodir + '_ab'
    abworkdir = workdir + '_ab'
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
    file_opr = FileOperation()

    # walk all files in repo dir
    files = file_opr.scan_dir(repo_dir=repodir)
    fs_init.initialize(files=files, work_dir=workdir,file_opr=file_opr)
    file_opr.summarize(files)

    files = file_opr.scan_dir(repo_dir=abrepodir)
    fs_init.initialize(files=files, work_dir=abworkdir,file_opr=file_opr)
    file_opr.summarize(files)

    del fs_init
    cache.pop('default')
    texts, _ = update_database_info()
    return gr.Textbox(label="数据库概况",value = '\n'.join(texts) ,visible = True)

def delete_database():
    _, workdir, _ = get_ready('repo_work')
    if os.path.exists(workdir):
        shutil.rmtree(workdir)
        shutil.rmtree(workdir+'_ab')
    return  gr.Textbox(label="数据库概况",lines =3,value = '数据库已删除',visible = True)

def update_database_textbox():
    texts, _ = update_database_info()
    if texts == []:
        return gr.Textbox(label="数据库概况",value = '目前还没有数据库',visible = True)
    else:
        return gr.Textbox(label="数据库概况",value = '\n'.join(texts),visible = True)

def update_chunksize_dropdown():
    _, jsonobj = update_database_info()
    return gr.Dropdown(choices= jsonobj.keys())

def update_ncluster_dropdown(chunksize:int):
    _, jsonobj = update_database_info()
    nclusters = jsonobj[chunksize]
    return gr.Dropdown(choices= nclusters)

# @spaces.GPU(duration=120)
def annotation(n,chunksize:int,nclusters:int,remote_ornot:bool,use_abstract:bool):
    '''
    use llm to annotate cluster
    n: percentage of clusters to annotate
    '''
    query = 'annotation'
    if remote_ornot:
        backend = 'remote'
    else:
        backend = 'local'

    clusterdir, samples, assistant, theme = get_ready('annotation',chunksize,nclusters,use_abstract)
    new_obj_list = []
    n = round(n * len(samples.keys()))
    for cluster_no in random.sample(samples.keys(), n):
        chunk = '\n'.join(samples[cluster_no]['samples'][:10])

        code, reply, cluster_no = assistant.annotate_cluster(
                                                theme = theme,
                                                cluster_no=cluster_no,
                                                chunk=chunk,
                                                history=[],
                                                groupname='',
                                                backend=backend)
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

# @spaces.GPU(duration=120)
def inspiration(annotation:str,chunksize:int,nclusters:int,remote_ornot:bool,use_abstract:bool):
    query = 'inspiration'
    if remote_ornot:
        backend = 'remote'
    else:
        backend = 'local'
        
    clusterdir, annoresult, assistant, theme = get_ready('inspiration',chunksize,nclusters,use_abstract)
    new_obj_list = []

    if annotation is not None: # if the user wants to get inspiration from specific clusters only  
        annoresult = [obj for obj in annoresult if obj['annotation'] in [txt.strip() for txt in annotation.split('\n')]]
    
    for index in random.sample(range(len(annoresult)), min(5, len(annoresult))):
        cluster_no = annoresult[index]['cluster_no']
        chunks = annoresult[index]['annotation']
        
        code, reply = assistant.getinspiration(
                                                theme = theme,
                                                annotations = chunks,
                                                history=[], 
                                                groupname='',backend=backend)
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
            
    return '\n\n'.join(list(set([obj['inspiration'] for obj in new_obj_list])))


def getpmcurls(references):
    urls = []
    for ref in references:
        if ref.startswith('PMC'):
            
            refid = ref.replace('.txt','')
            urls.append(f'https://www.ncbi.nlm.nih.gov/pmc/articles/{refid}/')
        else:
            urls.append(ref)
    return urls
    
@spaces.GPU(duration=120)
def summarize_text(query,chunksize:int,remote_ornot:bool,use_abstract:bool):
    if remote_ornot:
        backend = 'remote'
    else:
        backend = 'local'
        
    assistant,_ = get_ready('summarize',chunksize=chunksize,k=None,use_abstract=use_abstract)
    code, reply, references = assistant.generate(query=query,
                                                history=[],
                                                groupname='',backend = backend)
      
    logger.info(f'{code}, {query}, {reply}, {references}')
    urls = getpmcurls(references)
    mds = '\n\n'.join([f'[{ref}]({url})' for ref,url in zip(references,urls)])
    return gr.Markdown(label="看看",value = reply,line_breaks=True) , gr.Markdown(label="参考文献",value = mds,line_breaks=True) 

def main_interface():   
    with gr.Blocks() as demo:
        with gr.Row():
            gr.Markdown(
                """
                # 医学文献综述助手 (又名 不想看文献)
                """
            )

        with gr.Tab("模型服务配置"):
            gr.Markdown("""
            #### 配置模型服务 🛠️

            1. **是否使用远程大模型**
            - 勾选此项，如果你想使用远程的大模型服务。
            - 如果不勾选，将默认使用本地模型服务。

            2. **API配置**
            - 配置大模型提供商和API，确保模型服务能够正常运行。
            - 提供商选择：kimi、deepseek、zhipuai、gpt。
            - 输入您的API密钥和选择对应模型。
            - 点击“保存配置”按钮以保存您的设置。

            📝 **备注**：请参考[如何使用]('https://github.com/jabberwockyang/MedicalReviewAgent/blob/main/README.md')获取更多信息。

            """)

            remote_ornot = gr.Checkbox(label="是否使用远程大模型")
            with gr.Accordion("API配置", open=True):
                apimd = gr.Markdown("[如何配置API]('https://github.com/jabberwockyang/MedicalReviewAgent/blob/main/README.md')",visible=False)
                remote_company = gr.Dropdown(["kimi", "deepseek", "zhipuai",'gpt'],
                                            label="选择大模型提供商",interactive=False,visible=False)
                api = gr.Textbox(label="您的API",lines = 1,interactive=False,visible=False)
                baseurl = gr.Textbox(label="base url",lines = 1,interactive=False,visible=False)
                model = gr.Dropdown([],label="选择模型",interactive=False,visible=False)
            
            confirm_button = gr.Button("保存配置")

            remote_ornot.change(update_remote_buttons, inputs=[remote_ornot],outputs=[apimd,remote_company,api,baseurl,model])
            remote_company.change(udate_model_dropdown, inputs=[remote_company],outputs=[model])
            confirm_button.click(update_remote_config, inputs=[remote_ornot,remote_company,api,baseurl,model],outputs=[confirm_button])


        with gr.Tab("文献查找+数据库生成"):
            gr.Markdown("""
#### 查找文献 📚

1. **输入关键词或PMID批量PubMed PMC文献**
   - 在“感兴趣的关键词”框中输入您感兴趣的关键词，每行一个。
   - 设置查找数量（0-500）。
   - 在“输入PMID”框中输入在PubMed中导出的PMID，每行一个。
   - 点击“搜索PubMed 并拉取全文”按钮进行文献查找。目前主要基于PMC数据库和scihub, 在PMC中未收录的文献将使用scihub下载，scihub近年文献未收录
                        
2. **上传PDF**
   - 通过“上传PDF”按钮上传您已有的PDF文献文件。

3. **更新文献库情况 删除文献库**
   - 点击“更新文献库情况”按钮，查看当前文献库的概况。
   - 如果需要重置或删除现有文献库，点击“删除文献库”按钮。


#### 生成数据库 🗂️

1. **设置数据库构建参数 生成数据库**
   - 选择块大小（Chunk Size）和聚类数（Number of Clusters）。
   - 提供选项用于选择合适的块大小和聚类数。
   - 点击“生成数据库”按钮开始数据库生成过程。

2. **更新数据库情况 删除数据库**
   - 点击“更新数据库情况”按钮，查看当前数据库的概况。
   - 点击“删除数据库”按钮移除现有数据库。

📝 **备注**：请参考[如何选择数据库构建参数]('https://github.com/jabberwockyang/MedicalReviewAgent/tree/main')获取更多信息。
""")
            with gr.Row(equal_height=True):
                with gr.Column(scale=1):
                    with gr.Row():
                        with gr.Column(scale=1):
                            input_keys = gr.Textbox(label="感兴趣的关键词, 换行分隔, 不太好用别用等我改改",
                                                    lines = 5)
                            retmax = gr.Slider(
                                    minimum=0,
                                    maximum=500,
                                    value=250,
                                    interactive=True,
                                    label="搜索上限",
                                    info="How many articles you want to retrieve?"
                                )

                        with gr.Column(scale=1):
                            input_pmids = gr.Textbox(label="输入PMID, 换行分隔",
                                                    lines = 5)
                    
                    generate_repo_button = gr.Button("搜索PubMed并拉取全文")     

                with gr.Column(scale=1):
                    file_output = gr.File(scale=2)
                    upload_button = gr.UploadButton("上传PDF", 
                                    file_types=[".pdf"], 
                                    file_count="multiple",scale=1)
                    
            with gr.Row(equal_height=True):
                with gr.Column(scale=0):
                    delete_repo_button = gr.Button("删除文献库")
                    update_repo_button = gr.Button("更新文献库情况")
                with gr.Column(scale=2):
                    repo_summary =gr.Textbox(label= '文献库概况', 
                                             value="目前还没有文献库")

            generate_repo_button.click(generate_articles_repo, 
                                inputs=[input_keys,input_pmids,retmax],
                                outputs = [repo_summary])
            
            delete_repo_button.click(delete_articles_repo, inputs=None,
                                outputs = repo_summary)
            update_repo_button.click(update_repo, inputs=None,
                                outputs = repo_summary)
            upload_button.upload(upload_file, upload_button, file_output)
            
            with gr.Accordion("数据库构建参数", open=True):
                gr.Markdown("[如何选择数据库构建参数]('https://github.com/jabberwockyang/MedicalReviewAgent/tree/main')")
                chunksize = gr.Slider(label="Chunk Size",
                                      info= 'How long you want the chunk to be?',
                                        minimum=128, maximum=4096,value=1024,step=1,
                                        interactive=True)
                ncluster = gr.CheckboxGroup(["10", "20", "50", '100','200','500','1000'], 
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
#### 写综述 ✍️

1. **更新数据库情况**
   - 点击“更新数据库情况”按钮，确保使用最新的数据库信息。

2. **选择块大小和聚类数**
   - 从下拉菜单中选择合适的块大小和聚类数。

3. **抽样标注文章聚类**
   - 设置抽样标注比例（0-1）。
   - 点击“抽样标注文章聚类”按钮开始标注过程。

4. **获取灵感**
   - 如果不知道写什么，点击“获取灵感”按钮。
   - 系统将基于标注的文章聚类提供相应的综述子问题。

5. **写综述**
   - 输入您想写的内容或主题。
   - 点击“写综述”按钮，生成综述文本。

6. **查看生成结果**
   - 生成的综述文本将显示在“看看”文本框中。
   - 参考文献将显示在“参考文献”框中。

📝 **备注**：可以尝试不同的参数进行标注和灵感获取，有助于提高综述的质量和相关性。
            """)

            with gr.Accordion("聚类标注相关参数", open=True):
                with gr.Row():
                    update_options = gr.Button("更新数据库情况", scale=0)
                    use_abstract = gr.Checkbox(label="是否仅使用摘要",scale=0)
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
            output_text = gr.Markdown(label="看看")
            output_references = gr.Markdown(label="参考文献")
            
            update_options.click(update_chunksize_dropdown,
                                outputs=[chunksize])
            
            chunksize.change(update_ncluster_dropdown, 
                             inputs=[chunksize],
                             outputs= [nclusters])
            
            annotation_button.click(annotation, 
                                    inputs = [ntoread, chunksize, nclusters,remote_ornot,use_abstract],
                                    outputs=[annotation_output])
            
            inspiration_button.click(inspiration, 
                                     inputs= [annotation_output, chunksize, nclusters,remote_ornot,use_abstract],
                                     outputs=[inspiration_output])
            
            write_button.click(summarize_text,
                                inputs=[query, chunksize,remote_ornot,use_abstract],
                                outputs =[output_text,output_references])

    demo.launch(share=False, server_name='0.0.0.0', debug=True,show_error=True,allowed_paths=['img_0.jpg']) 
 
# start service
if __name__ == '__main__':
    args = parse_args()
    # copy config from config-bak 
    if args.model_downloaded:
        shutil.copy('config-mod_down-bak.ini', args.config_path) # yyj
    else:
        shutil.copy('config-bak.ini', args.config_path) # yyj

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

    main_interface()