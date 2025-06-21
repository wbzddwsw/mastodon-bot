import time
from datetime import datetime

if __name__ == "__main__":
    print("程序启动，开始持续打印时间...")

    while True:
        print(f"{datetime.now()} - 程序仍在运行")
        time.sleep(60)  # 每60秒打印一次