import streamlit as st
from PIL import Image
import numpy as np
from modules import Preprocess, Detection, OCR, Retrieval, Correction
import os
from tool.utils import natural_keys
from itertools import cycle
import time

#config st
st.set_page_config(layout="wide")
st.markdown("<h1 style='text-align: center; color: blue;'>Fina OCR Service</h1>", unsafe_allow_html=True)

def process(image_file, det_weight, ocr_weight):
    class_mapping = {"SELLER":0, "ADDRESS":1, "TIMESTAMP":2, "TOTAL_COST":3, "NONE":4}
    img_id = os.path.basename(image_file.name).split('.')[0]
    #read image
    img = Image.open(image_file)
    img = np.array(img)
    st.subheader('Image you Uploaded...')

    #load model
    start = time.time()
    det_model = Detection(weight_path=det_weight)
    ocr_model = OCR(weight_path=ocr_weight)
    # retrieval = Retrieval(class_mapping, mode = 'all')
    correction = Correction()

    #region box detection
    boxes, img_det  = det_model(
    img,
    crop_region=True,                               #Crop detected regions for OCR
    return_result=True,                             # Return plotted result
    output_path=f"/home/huynguyen14/workspace/fina/vietnamese-ocr-toolbox/results/{img_id}"   #Path to save cropped regions
    )

    #ocr
    img_paths=os.listdir(f"/home/huynguyen14/workspace/fina/vietnamese-ocr-toolbox/results/{img_id}/crops") # Cropped regions
    img_paths.sort(key=natural_keys)
    img_paths = [os.path.join(f"/home/huynguyen14/workspace/fina/vietnamese-ocr-toolbox/results/{img_id}/crops", i) for i in img_paths]

    texts, probs = ocr_model.predict_folder(img_paths, return_probs=True) # OCR
    texts = correction(texts)   # Word correction
    
    #plot image
    images = [image_file, img_det]
    caption = ['raw', 'preprocess']
    # st.image(images, caption=["some generic text"] * len(images), width=400)
    with st.container():
        col1, col2, col3 = st.columns((0.8, 0.8, 0.6))

        with col1:
            st.image(images[0], width=600, caption=caption[0])
        with col2:
            st.image(images[1], width=600, caption=caption[1])
        with col3:
            st.write(texts)
            st.write('Process time: ' + str(round(time.time() - start, 2)) + 'seconds')
            st.markdown('<h3 style="color: green;">OCR image done !!!</h3>',
                          unsafe_allow_html=True)

    # cols = cycle(st.columns(2)) # st.columns here since it is out of beta at the time I'm writing this
    # for idx, filteredImage in enumerate(images):
    #     next(cols).image(filteredImage, width=400, caption=caption[idx])
    # st.write(texts)

if __name__ == '__main__':
    image_file = st.file_uploader("Upload Image",type=['jpg','png','jpeg','JPG'])
    if st.button("Convert"):
        if image_file is not None:
            process(image_file, \
                det_weight='/home/huynguyen14/workspace/fina/vietnamese-ocr-toolbox/weights/PANNet_best_map.pth', \
                ocr_weight='/home/huynguyen14/workspace/fina/vietnamese-ocr-toolbox/weights/transformerocr.pth')
