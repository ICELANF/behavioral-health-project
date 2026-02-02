import requests
import time
import random
import math
from datetime import datetime

# 配置后端地址
API_URL = "http://127.0.0.1:8002/intervene"
USER_ID = 1001
USER_NAME = "老张"

def generate_glucose(tick):
    """
    模拟血糖波动曲线
    使用正弦函数模拟餐后波动 + 随机噪声
    """
    base = 7.0  # 基准血糖
    amplitude = 4.0  # 波动幅度
    # 模拟一个周期性的起伏
    variation = amplitude * math.sin(tick / 5.0)
    noise = random.uniform(-0.5, 0.5)
    return round(base + variation + noise, 1)

def start_simulation():
    print(f"🚀 CGM 模拟器已启动，正在向 {API_URL} 推送数据...")
    tick = 0
    
    try:
        while True:
            # 1. 生成模拟血糖
            current_val = generate_glucose(tick)
            
            # 2. 模拟行为标签（例如在特定波动下模拟“饮食超标”）
            tags = []
            if current_val > 10.5:
                tags = ["diet_excess"]
                print(f"⚠️ 检测到高血糖状态: {current_val}")

            # 3. 构造请求体
            payload = {
                "user_id": USER_ID,
                "user_name": USER_NAME,
                "current_glucose": current_val,
                "behavioral_tags": tags
            }

            # 4. 推送数据
            try:
                response = requests.post(API_URL, json=payload, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 推送成功: {current_val} mmol/L | AI建议: {data['content'][:20]}...")
                else:
                    print(f"❌ 推送失败: {response.status_code}")
            except Exception as e:
                print(f"📡 连接后端失败，请确保 FastAPI 正在 8002 端口运行: {e}")

            # 5. 每隔 5 秒推送一次（模拟加速的时间流）
            tick += 1
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n🛑 模拟器已停止")

if __name__ == "__main__":
    start_simulation()