import random
import requests
from datetime import datetime, timezone
import os

ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
INSTANCE = os.getenv('INSTANCE_URL')

if not ACCESS_TOKEN or not INSTANCE:
    print("请设置环境变量 ACCESS_TOKEN 和 INSTANCE_URL")
    exit(1)

TEXT_FILE = "sentences.txt"
IMAGE_FOLDER = "images"

def get_random_content():
    """
    随机获取待发送的内容（文字段落或图片路径）
    1. 从文本文件中读取全文，用空行分隔成段落，每段可以是多行文本
    2. 从图片文件夹读取所有支持格式的图片路径
    3. 如果都没有内容返回 None
    4. 随机返回其中一条内容
    """
    content_list = []

    if os.path.exists(TEXT_FILE):
        with open(TEXT_FILE, "r", encoding="utf-8") as f:
            text = f.read()
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            content_list.extend(paragraphs)

    if os.path.isdir(IMAGE_FOLDER):
        for file in os.listdir(IMAGE_FOLDER):
            if file.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
                content_list.append(os.path.join(IMAGE_FOLDER, file))

    if not content_list:
        print("没有可发送的文字或图片。")
        return None

    return random.choice(content_list)

def upload_media(image_path):
    url = f"{INSTANCE}/api/v2/media"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    try:
        with open(image_path, "rb") as img:
            files = {"file": img}
            response = requests.post(url, headers=headers, files=files)
        if response.status_code == 200:
            return response.json()["id"]
        else:
            print(f"图片上传失败：{response.text}")
            return None
    except Exception as e:
        print(f"上传图片异常：{e}")
        return None

def post_status(content):
    url = f"{INSTANCE}/api/v1/statuses"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    try:
        if os.path.isfile(content):
            media_id = upload_media(content)
            if not media_id:
                return
            data = {"status": "", "media_ids[]": [media_id]}
        else:
            data = {"status": content}
        r = requests.post(url, headers=headers, data=data)
        print(f"{datetime.now(timezone.utc)} 状态码: {r.status_code}")
        print(r.text)
    except Exception as e:
        print(f"发帖异常：{e}")

def job():
    print(f"{datetime.now(timezone.utc)} 开始执行定时任务")
    selected = get_random_content()
    if selected:
        print("将发送：", selected)
        post_status(selected)
    else:
        print("没有内容发送")

if __name__ == "__main__":
    print("机器人启动，执行一次任务后退出...")
    job()
