import os
import cv2
import shutil
import argparse
import torch
import numpy as np
import pandas as pd
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib
from preprocess import DocScanner
import detection
import ocr
import retrieval
from tool.config import Config 
from tool.utils import download_pretrained_weights


CACHE_DIR = 'tmp'

class Preprocess:
    def __init__(
        self, 
        find_best_rotation=True):
        
        self.find_best_rotation = find_best_rotation

        if self.find_best_rotation:
            self.crop_path = os.path.join(CACHE_DIR, 'crops')
            if os.path.exists(self.crop_path):
                shutil.rmtree(self.crop_path)
                os.mkdir(self.crop_path)
            self.det_model = Detection()
            self.ocr_model = OCR()
        self.scanner = DocScanner()

    def __call__(self, image, return_score=False):
        

        output = self.scanner.scan(image)
        
        if self.find_best_rotation:

            _ = self.det_model(
                output,
                crop_region=True,
                save_csv=False,
                return_result=False,
                output_path=CACHE_DIR)

            orientation_scores = np.array([0.,0.,0.,0.])
            num_crops = len(os.listdir(self.crop_path))
            for i in range(num_crops):
                single_crop_path = os.path.join(self.crop_path, f'{i}.jpg')
                if not os.path.isfile(single_crop_path):
                    continue
                img = cv2.imread(single_crop_path)
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                orientation_scores += ocr.find_rotation_score(img, self.ocr_model)
            best_orient = np.argmax(orientation_scores)
            print(f"Rotate image by {best_orient*90} degrees")

            # Rotate the original image
            output = ocr.rotate_img(output, best_orient)
        
        if return_score:
            return output, orientation_scores
        else:
            return output

class Detection:
    def __init__(self, config_path=None, weight_path=None):
        if config_path is None:
            config_path = 'tool/config/detection/configs.yaml'
        config = Config(config_path)
        if weight_path is None:
            tmp_path = os.path.join(CACHE_DIR, 'det_weight.pth')
            download_pretrained_weights("pan_resnet18_sroie19", cached=tmp_path)
            weight_path = tmp_path
        self.model = detection.PAN(config, model_path=weight_path)
        
    def __call__(
        self, 
        image,
        crop_region=False,
        save_csv=False,
        return_result=False,
        output_path=None):
        
        """
        Input: path to image
        Output: boxes (coordinates of 4 points)
        """

        if output_path is None:
            assert save_csv, "Please specify output_path"
            assert crop_region, "Please specify output_path"
        else:
            output_path = os.path.join(output_path, 'crops')
            if os.path.exists(output_path):
                shutil.rmtree(output_path)
                os.mkdir(output_path)

            
        # Detect and OCR for final result
        _, boxes_list, _ = self.model.predict(
            image, 
            output_path, 
            crop_region=crop_region,
            save_csv=save_csv)

        if return_result:
            img = detection.draw_bbox(image[:, :, ::-1], boxes_list)
        
        if return_result:
            return boxes_list, img
        else:
            return boxes_list

class OCR:
    def __init__(self, config_path=None, weight_path=None):
        if config_path is None:
            config_path = 'tool/config/ocr/configs.yaml'
        config = Config(config_path)
        ocr_config = ocr.Config.load_config_from_name(config.model_name)
        ocr_config['cnn']['pretrained']=False
        ocr_config['device'] = 'cuda:0'
        ocr_config['predictor']['beamsearch']=False

        if weight_path is None:
            tmp_path = os.path.join(CACHE_DIR, 'ocr_weight.pth')
            download_pretrained_weights("transformerocr_mcocr", cached=tmp_path)
            weight_path = tmp_path
        ocr_config['weights'] = weight_path
        self.model = ocr.Predictor(ocr_config)

    def __call__(self, img, return_prob=False):
        if isinstance(img, np.ndarray):
            img = Image.fromarray(img)
        return self.model.predict(img, return_prob)

    def predict_folder(self, img_paths, return_probs=False):
        texts = []
        if return_probs:
            probs = []
        for i, img_path in enumerate(img_paths):
            img = Image.open(img_path)
            if return_probs:
                text, prob = self(img, True)
                texts.append(text)
                probs.append(prob)
            else:
                text = self.model(img, False)
                texts.append(text)

        if return_probs:
            return texts, probs
        else:
            return texts

