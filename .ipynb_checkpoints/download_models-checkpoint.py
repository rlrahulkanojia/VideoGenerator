import os
from modelscope.hub.snapshot_download import snapshot_download

if not os.path.exists('models/'):
    model_dir = snapshot_download('damo/I2VGen-XL', cache_dir='models/', revision='v1.0.0')

