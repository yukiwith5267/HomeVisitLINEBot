import os
import json
import time
import pigpio
import pygame
import requests
import pyaudio
import numpy as np
import threading
import subprocess
from fastapi import FastAPI, Request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage
from dotenv import load_dotenv
from controllers import ImageHandler, OpenAIResponseCreator, SwitchBotController

load_dotenv()

# 環境変数
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
LINE_CHANNEL_SECRET_TOKEN = os.environ.get('LINE_CHANNEL_SECRET_TOKEN')
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_USER_ID = os.environ.get('LINE_USER_ID')
SWITCHBOT_AUTH_TOKEN = os.environ.get('SWITCHBOT_AUTH_TOKEN')

# PyAudio 設定
CHUNK = 1024 * 8
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 48000
RECORD_SECONDS = 1
rng = int(RATE / CHUNK * RECORD_SECONDS)

with open('config/fft_detection_config.json', 'r') as config_file:
    config = json.load(config_file)
    
threshold = config['threshold']
threshold2 = config['threshold2']
freq_indices = config['freq_indices']
freq_indices2 = [f * 2 for f in freq_indices]

app = FastAPI()

# サーボモーターとGPIO
SERVO_PIN = 18
pi = pigpio.pi()

# pygameの初期化
pygame.mixer.init()

# ハンドラーとコントローラーのインスタンス化
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET_TOKEN)
imageHandler = ImageHandler()
messageHandler = OpenAIResponseCreator(OPENAI_API_KEY)
switchbotController = SwitchBotController(SWITCHBOT_AUTH_TOKEN)

def setup():
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    return p, stream

def collect_data(stream, rng, CHUNK):
    frames = [stream.read(CHUNK, exception_on_overflow=False) for _ in range(rng)]
    d = np.frombuffer(b''.join(frames), dtype='int16')
    return d

def calc_FFTamp(frames, freq_indices, freq_indices2):
    fft_data = np.abs(np.fft.fft(frames))
    return sum(fft_data[i] for i in freq_indices), sum(fft_data[i] for i in freq_indices2)

def set_servo_angle(angle):
    if not 0 <= angle <= 180:
        raise ValueError('角度は0から180の間に設定してください')
    pulse_width = (angle / 180) * (2500 - 500) + 500
    pi.set_servo_pulsewidth(SERVO_PIN, pulse_width)

def play_sound(file_path):
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
        
def capture():
    try:
        subprocess.run(["fswebcam", "-r", "1280x720", "--no-banner", "data/captured_image.jpg"])
        return True
    except Exception as e:
        print(f"Failed to capture image: {e}")
        return False
       
@app.post("/callback")
async def callback(request: Request):
    # Callback処理
    body = await request.body()
    signature = request.headers['X-Line-Signature']
    try:
        handler.handle(body.decode('utf-8'), signature)
    except InvalidSignatureError:
        return 'Invalid signature'
    return 'OK'

# LINEメッセージイベントの処理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    
    if isinstance(event.message, TextMessage):
        text = event.message.text
        if text == 'ただいま':
            set_servo_angle(60)
            time.sleep(0.5)
            set_servo_angle(90)
            time.sleep(0.5)
            set_servo_angle(119)
            time.sleep(0.5)
            set_servo_angle(90)
            time.sleep(1)
            response_text = messageHandler.generate_response("ただいま")
            line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=response_text))
        elif text == '開けて':
            set_servo_angle(60)
            time.sleep(0.5)
            set_servo_angle(90)
            time.sleep(1.5)
            set_servo_angle(119)
            time.sleep(0.5)
            set_servo_angle(90)
            time.sleep(1)
            capture()
            image_url = imageHandler.upload()
            response_text = messageHandler.generate_response("開けてくれた？")
            messages = [TextSendMessage(text=response_text), ImageSendMessage(original_content_url=image_url, preview_image_url=image_url)]
            line_bot_api.push_message(LINE_USER_ID, messages=messages)
        elif text == '置き配して':
            set_servo_angle(60)
            time.sleep(0.5)
            set_servo_angle(90)
            play_sound("audio/delivery_announcement.mp3")
            set_servo_angle(119)
            time.sleep(0.5)
            set_servo_angle(90)
            time.sleep(1)
            capture()
            image_url = imageHandler.upload()
            response_text = messageHandler.generate_response("開けてくれた？")
            messages = [TextSendMessage(text=response_text), ImageSendMessage(original_content_url=image_url, preview_image_url=image_url)]
            line_bot_api.push_message(LINE_USER_ID, messages=messages)
        elif text == 'Uber予約おねがい':
            line_bot_api.reply_message(event.reply_token, TextSendMessage("🙆‍♀️"))
            with open("data/flag.txt", "w") as flag_file:
                flag_file.write("False")
            def data_collection_thread(stream, rng, CHUNK):  # stream を引数として追加
                print("Watching...")
                while True:
                    d = collect_data(stream, rng, CHUNK)            
                    amp, amp2 = calc_FFTamp(d, freq_indices, freq_indices2)
                    if (amp > threshold) and (amp/amp2 > threshold2):
                        print("Someone is at the door.")
                        time.sleep(6)
                        set_servo_angle(60)
                        time.sleep(0.5)
                        set_servo_angle(90)
                        time.sleep(1.5)
                        set_servo_angle(119)
                        time.sleep(0.5)
                        set_servo_angle(90)
                        time.sleep(3)
                        capture()
                        image_url = imageHandler.upload()
                        response_text = messageHandler.generate_response("開けてくれた？")
                        messages = [TextSendMessage(text=response_text), ImageSendMessage(original_content_url=image_url, preview_image_url=image_url)]
                        line_bot_api.push_message(LINE_USER_ID, messages=messages)
                        with open("data/flag.txt", "w") as flag_file:
                            flag_file.write("True")
                        break
            p, stream = setup()
            data_thread = threading.Thread(target=data_collection_thread, args=(stream, rng, CHUNK))
            data_thread.start()   
        elif text == '置き配予約おねがい':
            line_bot_api.reply_message(event.reply_token, TextSendMessage("🙆‍♀️"))
            with open("data/flag.txt", "w") as flag_file:
                flag_file.write("False")
            def data_collection_thread(stream, rng, CHUNK):  # stream を引数として追加
                print("Watching...")
                while True:
                    d = collect_data(stream, rng, CHUNK)            
                    amp, amp2 = calc_FFTamp(d, freq_indices, freq_indices2)
                    if (amp > threshold) and (amp/amp2 > threshold2):
                        print("Someone is at the door.")
                        time.sleep(6)
                        set_servo_angle(60)
                        time.sleep(0.5)
                        set_servo_angle(90)
                        time.sleep(0.5)
                        play_sound("audio/delivery_announcement.mp3")
                        set_servo_angle(119)
                        time.sleep(0.5)
                        set_servo_angle(90)
                        time.sleep(3)
                        capture()
                        image_url = imageHandler.upload()
                        response_text = messageHandler.generate_response("開けてくれた？")
                        messages = [TextSendMessage(text=response_text), ImageSendMessage(original_content_url=image_url, preview_image_url=image_url)]
                        line_bot_api.push_message(LINE_USER_ID, messages=messages)
                        with open("data/flag.txt", "w") as flag_file:
                            flag_file.write("True")
                        break
            p, stream = setup()
            data_thread = threading.Thread(target=data_collection_thread, args=(stream, rng, CHUNK))
            data_thread.start()
        elif text == '電気':
            switchbotController.toggle_devices()

if __name__ == "__main__":
    try:
        # アプリケーションの起動
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000, debug=False)
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
