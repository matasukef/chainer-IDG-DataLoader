import json
import pickle
from pathlib import Path

import cv2
import numpy as np
import chainer

from utils.process_image import ImgProcesser


class Seq2SeqDatasetBase(chainer.dataset.DatasetMixin):
    """
    Chainer Dataset Class for image captioning generation.

    Attributes
    ----------
    dataset_path: str
        path to dataset which contains image info and captions
        preprocessed by mscoco2formatted.py and preprocess_tokens.py.
    vocab_path: str
        path to vocabulary dictionary created by preprocess_tokens.py.
    img_root: str
        path to directory of images.
    img_feature_root: str
        path to directory of image features.
    use_img_features: bool, default True
        Use image features or not.
    img_mean: str, default imagenet
        image mean used for preprocess images.
        imagenet mean is used as a default.
    preload_features: bool, default False
        preload all image features onto RAM.
    """
    def __init__(
            self,
            dataset_path,
            vocab_path,
            img_feature_root,
            img_root,
            use_img_features=True,
            img_mean='imagenet',
            preload_features=False,
    ):

        if Path(dataset_path).exists() and Path(vocab_path).exists():
            self.dataset = self.load_data(dataset_path)
            self.word_ids = self.load_data(vocab_path)
            self.captions = self.dataset['captions']
            self.images = self.dataset['images']
        else:
            raise FileNotFoundError

        self.num_captions = len(self.captions)
        self.num_images = len(self.images)
        self.cap2img = {
            caption['caption_idx']: caption['img_idx'] for caption in self.captions
        }
        self.inv_word_ids = {
            v: k for k, v in self.word_ids.items()
        }

        if not use_img_features:
            self.img_proc = ImgProcesser(mean_type=img_mean)
            self.img_root = Path(img_root)
            if not self.img_root.exists() and not self.img_root.is_dir():
                raise FileNotFoundError
        else:
            self.img_feature_root = Path(img_feature_root)
            if not self.img_feature_root.exists() and not self.img_feature_root.is_dir():
                raise FileNotFoundError

        if preload_features:
            self._img_features = np.array(
                [
                    np.load('{0}.npz'.format(
                        self.img_root / Path(image['file_path']).with_suffix("")
                    ))['arr_0'] for image in self.images
                ]
            )

    def __len__(self):
        return len(self.captions)

    def get_raw_data():
        pass


    @staticmethod
    def load_data(path):
        in_path = Path(path)
        ext = in_path.suffix
        if ext == '.pickle':
            with in_path.open('rb') as f:
                dataset = pickle.load(f)
        elif ext == '.json':
            with in_path.open('r') as f:
                dataset = json.load(f)
        else:
            msg = 'File %s can not be loaded.\n \
                   choose json or pickle format' % path
            raise TypeError(msg)

        return dataset

    def get_example(self, i):
        pass

    def token2index(self, tokens):
        return [self.inv_word_ids[token] for token in tokens]

    def index2token(self, indices):
        return [self.word_ids[index] for index in indices]

    def load_img(self, img_path, img_h=224, img_w=224, expand_dim=True):
        img = cv2.imread(img_path).astype(np.float32)
        img_size = (img.shape[0], img.shape[1])
        resized_size = (img_h, img_w)

        if img_size != resized_size:
            img = cv2.resize(img, resized_size)

        img = img.transpose(2, 0, 1)
