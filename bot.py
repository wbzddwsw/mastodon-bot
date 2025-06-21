import random
import requests
from datetime import datetime
import os
import schedule
import time

# 从环境变量获取 Mastodon 访问令牌和实例地址
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
INSTANCE = os.getenv('INSTANCE_URL')

# 存放文字的文件和图片文件夹路径
TEXT_FILE = "sentences.txt"
IMAGE_FOLDER = "images"

# 随机获取一条内容（文字或图片）
def get_random_content():
    content_list = []

    # 读取文字内容，去除空行
    if os.path.exists(TEXT_FILE):
        with open(TEXT_FILE, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
            content_list.extend(lines)

    # 读取图片文件路径，支持多种格式
    if os.path.isdir(IMAGE_FOLDER):
        for file in os.listdir(IMAGE_FOLDER):
            if file.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
                content_list.append(os.path.join(IMAGE_FOLDER, file))

    # 如果没有内容，返回 None
    if not content_list:
        print("没有可发送的文字或图片。")
        return None

    # 随机选择一条内容返回
    return random.choice(content_list)

# 上传图片文件，返回媒体ID
def upload_media(image_path):
    url = f"{INSTANCE}/api/v2/media"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }
    # 以二进制方式打开图片，上传
    with open(image_path, "rb") as img:
        files = {"file": img}
        response = requests.post(url, headers=headers, files=files)
    # 上传成功返回媒体ID
    if response.status_code == 200:
        return response.json()["id"]
    else:
        print(f"图片上传失败：{response.text}")
        return None

# 发帖函数，根据内容类型发送文字或图片
def post_status(content):
    url = f"{INSTANCE}/api/v1/statuses"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }

    if os.path.isfile(content):  # 如果是图片路径
        media_id = upload_media(content)
        if not media_id:
            return  # 上传失败就不发帖了
        data = {
            "status": "",  # 不附加文字
            "media_ids[]": [media_id]
        }
    else:  # 如果是文字内容
        data = {
            "status": content
        }

    # 发送请求发帖
    r = requests.post(url, headers=headers, data=data)
    print(f"{datetime.now()} 状态码: {r.status_code}")
    print(r.text)

# 定时任务函数，每次执行时随机选内容发帖
def job():
    print(f"{datetime.now()} 开始执行定时任务")
    selected = get_random_content()
    if selected:
        print("将发送：", selected)
        post_status(selected)
    else:
        print("没有内容发送")

# 主程序入口，设置每天两次定时任务
if __name__ == "__main__":
    print("机器人启动，等待定时发送...")
    # 每天9:00执行一次job
    schedule.every().day.at("09:00").do(job)
    # 每天21:00执行一次job
    schedule.every().day.at("21:00").do(job)

    # 无限循环，等待执行任务
    while True:
        schedule.run_pending()
        time.sleep(60)