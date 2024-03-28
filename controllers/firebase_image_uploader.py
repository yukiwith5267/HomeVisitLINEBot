# Module Practice
import firebase_admin
from firebase_admin import credentials, storage
from datetime import datetime
import os

class ImageHandler:
    def __init__(self, cred_path='config/serviceAccountKey.json'):
        self.cred_path = cred_path
        self.file_path = 'data/captured_image.jpg' 
        
        if not firebase_admin._apps:
            cred = credentials.Certificate(self.cred_path)
            firebase_admin.initialize_app(cred, {
                'storageBucket': 'linebot-images.appspot.com' # gs:// prefix is not needed
            })

    def upload(self):
        """Uploads the captured image to Firebase and sends it via LINE bot."""

        # Check if the image was captured and exists before uploading
        if not os.path.exists(self.file_path):
            print("Image does not exist, make sure to capture it first.")
            return
        
        current_time = datetime.now().strftime('%Y%m%d%H%M%S')
        blob_name = f'uploads/captured_{current_time}.jpg'
        bucket = storage.bucket()
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(self.file_path)
        blob.make_public()
        public_url = blob.public_url
        return public_url 

# # Usage example
# image = ImageHandler()

# # To upload an image and send it via LINE bot
# image.upload(LINE_CHANNEL_ACCESS_TOKEN, LINE_USER_ID)