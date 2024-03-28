import concurrent.futures
import requests

class SwitchBotController:
    def __init__(self, auth_token):
        self.headers = {
            'Authorization': auth_token,
            'Content-Type': 'application/json; charset=utf8',
        }
        self.devices = [
            {
                'url': 'https://api.switch-bot.com/v1.0/devices/404CCAA594C2/commands',
                'data': {
                    "command": "toggle",
                    "parameter": "default",
                    "commandType": "command"
                }
            },
            {
                'url': 'https://api.switch-bot.com/v1.0/devices/404CCAA6CF9A/commands',
                'data': {
                    "command": "toggle",
                    "parameter": "default",
                    "commandType": "command"
                }
            }
        ]

    def toggle_devices(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(requests.post, device['url'], json=device['data'], headers=self.headers)
                for device in self.devices
            ]
            for future in concurrent.futures.as_completed(futures):
                response = future.result()
                print(response.json())  # or handle the response as needed

# # Usage example
# if __name__ == "__main__":
#     auth_token = '1bade265e71b80fbd266ce9e4cd031c683836796678edc47e7050884cb47f90c44eb7d4d308453318a5eca8bfe52fd31'
#     controller = SwitchBotController(auth_token)
#     controller.toggle_devices()
