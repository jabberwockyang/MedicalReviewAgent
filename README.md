# MedicalReviewAgent 不想看文献

## BASE MODEL
QWEN 1.5 7B CHAT

## WORKFLOW 
### FUNCTIONAL CALL 
- natural language request to a set of parameters
- a finetuning dataset for functional call
### RETRIEVAL AND CLEAN ✅
- thru [api](https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=PMCID) to get associative pubmed article ✅
- clean xml to text ✅
### RAG DATASET ESTABLISHMENT
- [HUIXIANGDOU](https://github.com/InternLM/HuixiangDou) の 改写 ✅
    - chunk size 摸索 [ref](https://www.llamaindex.ai/blog/evaluating-the-ideal-chunk-size-for-a-rag-system-using-llamaindex-6207e5d3fec5)
- 嵌入聚类 自动打标 可视化
### 灵感提供
- input
    - context: 打标内容
    - prompt：针对xxx的研究目的，基于context，提出子问题：
- output：
    - a list of child questions
- refresh is available
### writing
这一步可能要oneshot 或者finetuning
- input:
    - 子问题
    - 打标限制，（提示 更少的内容选择会让运行更快）
- output：
    - 带ref的文本
    - 
