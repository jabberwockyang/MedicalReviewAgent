# MedicalReviewAgent 不想看文献

## BASE MODEL
QWEN 1.5 7B CHAT

## WORKFLOW 
### keywords generation #TODO
- userinput:
    - text: a natural language query
- llm:
    - SFT may be needed 
    - natural language query to a set of parameters

### RETRIEVAL AND CLEAN ✅
- userinput:
    - text: a list of keywords
- programe:
    - get associative pubmed article thru PMC [API](https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=PMCID) ✅ 
    - clean xml to text ✅
### RAG DATASET ESTABLISHMENT
- userinput:
    - slider: chunk size (default 1024)  [ref](https://www.llamaindex.ai/blog/evaluating-the-ideal-chunk-size-for-a-rag-system-using-llamaindex-6207e5d3fec5)   ✅
    - slider: N-cluster for clustering (default 摸索中)
- programe:
    - [HUIXIANGDOU](https://github.com/InternLM/HuixiangDou) の 改写 ✅
        - 添加嵌入聚类代码 ✅
        - 添加llm自动标注聚类代码 ✅
        - chunk size 可调 ✅
    - output: faiss 向量储存文件+聚类结果
### 数据库概况
- userinput: 
    - slider: 标注数量（range: 0- 全量）优先标注大的cluster 
- llm:
    - 标注并储存
    - 跳过重复标注 
### 给我点灵感
- userinput: click button
- llm:
    - prompt：针对query的研究目的，基于tags，提出子问题：
    - output：
        - a list of child query（子问题）以及对应一个或多个的tag
    - temperature set to 1, refresh is available
### writing
- user: 输入子问题 以及一个或多个的tag，（可从灵感提供模块一键导入）
- programe: 通过打标限制提取相应的chunks实例化retreiver
- llm：
    - prompt:
        - 逐chunk判断是否回答问题（需要做实验明确必要性）
        - 对比总结+带ref 这一步可能要oneshotprompt 或者finetuning（考虑后期接入外部API功能，暂不考虑进行微调）
    - output：
        - 带ref文本
### gradio 前端 ✅
