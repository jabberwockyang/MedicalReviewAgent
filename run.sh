# 云端运行
conda activate ReviewAgent
cd MedicalReviewAgent
python3 applocal.py --model_downloaded True

# 本地映射端口
ssh -CNg -L 7860:127.0.0.1:7860 root@youripaddress
