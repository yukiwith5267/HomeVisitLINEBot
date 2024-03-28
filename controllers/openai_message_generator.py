import requests

class OpenAIResponseCreator:
    def __init__(self, openai_api_key):
        self.openai_api_key = openai_api_key
        self.openai_api_endpoint = "https://api.openai.com/v1/chat/completions"
    
    def generate_response(self, user_message):
        # OpenAI APIを使ってメッセージを生成する
        messages = [
            {"role": "system", "content": "一言で返して"},
            {"role": "user", "content": user_message}
        ]
        response = requests.post(
            self.openai_api_endpoint,
            headers={
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4",
                "messages": messages
            }
        )
        if response.status_code == 200:
            response_message = response.json()["choices"][0]["message"]["content"]
        else:
            response_message = "メッセージを生成できませんでした。"
        return response_message
