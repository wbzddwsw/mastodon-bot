import random
import requests
from datetime import datetime, timezone
import os

# 从环境变量中读取 Mastodon 访问令牌和实例地址
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
INSTANCE = os.getenv('INSTANCE_URL')

# 如果环境变量没有设置，程序会打印提示并退出，防止报错
if not ACCESS_TOKEN or not INSTANCE:
    print("请设置环境变量 ACCESS_TOKEN 和 INSTANCE_URL")
    exit(1)

# 文本文件路径，里面存放多段文字内容，段落之间用空行分隔
TEXT_FILE = "sentences.txt"
# 图片文件夹路径，存放待发送的图片文件
IMAGE_FOLDER = "images"

def get_random_content():
    """
    随机获取要发送的内容，可以是多段文字或者图片路径

    1. 读取文本文件，按空行分段，每段可以包含多行文本
    2. 读取图片文件夹，支持 png/jpg/jpeg/gif/webp 格式
    3. 合并文字段落和图片路径，随机选择一条返回
    4. 如果没有内容，返回 None
    """
    content_list = []

    # 读取文本内容（分段）
    if os.path.exists(TEXT_FILE):
        with open(TEXT_FILE, "r", encoding="utf-8") as f:
            # 读取整个文件，按两个换行符分割成段落
            text = f.read()
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            content_list.extend(paragraphs)

    # 读取图片文件路径
    if os.path.isdir(IMAGE_FOLDER):
        for filename in os.listdir(IMAGE_FOLDER):
            if filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
                full_path = os.path.join(IMAGE_FOLDER, filename)
                content_list.append(full_path)

    # 如果没有任何内容，返回 None
    if not content_list:
        print("没有可发送的文字或图片。")
        return None

    # 随机选择一条内容返回
    return random.choice(content_list)

def upload_media(image_path):
    """
    上传图片到 Mastodon 媒体库，返回媒体 ID 供发帖时使用

    - image_path: 本地图片文件路径
    - 成功返回媒体 ID（字符串）
    - 失败打印错误返回 None
    """
    url = f"{INSTANCE}/api/v2/media"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }
    try:
        with open(image_path, "rb") as img_file:
            files = {"file": img_file}
            response = requests.post(url, headers=headers, files=files)
        if response.status_code == 200:
            media_id = response.json().get("id")
            return media_id
        else:
            print(f"图片上传失败，状态码 {response.status_code}，内容: {response.text}")
            return None
    except Exception as e:
        print(f"上传图片异常：{e}")
        return None

def post_status(content):
    """
    发送帖子

    - 如果 content 是图片路径，先上传图片获得媒体 ID，再发一条只带图片的帖子
    - 如果是文字内容，直接发带文字的帖子
    - 打印发送状态和返回内容，方便调试
    """
    url = f"{INSTANCE}/api/v1/statuses"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }
    try:
        if os.path.isfile(content):
            # 如果是图片文件，先上传
            media_id = upload_media(content)
            if not media_id:
                print("上传图片失败，跳过发帖")
                return
            data = {
                "status": "",           # 只发图片，不带文字
                "media_ids[]": [media_id]
            }
        else:
            # 普通文字发帖
            data = {
                "status": content
            }
        response = requests.post(url, headers=headers, data=data)
        print(f"{datetime.now(timezone.utc)} 状态码: {response.status_code}")
        print(response.text)
    except Exception as e:
        print(f"发帖异常：{e}")

def main():
    """
    主程序入口，获取随机内容并发帖
    """
    now = datetime.now(timezone.utc)
    print(f"{now} - 开始执行发帖任务")

    content = get_random_content()
    if content:
        print("选中内容：", content)
        post_status(content)
    else:
        print("无可用内容，跳过发帖")

if __name__ == "__main__":
    main()
