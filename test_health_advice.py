import requests
import json

def test_xingjian_coach_advice():
    # 根据接口文档 image_aefede.png 修正后的完整 URL
    url = "http://127.0.0.1:8000/api/v1/chat" 
    
    # 模拟程序员针对颈椎痛的咨询请求
    payload = {
        "message": "我是一名程序员，最近由于长期久坐导致颈椎严重酸痛，请从行健教练的专业角度提供行为干预和康复建议。"
    }
    headers = {
        "Content-Type": "application/json"
    }

    print("--- [行健行为教练] 正在向 14b 模型发起处方验证 ---")
    print(f"目标地址: {url}")
    
    try:
        # 发送 POST 请求
        response = requests.post(url, json=payload, headers=headers)
        
        # 检查状态码
        if response.status_code == 200:
            result = response.json()
            print("\n✅ 验证成功！14b 模型反馈建议如下：\n")
            # 打印格式化后的 JSON 响应
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"\n❌ 请求失败，状态码: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到服务器。请确保后端 Uvicorn 服务已启动并显示 'Application startup complete'。")
    except Exception as e:
        print(f"\n❌ 发生未知错误: {e}")

if __name__ == "__main__":
    test_xingjian_coach_advice()