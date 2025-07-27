import random
import requests
from datetime import datetime, timezone
import os
import schedule
import time

# 从环境变量读取 Mastodon 访问令牌和实例地址
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
INSTANCE = os.getenv('INSTANCE_URL')

# 如果环境变量未设置，则程序退出并提示用户
if not ACCESS_TOKEN or not INSTANCE:
    print("请设置环境变量 ACCESS_TOKEN 和 INSTANCE_URL")
    exit(1)

# 文本内容文件路径（根目录下）
TEXT_FILE = "sentences.txt"

# 图片文件夹路径（根目录下）
IMAGE_FOLDER = "images"

def get_random_content():
    """
    随机获取待发送的内容（文字段落或图片路径）

    逻辑：
    1. 从sentences.txt读取全文，使用空行（两个换行）分段，每段可以包含多行文字
    2. 读取images文件夹内所有支持格式的图片路径
    3. 把文字段落和图片路径混合到一个列表中，随机选一个返回
    4. 若无内容则返回 None
    """
    content_list = []

    # 读取文本段落
    if os.path.exists(TEXT_FILE):
        with open(TEXT_FILE, "r", encoding="utf-8") as f:
            text = f.read()
            # 以连续两个换行分段，过滤掉空白段落
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            content_list.extend(paragraphs)

    # 读取图片文件
    if os.path.isdir(IMAGE_FOLDER):
        for file in os.listdir(IMAGE_FOLDER):
            if file.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
                content_list.append(os.path.join(IMAGE_FOLDER, file))

    if not content_list:
        print("没有可发送的文字或图片。")
        return None

    # 返回随机选中的一条
    return random.choice(content_list)

def upload_media(image_path):
    """
    上传图片到 Mastodon 实例，返回媒体 ID
    """
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
    """
    发帖函数
    - 如果是图片路径，先上传图片，成功后发空文字带图片帖子
    - 如果是文字段落，直接发带文字的帖子
    """
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
    """
    定时任务执行函数
    """
    print(f"{datetime.now(timezone.utc)} 开始执行定时任务")
    selected = get_random_content()
    if selected:
        print("将发送：", selected)
        post_status(selected)
    else:
        print("没有内容发送")

def heartbeat():
    """
    心跳函数，防止容器休眠
    """
    now_utc = datetime.now(timezone.utc)
    print(f"{now_utc} 心跳：程序仍在运行... 防止容器休眠")

if __name__ == "__main__":
    print("机器人启动，等待定时发送...")

    # 服务器是 UTC 时间，北京时间 = UTC + 8 小时
    # 所以北京时间09:00对应UTC 01:00，21:00对应UTC 13:00
    schedule.every().day.at("01:00").do(job)  # 北京时间09:00
    schedule.every().day.at("13:00").do(job)  # 北京时间21:00

    schedule.every(5).minutes.do(heartbeat)  # 每5分钟心跳一次

    while True:
        schedule.run_pending()
        time.sleep(1)
