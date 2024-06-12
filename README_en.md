Here's a README in English for your project, "MedicalReviewAgent" (a.k.a. "I Don't Want to Read Papers").

---

# MedicalReviewAgent: I Don't Want to Read Papers

## Project Overview

- MedicalReviewAgent is a medical literature review assistance tool based on RAG technology and agent workflows. It enables users to configure local or remote large language models to search PubMed via keywords or PMIDs, upload PDF files, and create and manage literature databases. Users can generate databases with different settings for various needs.
- The tool innovatively includes text block clustering and tagging to manage large volumes of text efficiently. By clustering text blocks, the large model only needs to read a few representative blocks and annotate clusters to summarize the database content comprehensively.
- The "write review" feature allows generating complete review text with references based on user queries.
- Overall, this tool is designed to help researchers efficiently retrieve, manage, read, and summarize literature.
- [Hugging Face Experience Link](https://huggingface.co/spaces/Yijun-Yang/ReadReview/). Note: ZeroGPUs are limited, so avoid using the local model as it may result in errors.

## Workflow Diagrams

### Literature and Knowledge Base Construction
![Literature and Knowledge Base Construction Diagram](https://github.com/jabberwockyang/MedicalReviewAgent/assets/52541128/d70a2ec1-7a20-4b5b-a91c-bf649f657319)

### Human-Computer Collaborative Writing
![Human-Computer Collaborative Writing Diagram](https://github.com/jabberwockyang/MedicalReviewAgent/assets/52541128/fc394d8b-1668-4349-9adc-1c4c0a7e0a8b)

## Features

1. **Model Service Configuration**
   - **Remote Model Selection**: Allows users to choose between remote or local large models from various providers like Kimi, Deepseek, Zhipuai, and GPT.

2. **Literature Search + Database Creation**
   - **Literature Search**: Users can enter keywords, set the search quantity, and conduct PubMed PMC literature searches.
   - **Literature Database Management**: Supports deleting existing literature databases and provides real-time updates on the library's overview.
   - **Database Creation**: Users can set block size and cluster numbers for text clustering.
   - **Database Management**: Supports creating new databases, deleting existing ones, and viewing database overviews.

3. **Writing Reviews**
   - **Sampling Annotated Article Clusters**: Users can choose block size and cluster numbers, set the sampling annotation ratio, and start the annotation process.
   - **Inspiration Generation**: Based on annotated article clusters, the large model provides inspiration to help generate the framework of questions needed for the review.
   - **Review Generation**: Users can input the content or topic they wish to write about, click the generate review button, and the system will automatically generate review text with references.

## Highlights

1. **Efficient Literature Search and Management**: Quickly find related literature by keywords and supports uploading existing PDF literature for easy library construction and management.
2. **Flexible Database Generation**: Provides flexible parameters for database generation, supports multiple generations and updates to ensure timeliness and accuracy.
3. **Intelligent Review Generation**: Utilizes advanced large model technology for automated article cluster annotation and inspiration generation, helping users quickly produce high-quality review text.
4. **User-Friendly Interface**: Intuitive interface and detailed usage instructions make it easy for users to start and use all features.
5. **Remote and Local Model Support**: Supports a variety of large model providers to meet different user needs. Whether using local or remote models, configurations can be flexibly adjusted.

## Installation and Running

Create a new conda environment:
```bash
conda create --name ReviewAgent python=3.10.14
conda activate ReviewAgent
```
Clone the GitHub repository:
```bash
git clone https://github.com/jabberwockyang/MedicalReviewAgent.git
cd MedicalReviewAgent
pip install -r requirements.txt
```
Download models with huggingface-cli (optional, HF will download on first call, but there might be firewall issues):
```bash
cd /root && mkdir models
cd /root/models
# login required
huggingface-cli download Qwen/Qwen1.5-7B-Chat --local-dir /root/models/Qwen1.5-7B-Chat
huggingface-cli download maidalun1020/bce-embedding-base_v1 --local-dir /root/models/bce-embedding-base_v1
huggingface-cli download maidalun1020/bce-reranker-base_v1 --local-dir /root/models/bce-reranker-base_v1
```
Start the service:
```bash
conda activate ReviewAgent
cd MedicalReviewAgent
python3 app.py --model_downloaded True # Use this if models