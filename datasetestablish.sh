conda activate InternLM2_Huixiangdou


# 创建向量数据集存储目录
export REPODIR='repodir_skingutaxis'
cd /root/ReviewAgent && mkdir $REPODIR
# 通过关键词检索文献并清洗数据到向量数据集存储目录
python3 Retrieval.py --keywords skin-gut axis --retmax 500 --repo_dir $REPODIR


# 创建一个测试用的问询列表，用来测试拒答流程是否起效
cd /root/ReviewAgent
echo '[
"what is skin-gut axis",
"你好，介绍下自己"
]' > ./test_queries.json

# 创建向量数据库存储目录
conda activate InternLM2_Huixiangdou
export WORKDIR='workdir_skingutaxis'
export REPODIR='repodir_skingutaxis'
cd /root/ReviewAgent && mkdir $WORKDIR
# 分别向量化知识语料、接受问题和拒绝问题中后保存到 workdir
python3 -m huixiangdou.service.feature_store --work_dir $WORKDIR --repo_dir $REPODIR --sample ./test_queries.json --chunk_size 768 
                                            
# 创建向量数据库存储目录
conda activate InternLM2_Huixiangdou
export WORKDIR='workdir_skingutaxis-128'
export REPODIR='repodir_skingutaxis'
cd /root/ReviewAgent && mkdir $WORKDIR
# 分别向量化知识语料、接受问题和拒绝问题中后保存到 workdir
python3 -m huixiangdou.service.feature_store --work_dir $WORKDIR --repo_dir $REPODIR --sample ./test_queries.json --chunk_size 128 

# 创建向量数据库存储目录
conda activate InternLM2_Huixiangdou
export WORKDIR='workdir_skingutaxis-768'
export REPODIR='repodir_skingutaxis'
cd /root/ReviewAgent && mkdir $WORKDIR
# 分别向量化知识语料、接受问题和拒绝问题中后保存到 workdir
python3 -m huixiangdou.service.feature_store --work_dir $WORKDIR --repo_dir $REPODIR --sample ./test_queries.json --chunk_size 768 
                                               


# 运行茴香豆

conda activate InternLM2_Huixiangdou
cd /root/ReviewAgent/
export WORKDIR='workdir_skingutaxis-128'
# 改写config文件第五行为 work_dir = "workdir_skingutaxis-128"
sed -i '5s/.*/work_dir = "workdir_skingutaxis-128"/' config.ini
python3 -m huixiangdou.main --work_dir $WORKDIR --standalone

conda activate InternLM2_Huixiangdou
cd /root/ReviewAgent/
export WORKDIR='workdir_skingutaxis-768'
# 改写config文件第五行为 work_dir = "workdir_skingutaxis-768"
sed -i '5s/.*/work_dir = "workdir_skingutaxis-768"/' config.ini
python3 -m huixiangdou.main --work_dir $WORKDIR --standalone