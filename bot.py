import random
import requests
from datetime import datetime
import os
import schedule
import time

# 从环境变量读取 Mastodon 访问令牌和实例地址
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
INSTANCE = os.getenv('INSTANCE_URL')

# 如果环境变量没有设置，程序直接退出并打印提示
if not ACCESS_TOKEN or not INSTANCE:
    print("请设置环境变量 ACCESS_TOKEN 和 INSTANCE_URL")
    exit(1)

# 文字内容文件路径，存放待发送的文本句子
TEXT_FILE = "sentences.txt"
# 图片文件夹路径，存放待发送的图片文件
IMAGE_FOLDER = "images"

def get_random_content():
    """
    从文本文件和图片文件夹中随机选取一条内容。
    先读取文本文件中的每一行非空文本，加入候选列表。
    再扫描图片文件夹，支持多种图片格式，加入候选列表。
    如果都没有内容，返回 None。
    返回随机选中的文本或图片路径。
    """
    content_list = []

    # 读取文本文件内容
    if os.path.exists(TEXT_FILE):
        with open(TEXT_FILE, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]  # 过滤空行
            content_list.extend(lines)

    # 读取图片文件列表
    if os.path.isdir(IMAGE_FOLDER):
        for file in os.listdir(IMAGE_FOLDER):
            # 支持常见图片格式（不区分大小写）
            if file.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
                content_list.append(os.path.join(IMAGE_FOLDER, file))

    # 如果候选列表为空，提示并返回 None
    if not content_list:
        print("没有可发送的文字或图片。")
        return None

    # 随机选取一条内容返回
    return random.choice(content_list)

def upload_media(image_path):
    """
    上传图片到 Mastodon 实例，返回媒体ID。
    使用 /api/v2/media 接口。
    如果上传失败，打印错误信息并返回 None。
    """
    url = f"{INSTANCE}/api/v2/media"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }
    try:
        # 以二进制模式打开图片文件
        with open(image_path, "rb") as img:
            files = {"file": img}
            # 发送POST请求上传图片
            response = requests.post(url, headers=headers, files=files)
        if response.status_code == 200:
            # 返回媒体ID，供发帖时引用
            return response.json()["id"]
        else:
            print(f"图片上传失败：{response.text}")
            return None
    except Exception as e:
        print(f"上传图片异常：{e}")
        return None

def post_status(content):
    """
    根据传入内容发帖：
    - 如果传入的是图片文件路径，先上传图片，获得media_id，再发空文字带图片的帖子；
    - 如果是普通文字，直接发文字帖子。
    发送完成后打印响应状态码和返回内容。
    """
    url = f"{INSTANCE}/api/v1/statuses"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }
    try:
        if os.path.isfile(content):  # 是图片路径
            media_id = upload_media(content)
            if not media_id:
                return  # 上传失败不发帖
            data = {
                "status": "",  # 不附加文字
                "media_ids[]": [media_id]  # 关联已上传图片
            }
        else:  # 是文字内容
            data = {
                "status": content
            }
        # 发送发帖请求
        r = requests.post(url, headers=headers, data=data)
        print(f"{datetime.now()} 状态码: {r.status_code}")
        print(r.text)
    except Exception as e:
        print(f"发帖异常：{e}")

def job():
    """
    定时执行的任务函数：
    - 随机获取一条待发送内容
    - 如果有内容，调用发帖函数发送
    - 如果无内容，打印提示
    """
    print(f"{datetime.now()} 开始执行定时任务")
    selected = get_random_content()
    if selected:
        print("将发送：", selected)
        post_status(selected)
    else:
        print("没有内容发送")

if __name__ == "__main__":
    print("机器人启动，等待定时发送...")

    # 设置每天09:00执行job任务
    schedule.every().day.at("09:00").do(job)
    # 设置每天21:00执行job任务
    schedule.every().day.at("21:00").do(job)

    # 主循环，等待定时任务执行，每60秒检查一次
    while True:
        schedule.run_pending()
        time.sleep(60)