.PHONY: all conda conda-setup setup download autostart run docker-build docker-run

all: static-tests doc-tests unit-tests

conda:
	wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
	chmod +x Miniconda3-latest-Linux-x86_64.sh
	./Miniconda3-latest-Linux-x86_64.sh -b
	rm Miniconda3-latest-Linux-x86_64.sh
	conda init

conda-setup:
	bash -c "source ~/.bashrc && conda create -n exp python=3.8 -y && conda activate exp"

setup:
	apt-get update && apt-get install ffmpeg libsm6 libxext6  -y
	echo "Make sure python version >3.8 is installed."
	pip install torch==1.12.0+cu113 torchvision==0.13.0+cu113 torchaudio==0.12.0 --extra-index-url https://download.pytorch.org/whl/cu113
	pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

download:
	pip install modelscope
	python3 download_models.py
	mv models/damo/I2VGen-XL/* models/
	pip install opencv-python --upgrade

autostart:
	echo "cd /root/VideoGenerator" > /root/onstart.sh
	echo "/opt/conda/envs/exp/bin/python /root/VideoGenerator/main.py" >> /root/onstart.sh

docker-build:
	docker build -t vatfilm:staging .

docker-run:
	docker run --rm -it --gpus all vatfilm:staging /bin/bash