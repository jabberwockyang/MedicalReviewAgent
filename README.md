# MedicalReviewAgent 不想看文献

## BASE MODEL
QWEN 1.5 7B CHAT

## WORKFLOW 
### FUNCTIONAL CALL 
- natural language query to a set of parameters
- 用户自己选择
### RETRIEVAL AND CLEAN ✅
- thru [api](https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=PMCID) to get associative pubmed article ✅
- clean xml to text ✅
### RAG DATASET ESTABLISHMENT
- [HUIXIANGDOU](https://github.com/InternLM/HuixiangDou) の 改写 ✅
    - chunk size 摸索 [ref](https://www.llamaindex.ai/blog/evaluating-the-ideal-chunk-size-for-a-rag-system-using-llamaindex-6207e5d3fec5)
- 嵌入聚类 自动打标tag 可视化
    - 热图 词云
### 灵感提供
- input
    - context: chunks with tag A
    - prompt：针对query的研究目的，基于context，提出子问题：
- output：
    - a list of child query（子问题）以及对应一个或多个的tag
- refresh is available
### writing
这一步可能要oneshot 或者finetuning
- input:
    - 用户输入子问题
    - 用户输入一个或多个的tag，（提示 更少的内容选择会让运行更快）
    - 程序通过打标限制提取相应的chunk
- prompt:
    - 判断是否回答问题
    - 对比总结+带ref
- output：
    - 带ref文本
