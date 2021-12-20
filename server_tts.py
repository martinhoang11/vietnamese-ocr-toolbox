from os import times
import streamlit as st
import requests
import time
from urllib.request import urlopen


st.set_page_config(layout="wide")

url = 'https://api.fpt.ai/hmi/tts/v5'

def api(text, speech, speed):
    payload = text
    headers = {
        'api-key': 'nbpGjQTABwbYN220gQBOg1hT733Lq0xW',
        'speed': str(speed),
        'voice': speech
    }
    response = requests.request('POST', url, data=payload.encode('utf-8'), headers=headers)
    return response.json()

def play_audio():
    text = st.text_input('Input your sentence: ')
    res = api(text)
    return res['async']

if __name__ == '__main__':
    st.markdown("<h1 style='text-align: center; color: blue;'>Fina text to speech service</h1>", unsafe_allow_html=True)
    text = st.text_input('Input your sentence: ')

    speech = st.selectbox(
    "Select your people accent",
    (
        "banmai.ace",
        "thuminh.ace",
        "ngoclam.ace",
        "linhsan.ace",
        "minhquang.ace",
        "banmai",
        "thuminh",
        "ngoclam",
        "myan",
        "giahuy",
        "leminh",
        "minhquang",
        "linhsan",
        "lannhi",
    ))

    speed = st.slider("Select audio speech", -3, 3, 0)

    if st.button('Convert'):
        res = api(text, speech=speech, speed=speed)
        with st.spinner('Wait for it...'):
            time.sleep(3)
            st.success('Done!')
        st.audio(res['async'], format="audio/mp3", start_time=0)