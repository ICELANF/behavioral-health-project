import aiohttp
import asyncio
import json

# 配置你的 Dify API Key 和 Base URL
DIFY_API_KEY = 'app-DWgBYMy4FAnq1fwtWgTKyvcr' 
BASE_URL = 'http://localhost/v1'  # 因为你是本地部署 Docker，建议用这个地址

async def send_chat_message(query, user_id):
    url = f"{BASE_URL}/chat-messages"
    headers = {
        'Authorization': f'Bearer {DIFY_API_KEY}',
        'Content-Type': 'application/json'
    }
    payload = {
        "inputs": {
                "sys.query": "我是一名程序员，最近由于赶进度天天加班，脖子后面像火烧一样疼。"
            },
            "response_mode": "blocking",
            "user": "abc-123"
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=headers, json=payload) as response:
                response.raise_for_status()
                result = await response.json()
                return result
        except Exception as e:
            print(f"请求发生错误: {e}")
            return None

async def main():
    print("🚀 正在向行健系统发送首个测试消息...")
    response = await send_chat_message(
        query="我是一名程序员，最近脖子很疼，请问该怎么办？",
        user_id="tester_001"
    )
    
    if response:
        answer = response.get('answer', '')
        print(f"\n✅ 行健教练回复：\n{'-'*30}\n{answer}\n{'-'*30}")

if __name__ == "__main__":
    asyncio.run(main())