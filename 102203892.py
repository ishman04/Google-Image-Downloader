from flask import Flask, request, render_template, send_file, jsonify
import os
import requests
from googleapiclient.discovery import build
import zipfile
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import smtplib
import threading

API_KEY = 'AIzaSyBJRN3dr9BChmjGT5ZPkjlZrC-CYOCkfVs'
CSE_ID = '11d805ad410224eef'

app = Flask(__name__, template_folder=os.path.abspath('templates'))

def search_and_download_images(query, num_images, save_dir):
    service = build("customsearch", "v1", developerKey=API_KEY)
    image_urls = []

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    start_index = 1
    while len(image_urls) < num_images:
        res = service.cse().list(
            q=query,
            cx=CSE_ID,
            searchType='image',
            num=min(10, num_images - len(image_urls)),
            start=start_index
        ).execute()

        if 'items' in res:
            for item in res['items']:
                image_urls.append(item['link'])

        start_index += 10
        if len(res['items']) < 10:
            break

    for i, url in enumerate(image_urls):
        try:
            print(f'Downloading {url}')
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                image_path = os.path.join(save_dir, f'image_{i+1}.jpg')
                with open(image_path, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
            else:
                print(f"Failed to download image from {url}")
        except Exception as e:
            print(f"Error downloading {url}: {e}")

    print(f"Downloaded {len(image_urls)} images.")

def send_email(recipient_email, zip_file_path):
    if not os.path.exists(zip_file_path):
        print(f"Error: ZIP file not found at {zip_file_path}")
        return

    sender_email = "ishmanalagh@gmail.com"
                    
    password = 'oxip jmqu hskv xwya' 

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = "Your images are ready!"

    body = "Here's your images. Enjoy!"
    msg.attach(MIMEText(body, 'plain'))

    try:
        with open(zip_file_path, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())

        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename= {os.path.basename(zip_file_path)}",
        )
        msg.attach(part)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, password)
            server.send_message(msg)
        
        print(f"Email sent successfully to {recipient_email}")
    except Exception as e:
        print(f"Error sending email: {str(e)}")

def zip_downloaded_images(zip_filename, folder_to_zip):
    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        for foldername, subfolders, filenames in os.walk(folder_to_zip):
            for filename in filenames:
                file_path = os.path.join(foldername, filename)
                zipf.write(file_path, os.path.basename(file_path))
    return f"{zip_filename} created successfully."

def process_search(keyword, num, save_dir, recipient_email):
    search_and_download_images(keyword, num, save_dir)
    zip_filename = './downloaded_images.zip'
    zip_downloaded_images(zip_filename, save_dir)
    send_email(recipient_email, zip_filename)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_mashup', methods=['POST'])
def generate_mashup():
    try:
        print("Received request for generate_mashup")
        print("Form data:", request.form)
        
        keyword = request.form['singerName']
        num = int(request.form['numVideos'])
        save_dir = './images'
        recipient_email = request.form['email']
        
        print(f"Processing request: keyword={keyword}, num={num}, email={recipient_email}")
        
        thread = threading.Thread(target=process_search, args=(keyword, num, save_dir, recipient_email))
        thread.start()
        
        return jsonify({"message": f"Mashup generation started. The file will be sent to {recipient_email} when ready."})
    except Exception as e:
        print(f"Error occurred in generate_mashup: {str(e)}")
        return jsonify({"message": f"Error: {str(e)}"}), 500


if __name__ == '__main__':
    print("Current working directory:", os.getcwd())
    print("Template folder path:", os.path.abspath('templates'))
    app.run(debug=True)
