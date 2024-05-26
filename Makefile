all: static-tests doc-tests unit-tests

.PHONY: all

setup:
	
	sudo apt-get update && apt-get install ffmpeg libsm6 libxext6  -y
	echo "Make sure python version >3.8 is installed."
	pip install torch==1.12.0+cu113 torchvision==0.13.0+cu113 torchaudio==0.12.0 --extra-index-url https://download.pytorch.org/whl/cu113
	pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple


download:
	pip install modelscope
	python download_models.py
	mv models/damo/I2VGen-XL/* models/


run: setup download
	echo "To run the inference, head over the notebook, Inference.ipynb"
