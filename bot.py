import random
import requests
from datetime import datetime
import os

# 从环境变量读取
ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN')
INSTANCE = os.environ.get('INSTANCE_URL')

# 配置路径
TEXT_FILE = "sentences.txt"
IMAGE_FOLDER = "images"

# 获取随机内容
def get_random_content():
    content_list = []

    # 加入文字内容
    if os.path.exists(TEXT_FILE):
        with open(TEXT_FILE, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
            content_list.extend(lines)

    # 加入图片路径
    if os.path.isdir(IMAGE_FOLDER):
        for file in os.listdir(IMAGE_FOLDER):
            if file.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
                content_list.append(os.path.join(IMAGE_FOLDER, file))

    if not content_list:
        print("没有可发送的文字或图片。")
        return None

    return random.choice(content_list)

# 上传图片并返回媒体ID
def upload_media(image_path):
    url = f"{INSTANCE}/api/v2/media"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }
    with open(image_path, "rb") as img:
        files = {"file": img}
        response = requests.post(url, headers=headers, files=files)
    if response.status_code == 200:
        media_id = response.json().get("id")
        print(f"图片上传成功，media_id: {media_id}")
        return media_id
    else:
        print(f"图片上传失败：{response.status_code} {response.text}")
        return None

# 发帖
def post_status(content):
    url = f"{INSTANCE}/api/v1/statuses"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }

    if os.path.isfile(content):  # 是图片路径
        media_id = upload_media(content)
        if not media_id:
            return
        data = {
            "status": "",  # 图片发帖不附加文字
            "media_ids[]": media_id
        }
        r = requests.post(url, headers=headers, data=data)
    else:  # 是文字
        data = {
            "status": content
        }
        r = requests.post(url, headers=headers, data=data)

    print(f"{datetime.now()} 状态码: {r.status_code}")
    print(r.text)

# 主程序
if __name__ == "__main__":
    if not ACCESS_TOKEN or not INSTANCE:
        print("请确保环境变量 ACCESS_TOKEN 和 INSTANCE_URL 已设置。")
        exit(1)

    selected = get_random_content()
    if selected:
        print("将发送：", selected)
        post_status(selected)