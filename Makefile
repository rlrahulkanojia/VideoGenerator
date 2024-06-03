all: static-tests doc-tests unit-tests

.PHONY: all

conda:
	wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
	chmod +x Miniconda3-latest-Linux-x86_64.sh
	./Miniconda3-latest-Linux-x86_64.sh -b
	rm Miniconda3-latest-Linux-x86_64.sh
	conda init
	source ~/.bashrc 
	conda create -n exp python=3.8 -y
	conda activate exp

setup:
	
	apt-get update && apt-get install ffmpeg libsm6 libxext6  -y
	echo "Make sure python version >3.8 is installed."
	pip install torch==1.12.0+cu113 torchvision==0.13.0+cu113 torchaudio==0.12.0 --extra-index-url https://download.pytorch.org/whl/cu113
	pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple


download:
	pip install modelscope
	python download_models.py
	mv models/damo/I2VGen-XL/* models/
	pip install opencv-python --upgrade

autostart:
	echo "cd /root/VideoGenerator" > /root/onstart.sh
	echo "/opt/conda/envs/exp/bin/python /root/VideoGenerator/main.py" >> /root/onstart.sh

run: setup download
	echo "To run the inference, head over the notebook, Inference.ipynb"
