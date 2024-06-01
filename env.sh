conda create --name ReviewAgent python=3.10,13
conda activate ReviewAgent
git clone https://github.com/jabberwockyang/MedicalReviewAgent.git
cd MedicalReviewAgent
pip install -r requirements.txt

cd /root && mkdir models
cd /root/models
huggingface-cli download --resume-download Qwen/Qwen1.5-7B-Chat --local-dir-use-symlinks False  --local-dir /root/models/Qwen1.5-7B-Chat
huggingface-cli download --resume-download bce-embedding-base_v1 --local-dir-use-symlinks False  --local-dir /root/models/bce-embedding-base_v1
huggingface-cli download --resume-download bce-reranker-base_v1 --local-dir-use-symlinks False  --local-dir /root/models/bce-reranker-base_v1