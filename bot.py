import random
import requests
from datetime import datetime
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

# 存放文本内容的文件路径
TEXT_FILE = "sentences.txt"
# 存放图片的文件夹路径
IMAGE_FOLDER = "images"

def get_random_content():
    """
    随机获取待发送的内容（文字或图片路径）
    1. 先从文本文件读取非空行，加入候选列表
    2. 再从图片文件夹读取所有支持格式的图片路径，加入候选列表
    3. 如果候选列表为空，返回 None
    4. 否则返回随机选中的一条内容
    """
    content_list = []

    # 检查文本文件是否存在并读取内容
    if os.path.exists(TEXT_FILE):
        with open(TEXT_FILE, "r", encoding="utf-8") as f:
            # 读取每一行并去除空白字符，过滤空行
            lines = [line.strip() for line in f if line.strip()]
            content_list.extend(lines)

    # 检查图片文件夹是否存在并读取支持的图片文件
    if os.path.isdir(IMAGE_FOLDER):
        for file in os.listdir(IMAGE_FOLDER):
            # 支持 png, jpg, jpeg, gif, webp 格式（不区分大小写）
            if file.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
                # 拼接完整路径加入候选列表
                content_list.append(os.path.join(IMAGE_FOLDER, file))

    # 如果没有任何可用内容，打印提示并返回 None
    if not content_list:
        print("没有可发送的文字或图片。")
        return None

    # 从候选内容中随机选择一条返回
    return random.choice(content_list)

def upload_media(image_path):
    """
    上传图片到 Mastodon 实例，返回媒体 ID 以供发帖时引用
    失败时打印错误并返回 None
    """
    url = f"{INSTANCE}/api/v2/media"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }
    try:
        # 以二进制方式打开图片文件
        with open(image_path, "rb") as img:
            files = {"file": img}
            # 发送 POST 请求上传图片
            response = requests.post(url, headers=headers, files=files)
        if response.status_code == 200:
            # 成功返回媒体 ID
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
    - 如果传入的是图片路径，先调用 upload_media 上传，再发空文字附带图片的帖子
    - 如果是普通文字，则直接发文字帖子
    发送完成后打印响应状态码和内容
    """
    url = f"{INSTANCE}/api/v1/statuses"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }
    try:
        if os.path.isfile(content):  # 判断是否为文件（图片）
            media_id = upload_media(content)  # 上传图片，获取媒体 ID
            if not media_id:
                return  # 上传失败，跳过发帖
            data = {
                "status": "",            # 不附带文字
                "media_ids[]": [media_id]  # 附带上传成功的图片 ID
            }
        else:
            # 普通文字直接发帖
            data = {
                "status": content
            }
        # 发送发帖请求
        r = requests.post(url, headers=headers, data=data)
        # 打印当前 UTC 时间，响应状态码和返回内容，方便调试
        print(f"{datetime.utcnow()} 状态码: {r.status_code}")
        print(r.text)
    except Exception as e:
        print(f"发帖异常：{e}")

def job():
    """
    定时任务执行函数
    - 获取一条随机内容（文字或图片）
    - 如果有内容，调用发帖函数发送
    - 如果没有，打印提示信息
    """
    print(f"{datetime.utcnow()} 开始执行定时任务")
    selected = get_random_content()
    if selected:
        print("将发送：", selected)
        post_status(selected)
    else:
        print("没有内容发送")

def heartbeat():
    """
    心跳函数，用于每隔一段时间打印日志，防止容器被平台判定为空闲自动休眠。
    使用带时区的 UTC 时间打印，避免弃用警告。
    """
    now_utc = datetime.now(timezone.utc)  # 获取当前UTC时间，带时区信息
    print(f"{now_utc} 心跳：程序仍在运行... 防止容器休眠")

if __name__ == "__main__":
    print("机器人启动，等待定时发送...")

    # 由于服务器时区是 UTC，我们要把北京时间 09:00 和 21:00 转换为 UTC 时间
    # 北京时间 = UTC +8小时
    # 所以北京时间 09:00 = UTC 01:00
    # 北京时间 21:00 = UTC 13:00
    schedule.every().day.at("01:00").do(job)  # UTC 时间 01:00，实际北京时间 09:00
    schedule.every().day.at("13:00").do(job)  # UTC 时间 13:00，实际北京时间 21:00

    # 每分钟执行一次心跳打印，防止容器因无日志输出被休眠
    schedule.every(5).minutes.do(heartbeat)

    # 主循环，循环执行所有待运行的任务，每秒检测一次
    while True:
        schedule.run_pending()
        time.sleep(1)