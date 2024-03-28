# HomeVisitLINEBot

![](images/Screenshot29.png)

## Setup

1. **FFT intercom**: Edit `fft_detection_config.json` in the fft directory:

[How to fft the intercom](https://github.com/yukiwith5267/Linebot-Unlocker/tree/main/fft)
   ```json
   {
     "threshold": "<Your_Threshold_Value>",
     "freq_indices": "<Your_Frequency_Indices>"
   }
   ```

2. **Environment Variables**: Set up a `.env` file at the project root for environment variables. Include the following:

   ```.env
   LINE_CHANNEL_SECRET_TOKEN=<Your_LINE_Channel_Secret_Token>
   LINE_CHANNEL_ACCESS_TOKEN=<Your_LINE_Channel_Access_Token>
   OPENAI_API_KEY=<Your_OpenAI_API_Key>
   LINE_USER_ID=<Your_LINE_User_ID>
   SWITCHBOT_AUTH_TOKEN=<Your_SwitchBot_Auth_Token>
   LINE_NOTIFY_TOKEN=<Your_LINE_Notify_Token>
   ```

3. Installation and Execution

```bash
# Update system and install dependencies
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install tmux portaudio19-dev libopenblas-dev python3-pandas fswebcam -y

# Setup virtual environment
python -m venv env
source env/bin/activate
pip install -r requirements.txt

# Start sessions in tmux for concurrent script execution
# Session 1: Run notify.py
tmux new-session -d -s mySession 'source env/bin/activate; python notify.py'

# Session 2: Run main.py
tmux new-window 'source env/bin/activate; sudo pigpiod; uvicorn main:app --host 0.0.0.0 --port 8000 --reload'
```

## Exposing Localhost to the Internet

**Using ngrok:**

```bash
wget https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-arm.zip
unzip ngrok-stable-linux-arm.zip
chmod +x ngrok
sudo mv ngrok /usr/local/bin/
ngrok authtoken YOUR_AUTHTOKEN
ngrok http 8000
```

**Using Cloudflare Tunnel:**

- Obtain a domain (e.g., through squarespace) and register Cloudflare DNS:
  [https://domains.squarespace.com/](https://domains.squarespace.com/)
  [https://account.squarespace.com/domains/managed/{your_domain}/dns/domain-nameservers](https://account.squarespace.com/domains/managed/{your_domain}/dns/domain-nameservers)
