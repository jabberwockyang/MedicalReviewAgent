# MedicalReviewAgent 不想看文献
## 项目概述
- 整一个帮我写综述的Agent，希望他能完成文献内容的收集，文本分类和总结，科学事实对比，撰写综述等功能
- 计划用到RAG, function calling等技术
- 还在不断摸索中，欢迎大佬指导！

## 流程图
基本上就是在上海AIlab的茴香豆上面改的 这里主要讲解使用流程 架构和茴香豆一样 [茴香豆架构](https://github.com/InternLM/HuixiangDou/blob/main/docs/architecture_zh.md)
### 文献库和知识库构建
![image](https://github.com/jabberwockyang/MedicalReviewAgent/assets/52541128/81d4397a-0a15-46c1-8416-eaa27b4d1182)


### 人机合作写文章
<img width="847" alt="image" src="https://github.com/jabberwockyang/MedicalReviewAgent/assets/52541128/fc394d8b-1668-4349-9adc-1c4c0a7e0a8b">


## 技术路线
目前的基础模型是qwen1.5 7b chat，后头流程摸顺了换成GPT4的API

基于茴香豆加了几个功能

1. 文献搜索和文本清洗
   - 用户键入文献检索关键词，自动从PubMed公开数据库上搜索并下载文献全文
   - xml到txt的文本清洗，去除reference 等无关信息
  
2. 基于[Ragflow](https://github.com/infiniflow/ragflow/blob/main/README_zh.md)的deepdoc库的PDF识别
   - 输出文献中的文字和表格，其中文字存储为 txt, 表格存储为图片，json, html三个格式
   - 目前工作流中仅利用文字，表格数据的利用开发中
     
3. chunk size可调的数据库生成
   -  default 1024 [ref](https://www.llamaindex.ai/blog/evaluating-the-ideal-chunk-size-for-a-rag-system-using-llamaindex-6207e5d3fec5)
     
4. 嵌入kmeans聚类
   - 基于Faiss库
   - k可调
     
5. 基于LLM的聚类内容标注
   - 为节省算力，可以抽样标注
   - 标注后本地储存避免重复标注
     
6. 基于LLM的子问题生成
   - 聚类标注内容作为context，生成对应的子问题
     
7. 基于LLM的综述生成
   - 输入可以是用户自己的问题，也可以参考之前llm生成的子问题
   - 为了比较同一个科学问题的不同来源的观点，修改了一部分茴香豆的Retriever逻辑
      - retreiver 优化 [ref](https://medium.aiplanet.com/evaluating-naive-rag-and-advanced-rag-pipeline-using-langchain-v-0-1-0-and-ragas-17d24e74e5cf)
      - 返回topk =10的分段
      - 由于LLM捞针能力在头尾两端较靠谱，用langchain_community.document_transformers.LongContextReorder 将相关性较高的文本分布在头尾两端
     
8. gradio前端
   
   - 可以添加API配置
     
   - 目前是酱的
     
<div style="display: flex;">
    <img src="https://github.com/jabberwockyang/MedicalReviewAgent/assets/52541128/460990bb-c214-4d43-8481-2bcb853c70fb" style="width: 30%;" />
    <img src="https://github.com/jabberwockyang/MedicalReviewAgent/assets/52541128/c369aeaa-6749-4d56-b71a-d62ff1cb780f" style="width: 30%;" />
    <img src="https://github.com/jabberwockyang/MedicalReviewAgent/assets/52541128/27f1d440-2b79-4cbb-9b15-a5e2fa037d33" style="width: 30%;" />
</div>
<div style="display: flex;">
    <img src="https://github.com/jabberwockyang/MedicalReviewAgent/assets/52541128/db2443ff-b6a2-4c35-83e6-21e478c39eba" style="width: 30%;" />
    <img src="https://github.com/jabberwockyang/MedicalReviewAgent/assets/52541128/77496f38-f1e6-4919-a439-c06b4fd52aab" style="width: 30%;" />
</div>


## 安装运行
   新建conda环境

   ```bash
conda create --name ReviewAgent python=3.10.14
conda activate ReviewAgent
   ```
   拉取github仓库 

   ```bash
git clone https://github.com/jabberwockyang/MedicalReviewAgent.git
cd MedicalReviewAgent
pip install -r requirements.txt
   ```
   huggingface-cli下载模型

   ```bash
cd /root && mkdir models
cd /root/models
huggingface-cli download --resume-download Qwen/Qwen1.5-7B-Chat --local-dir-use-symlinks False  --local-dir /root/models/Qwen1.5-7B-Chat
huggingface-cli download --resume-download bce-embedding-base_v1 --local-dir-use-symlinks False  --local-dir /root/models/bce-embedding-base_v1
huggingface-cli download --resume-download bce-reranker-base_v1 --local-dir-use-symlinks False  --local-dir /root/models/bce-reranker-base_v1
   ```
   启动服务

   ```bash
conda activate ReviewAgent
cd MedicalReviewAgent
python3 app.py
   ```

## TODO 
1. 自然语言到文献搜索参数的functional call功能
   - 比如：
       - 输入：帮我搜索近五年特应性皮炎相关的孟德尔随机化文章，不要综述
       - 输出：
         ```json
            {"keywords":["atopic dermatitis","mendelian randomisation"],
             "min-year":2019,
             "max-year":2024,
             "include-type":null,
             "exclude-type":"review"
             }
         ```
2. 摸索适用于不同需求的chunk size和 k值
   - 比方说用来找某个实验方法用多大浓度的试剂，和总结某研究领域的前沿进展所用到的chunksize应该是不一样的吧🤔
   - 后者的大小其实取决于前者叭🤔
3. 表格数据利用
     
## 感谢
1. [茴香豆](https://github.com/InternLM/HuixiangDou)
2. [E-utilities](https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=PMCID)
3. [Ragflow](https://github.com/infiniflow/ragflow/blob/main/README_zh.md)
4. [Advanced RAG pipeline](https://medium.aiplanet.com/evaluating-naive-rag-and-advanced-rag-pipeline-using-langchain-v-0-1-0-and-ragas-17d24e74e5cf)
   
