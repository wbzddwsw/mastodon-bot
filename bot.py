import os
import random
import requests
from datetime import datetime, timedelta, timezone
import pytz

# ==== 必要配置 ====
MASTODON_API_BASE = "https://mas.to"  # 替换为你自己的实例
ACCESS_TOKEN = os.getenv("MASTODON_ACCESS_TOKEN")  # 建议通过环境变量注入
HEADERS = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

# ==== 工具函数 ====

def post_status(text, media_id=None):
    """发送文字（可选附带图片）到 Mastodon"""
    url = f"{MASTODON_API_BASE}/api/v1/statuses"
    payload = {
        "status": text,
        "visibility": "public",
    }
    if media_id:
        payload["media_ids[]"] = [media_id]

    r = requests.post(url, headers=HEADERS, data=payload)
    print("状态码:", r.status_code)
    print("响应内容:", r.text)

def upload_media(file_path):
    """上传图片文件，返回 media_id"""
    url = f"{MASTODON_API_BASE}/api/v2/media"
    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f)}
        r = requests.post(url, headers=HEADERS, files=files)

    if r.status_code == 200:
        return r.json().get("id")
    else:
        print("图片上传失败：", r.text)
        return None

def get_random_text():
    """从文本文件中读取并随机选择一个段落（多个换行也可以）"""
    with open("content/text.txt", "r", encoding="utf-8") as f:
        paragraphs = f.read().split("\n\n")  # 用两个换行分段
        return random.choice([p.strip() for p in paragraphs if p.strip()])

def get_random_image():
    """从 images 文件夹中随机选择一张图片"""
    image_dir = "content/images"
    if not os.path.exists(image_dir):
        return None
    images = [f for f in os.listdir(image_dir) if f.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp"))]
    if not images:
        return None
    return os.path.join(image_dir, random.choice(images))

# ==== 主任务 ====

def main():
    # 设置为东八区（北京时间）
    tz = pytz.timezone("Asia/Shanghai")
    now = datetime.now(tz)
    print(f"{now.isoformat()} 机器人开始运行")

    # 决定发图还是发文字
    if random.choice([True, False]):
        # 发文字
        text = get_random_text()
        if text:
            print("发送文字：", text[:30], "..." if len(text) > 30 else "")
            post_status(text)
    else:
        # 发图+说明
        image_path = get_random_image()
        text = get_random_text()
        if image_path:
            print("将发送图片：", image_path)
            media_id = upload_media(image_path)
            if media_id:
                post_status(text or "", media_id)
        else:
            print("没有找到可用的图片。")

if __name__ == "__main__":
    main()