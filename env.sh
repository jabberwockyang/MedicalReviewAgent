conda create --name ReviewAgent python=3.10.13
conda activate ReviewAgent
git clone https://github.com/jabberwockyang/MedicalReviewAgent.git
cd MedicalReviewAgent
pip install -r requirements.txt

cd /root && mkdir models
cd /root/models

# login required
huggingface-cli download Qwen/Qwen1.5-7B-Chat --local-dir /root/models/Qwen1.5-7B-Chat
huggingface-cli download maidalun1020/bce-embedding-base_v1 --local-dir /root/models/bce-embedding-base_v1
huggingface-cli download maidalun1020/bce-reranker-base_v1 --local-dir /root/models/bce-reranker-base_v1