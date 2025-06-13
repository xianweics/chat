import json
import logging

import requests

# 设置日志模版
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


url = "http://localhost:8012/v1/chat/completions"
headers = {"Content-Type": "application/json"}


# 默认非流式输出 True or False
stream_flag = True


input_text = "你好"
# input_text = "3*4"
# input_text = "查询张三九的健康档案信息"
# input_text = "查询钱七的健康档案信息"


# 封装请求的参数
data = {
    "messages": [{"role": "user", "content": input_text}],
    "stream": stream_flag,
    "userId": "8010",
    "conversationId": "8010",
}

# 接收流式输出处理
if stream_flag:
    full_response = ""
    try:
        with requests.post(
            url, stream=True, headers=headers, data=json.dumps(data)
        ) as response:
            for line in response.iter_lines():
                if line:
                    json_str = line.decode("utf-8").strip("data: ")
                    # 检查是否为空或不合法的字符串
                    if not json_str:
                        print(f"收到空字符串，跳过...")
                        continue
                    # 确保字符串是有效的JSON格式
                    if json_str.startswith("{") and json_str.endswith("}"):
                        try:
                            data = json.loads(json_str)
                            if "delta" in data["choices"][0]:
                                delta_content = data["choices"][0]["delta"].get(
                                    "content", ""
                                )
                                full_response += delta_content
                                print(f"流式输出，响应部分是: {delta_content}")
                            if data["choices"][0].get("finish_reason") == "stop":
                                print(f"接收JSON数据结束")
                                print(f"完整响应是: {full_response}")
                        except json.JSONDecodeError as e:
                            print(f"JSON解析错误: {e}")
                    else:
                        print(f"无效JSON格式: {json_str}")
    except Exception as e:
        logger.error(f"Error occurred: {e}")

# 接收非流式输出处理
else:
    # 发送post请求
    response = requests.post(url, headers=headers, data=json.dumps(data))
    # print(f"接收到返回的响应原始内容: {response.json()}\n")
    content = response.json()["choices"][0]["message"]["content"]
    print(f"响应内容是: {content}\n")
