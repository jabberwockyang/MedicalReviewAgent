# MedicalReviewAgent 不想看文献

## BASE MODEL
QWEN 1.5 7B CHAT

## WORKFLOW 
### keywords generation optional
- user: a natural language query
- llm: natural language query to a set of parameters
- 页面展示关键词多选项，用户自己选择
### RETRIEVAL AND CLEAN ✅
- user: a list of keywords
- programe:
    - get associative pubmed article thru [api](https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=PMCID) ✅ 
    - clean xml to text ✅
### RAG DATASET ESTABLISHMENT
- programe:
    - [HUIXIANGDOU](https://github.com/InternLM/HuixiangDou) の 改写 ✅
        - chunk size 摸索 [ref](https://www.llamaindex.ai/blog/evaluating-the-ideal-chunk-size-for-a-rag-system-using-llamaindex-6207e5d3fec5)  ✅
    - 嵌入聚类 自动打标tag 可视化
        - 可视化选项: 热图 词云
### 灵感提供
- user: click button
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
