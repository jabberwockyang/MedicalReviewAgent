---
title: 文献综述助手
emoji: 📚
colorFrom: blue
colorTo: indigo
python_version: 3.10.13
sdk: gradio
sdk_version: "4.25.0"
app_file: app.py
pinned: false
---
[English](README_en.md) | 中文
# MedicalReviewAgent 
## 项目概述
- 一个基于RAG技术和Agent流程的医学文献综述辅助工具。他允许用户配置本地或远程的大语言模型，通过关键词或PMID搜索PubMed以获取文献，上传PDF文件，以及创建和管理文献数据库。用户可以通过设置不同的参数来生成数据库，用于不同的需求。
- 其中文本分块的聚类和标注功能作为一个创新点，目标是通过聚类算法对大量的文本分块进行聚类，这样大模型只需要阅读少量代表性分块并对聚类进行标注就可以输出对数据库内容的整体认识。
- 最后写综述功能可以基于用户提问输出一段完整带有相关参考文献的综述文本。
- 总体来说这个小工具旨在帮助科研人员高效检索，管理，阅读和总结文献。
- [huggingface 体验链接](https://huggingface.co/spaces/Yijun-Yang/ReadReview/), zeroGPUs 比较吝啬 我把本地推理给阉割了 不要用本地模型哈 用API 用本地模型会报错

## 流程图
基本上就是在上海AIlab的茴香豆上面改的 这里主要讲解使用流程 架构和茴香豆一样 [茴香豆架构](https://github.com/InternLM/HuixiangDou/blob/main/docs/architecture_zh.md)
### 文献库和知识库构建
![image](https://github.com/jabberwockyang/MedicalReviewAgent/assets/52541128/d70a2ec1-7a20-4b5b-a91c-bf649f657319)

### 人机合作写文章
<img width="847" alt="image" src="https://github.com/jabberwockyang/MedicalReviewAgent/assets/52541128/fc394d8b-1668-4349-9adc-1c4c0a7e0a8b">


## 功能

1. **模型服务配置**
   - **远程模型选择**：允许用户选择使用远程大模型或本地模型。提供多种大模型提供商选择，如kimi、deepseek、zhipuai、gpt。

2. **文献查找+数据库生成**
   - **文献查找**：
     - 用户可以输入感兴趣的关键词，设置查找数量，并进行PubMed PMC文献查找。
     - 支持用户上传已有的PDF文献文件，可处理复杂PDF结构。
   - **文献库管理**：
     - 支持删除现有文献库。
     - 提供文献库概况的实时更新。
   - **数据库生成**：
     - 用户可以设置块大小用于构建数据库
     - 用户可以设置聚类数量用于文本聚类
   - **数据库管理**：      
     - 支持生成新的数据库，删除现有数据库，并查看数据库概况。

3. **写综述**
   - **抽样标注文章聚类**：
     - 用户可以选择特定的块大小和聚类数，设置抽样标注比例，并开始标注过程。
   - **获取灵感**：
     - 基于标注的文章聚类，大模型提供灵感，帮助用户生成综述所需的问题框架。
   - **综述生成**：
     - 用户可以输入想写的内容或主题，点击生成综述按钮，系统将自动生成综述文本并提供参考文献。

## 亮点

1. **高效的文献查找和管理**
   - 通过关键词快速查找相关文献，支持上传已有PDF文献，方便文献库的构建和管理。

2. **灵活的数据库生成**
   - 提供灵活的数据库生成参数设置，支持多次生成和更新数据库，保证数据的及时性和准确性。

3. **智能的综述生成**
   - 基于先进的大模型技术，提供自动化的文章聚类标注和灵感生成功能，帮助用户快速生成高质量的综述文本。

4. **用户友好界面**
   - 直观的操作界面和详细的使用指导，让用户能够轻松上手和使用各项功能。

5. **远程和本地模型支持**
   - 支持多种大模型提供商的选择，满足不同用户的需求，无论是本地模型还是远程大模型，都能灵活配置和使用。

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
   huggingface-cli下载模型(optional, 第一次调用的时候hf会下载,但是可能有墙)

   ```bash
cd /root && mkdir models
cd /root/models
# login required
huggingface-cli download Qwen/Qwen1.5-7B-Chat --local-dir /root/models/Qwen1.5-7B-Chat
huggingface-cli download maidalun1020/bce-embedding-base_v1 --local-dir /root/models/bce-embedding-base_v1
huggingface-cli download maidalun1020/bce-reranker-base_v1 --local-dir /root/models/bce-reranker-base_v1
   ```
   启动服务

   ```bash
conda activate ReviewAgent
cd MedicalReviewAgent
python3 applocal.py --model_downloaded True # 如果已经在/root/models下载了模型 这个参数会换一个配置文件,里面的modelpath是本地路径不是hf的仓库路径 自己显卡跑跑用这个
python3 app.py # 如果不打算用本地/root/models储存的模型 这是hf的spaces的构建配置
   ```
   gradio在本地7860端口运行

## 技术要点

基于茴香豆加了几个功能

1. 本地和远程模型灵活配置
   - 本地模型是qwen1.5 7b chat
   - 用户也可以在前端界面填写自己的API，本地远程模型任意切换
     
3. 文献搜索和文本清洗
   - 用户键入文献检索关键词，自动从PubMed公开数据库上搜索并下载文献全文
   - xml到txt的文本清洗，去除reference 等无关信息
  
4. 基于[Ragflow](https://github.com/infiniflow/ragflow/blob/main/README_zh.md)的deepdoc库的PDF识别
   - 输出文献中的文字和表格，其中文字存储为 txt, 表格存储为图片，json, html三个格式
   - 目前工作流中仅利用文字，表格数据的利用开发中
     
5. chunk size可调的数据库生成
   -  default 1024 [ref](https://www.llamaindex.ai/blog/evaluating-the-ideal-chunk-size-for-a-rag-system-using-llamaindex-6207e5d3fec5)
     
6. 嵌入kmeans聚类
   - 基于Faiss库
   - k可调
     
7. 基于LLM的聚类内容标注
   - 为节省算力，可以抽样标注
   - 标注后本地储存避免重复标注
     
8. 基于LLM的子问题生成
   - 聚类标注内容作为context，生成对应的子问题
     
9. 基于LLM的综述生成
   - 输入可以是用户自己的问题，也可以参考之前llm生成的子问题
   - 为了比较同一个科学问题的不同来源的观点，修改了一部分茴香豆的Retriever逻辑
      - retreiver 优化 [ref](https://medium.aiplanet.com/evaluating-naive-rag-and-advanced-rag-pipeline-using-langchain-v-0-1-0-and-ragas-17d24e74e5cf)
      - 返回topk =10的分段
      - 由于LLM捞针能力在头尾两端较靠谱，用langchain_community.document_transformers.LongContextReorder 将相关性较高的文本分布在头尾两端
     
10. gradio前端
     
<div style="display: flex;">
    <img src="https://github.com/jabberwockyang/MedicalReviewAgent/assets/52541128/83a1cefe-ebe6-499a-9ca7-214e90089815" style="width: 30%;" />
    <img src="https://github.com/jabberwockyang/MedicalReviewAgent/assets/52541128/c369aeaa-6749-4d56-b71a-d62ff1cb780f" style="width: 30%;" />
    <img src="https://github.com/jabberwockyang/MedicalReviewAgent/assets/52541128/27f1d440-2b79-4cbb-9b15-a5e2fa037d33" style="width: 30%;" />
</div>
<div style="display: flex;">
    <img src="https://github.com/jabberwockyang/MedicalReviewAgent/assets/52541128/db2443ff-b6a2-4c35-83e6-21e478c39eba" style="width: 30%;" />
    <img src="https://github.com/jabberwockyang/MedicalReviewAgent/assets/52541128/77496f38-f1e6-4919-a439-c06b4fd52aab" style="width: 30%;" />
</div>

   
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
2. [E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25499/)
3. [Ragflow](https://github.com/infiniflow/ragflow/blob/main/README_zh.md)
4. [Advanced RAG pipeline](https://medium.aiplanet.com/evaluating-naive-rag-and-advanced-rag-pipeline-using-langchain-v-0-1-0-and-ragas-17d24e74e5cf)
   
