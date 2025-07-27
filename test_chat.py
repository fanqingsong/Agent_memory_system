#!/usr/bin/env python3
"""测试聊天功能"""

import asyncio
import websockets
import json
import uuid

async def test_chat():
    """测试聊天功能"""
    
    uri = "ws://localhost:8000/ws"
    
    print("=== 测试聊天功能 ===")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✓ 连接到WebSocket")
            
            # 等待欢迎消息
            welcome_msg = await websocket.recv()
            print(f"收到欢迎消息: {welcome_msg}")
            
            # 发送测试消息
            test_message = {
                "type": "message",
                "data": {
                    "content": "我是谁？",
                    "message_id": str(uuid.uuid4())
                },
                "timestamp": "2025-07-27T15:40:00.000Z"
            }
            
            print(f"发送消息: {json.dumps(test_message, ensure_ascii=False)}")
            await websocket.send(json.dumps(test_message))
            
            # 等待回复
            response = await websocket.recv()
            print(f"收到回复: {response}")
            
            # 解析回复
            response_data = json.loads(response)
            if response_data.get("success"):
                content = response_data.get("data", {}).get("content", "")
                print(f"\nAI回复: {content}")
            else:
                print(f"错误: {response_data.get('error')}")
                
    except Exception as e:
        print(f"✗ 连接失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_chat()) 