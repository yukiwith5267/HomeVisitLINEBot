import time
import pyaudio
import wave
import numpy as np
import requests
import subprocess
import threading
import queue
import os
import json
import boto3
from dotenv import load_dotenv
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage
from controllers import ImageHandler

load_dotenv()

LINE_NOTIFY_TOKEN = os.getenv('LINE_NOTIFY_TOKEN')
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET_TOKEN = os.getenv('LINE_CHANNEL_SECRET_TOKEN')
LINE_USER_ID = os.getenv('LINE_USER_ID')

image = ImageHandler()
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

# data/flag.txtでmain.pyと連携し、二重通知、デバイスの使用の重複を避ける
flag_file = "data/flag.txt"

Check_every_time = False

RECORD_SECONDS = 1

with open('config/fft_detection_config.json', 'r') as config_file:
    config = json.load(config_file)
    
threshold = config['threshold']
threshold2 = config['threshold2']
freq_indices = config['freq_indices']
freq_indices2 = [f * 2 for f in freq_indices]

CHUNK = 1024 * 8
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 48000  # サンプルレートの設定 一般的な値は44100Hzまたは48000Hz
rng = int(RATE / CHUNK * RECORD_SECONDS)

def setup():
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    return p, stream

def collect_data(stream, rng, CHUNK):
    frames = []
    for i in range(rng):
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)
    d = np.frombuffer(b''.join(frames), dtype='int16')
    return d

def calc_FFTamp(frames, freq_indices, freq_indices2):
    fft_data = np.abs(np.fft.fft(frames))
    amp, amp2 = 0, 0
    for i in freq_indices:
        amp += fft_data[i]
    for i in freq_indices2:
        amp2 += fft_data[i]
    return amp, amp2

def capture():
    try:
        subprocess.run(["fswebcam", "-r", "1280x720", "--no-banner", "data/captured_image.jpg"])
        return True
    except Exception as e:
        print(f"Failed to capture image: {e}")
        return False

# Send message and image to Line Notify
def send_LineNotify(token, amp, amp2, threshold, threshold2):
    url = "https://notify-api.line.me/api/notify"
    headers = {"Authorization": "Bearer " + LINE_NOTIFY_TOKEN}
    message = "❗️\n強度 {:.2e} --- 基準 {:.1e}\n比率 {:.2e} --- 基準 {:.1e}".format(amp, threshold, amp / amp2, threshold2)
    payload = {"message": message}
    r = requests.post(url, headers=headers, params=payload)

# collect_data関数をマルチスレッドで実行するための関数
def collect_data_thread(stream, rng, CHUNK, data_queue):
    frames = []
    for i in range(rng):
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)
    d = np.frombuffer(b''.join(frames), dtype='int16')
    data_queue.put(d)

if __name__ == '__main__':
    p, stream = setup()
    data_queue = queue.Queue()  # データを格納するためのキューを作成
    try:
        while True:
            with open("data/flag.txt", "r") as flag_file:
                flag = flag_file.read().strip()
            if flag == "True":
                # マルチスレッドで音声データを収集
                thread = threading.Thread(target=collect_data_thread, args=(stream, rng, CHUNK, data_queue))
                thread.start()

                # 音声データを取得
                thread.join()
                d = data_queue.get()

                amp, amp2 = calc_FFTamp(d, freq_indices, freq_indices2)
                if (amp > threshold) and (amp / amp2 > threshold2):
                    print("Someone is at the door.")
                    send_LineNotify(LINE_NOTIFY_TOKEN, amp, amp2, threshold, threshold2)  # Send the image and message
                    capture()
                    image_url = image.upload()
                    messages = [TextSendMessage(text="だれか来たよ！(｡•̀ᴗ-)"), ImageSendMessage(original_content_url=image_url, preview_image_url=image_url)]
                    line_bot_api.push_message(LINE_USER_ID, messages=messages)
                    if Check_every_time:
                        pass
                    time.sleep(60)
                    print("Keep watching...")
    except KeyboardInterrupt:
        print('You terminated the program.\nThe program ends.')
        stream.stop_stream()
        stream.close()
        p.terminate()
