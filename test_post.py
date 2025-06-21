import requests
from datetime import datetime
import os

ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
INSTANCE = os.getenv('INSTANCE_URL')

def post_status(content):
    url = f"{INSTANCE}/api/v1/statuses"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }
    data = {
        "status": content
    }
    r = requests.post(url, headers=headers, data=data)
    print(f"{datetime.now()} 状态码: {r.status_code}")
    print(r.text)

if __name__ == "__main__":
    test_content = "测试：这是一条来自Railway的测试消息！"
    print("马上发送测试消息：", test_content)
    post_status(test_content)