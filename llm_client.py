import os
import openai
import time
import json

class LLMClient:
    """LLM客户端，负责与OpenAI API通信"""
    
    def __init__(self, api_key=None, model_name="gpt-3.5-turbo"):
        # 优先使用传入的API密钥，否则从环境变量获取
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("未提供OpenAI API密钥，请通过参数传入或设置OPENAI_API_KEY环境变量")
        
        openai.api_key = self.api_key
        self.model_name = model_name
        self.max_retries = 3
        self.retry_delay = 2  # 重试延迟，单位秒
    
    def chat(self, prompt, temperature=0.7, max_tokens=500):
        """
        向LLM发送聊天请求
        
        Args:
            prompt (str): 输入提示
            temperature (float): 控制随机性，越高越随机
            max_tokens (int): 生成文本的最大长度
            
        Returns:
            str: LLM返回的文本响应
        """
        # 重试逻辑
        for attempt in range(self.max_retries):
            try:
                response = openai.ChatCompletion.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                print(f"API请求失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))  # 指数退避
                else:
                    print("所有重试都失败，返回默认响应")
                    return "我无法回应，请稍后再试。"
    
    def set_model(self, model_name):
        """设置使用的模型"""
        self.model_name = model_name
    
    def get_model(self):
        """获取当前使用的模型名称"""
        return self.model_name