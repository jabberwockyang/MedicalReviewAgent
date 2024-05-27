# MedicalReviewAgent 不想看文献
## 项目概述
整一个帮我写综述的Agent，希望他能完成文献内容的收集，文本分类和总结，科学事实对比，撰写综述等功能
用到了RAG, functional call等技术
还在不断摸索中，欢迎大佬指导！

## 流程图
基本上就是在上海AIlab的茴香豆上面改的 这里主要讲解使用流程 架构和茴香豆一样
### 文献库和知识库构建
<img width="663" alt="image" src="https://github.com/jabberwockyang/MedicalReviewAgent/assets/52541128/bb61d5ed-1e7f-4855-b771-2961a81d28c8">

### 人机合作写文章
<img width="847" alt="image" src="https://github.com/jabberwockyang/MedicalReviewAgent/assets/52541128/fc394d8b-1668-4349-9adc-1c4c0a7e0a8b">


## 技术路线
目前的基础模型是qwen1.5 7b chat，后头流程摸顺了换成GPT4的API

基于茴香豆加了几个功能

1. 文献搜索和文本清洗
   - 用户键入文献检索关键词，自动从PubMed公开数据库上搜索并下载文献全文
   - xml到txt的文本清洗，去除reference 等无关信息
  
2. chunk size可调
   -  default 1024 [ref](https://www.llamaindex.ai/blog/evaluating-the-ideal-chunk-size-for-a-rag-system-using-llamaindex-6207e5d3fec5)
     
3. 嵌入kmeans聚类
   - 基于Faiss库
   - k可调
     
4. 基于LLM的聚类内容标注
   - 为节省算力，可以抽样标注
   - 标注后本地储存避免重复标注
     
5. 基于LLM的子问题生成
   - 聚类标注内容作为context，生成对应的子问题
     
6. 基于LLM的综述生成
   - 输入可以是用户自己的问题，也可以参考之前llm生成的子问题
     
7. gradio前端
   目前是酱的
<div style="display: flex;">
    <img src="https://github.com/jabberwockyang/MedicalReviewAgent/assets/52541128/f1cd213f-d41a-49f2-b0c9-2539f23b2b22" style="width: 30%;" />
    <img src="https://github.com/jabberwockyang/MedicalReviewAgent/assets/52541128/5037eb48-d0ef-46f2-9416-037079c58da9" style="width: 30%;" />
    <img src="https://github.com/jabberwockyang/MedicalReviewAgent/assets/52541128/80d8d463-45a4-46df-b988-86c4f42d4e7b" style="width: 30%;" />
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
             "include-type":None,
             "exclude-type":"review"
             }
         ```
2. PDF处理功能，打算用RAGflow里面的deepdoc包
3. 摸索适用于不同需求的chunk size和 k值
   - 比方说用来找某个实验方法用多大浓度的试剂，和总结某研究领域的前沿进展所用到的chunksize应该是不一样的吧🤔
   - 后者的大小其实取决于前者叭🤔

     
## 感谢
1. [茴香豆](https://github.com/InternLM/HuixiangDou)
2. [E-utilities](https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=PMCID)
3. [Ragflow](https://github.com/infiniflow/ragflow/blob/main/README_zh.md)
   
