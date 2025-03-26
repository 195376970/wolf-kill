import os
import json
import time
import requests
from typing import Dict, List, Optional, Any, Union, Tuple
import random
import re

class LLMClient:
    """负责与大型语言模型API通信的客户端"""
    
    # 可用模型列表，按照测试响应速度排序
    AVAILABLE_MODELS = [
        "grok-2",         # 响应时间约1.35秒
        "gpt-4",          # 响应时间约1.76秒
        "claude-3-5-sonnet-20241022", # 响应时间约2.24秒
        "deepseek-v3",    # 响应时间约3.43秒
        "claude-3.5-sonnet", # 响应时间约3.78秒
        "deepseek-r1",    # 响应时间约6.82秒
        "gpt-4o",         # 响应时间约30.94秒
    ]
    
    def __init__(self, model: str = "gpt-4", api_key: Optional[str] = None, 
                 temperature: float = 0.7, max_tokens: int = 500, timeout: int = 30):
        """初始化LLM客户端
        
        Args:
            model: 使用的模型名称
            api_key: API密钥，如果为None则从环境变量获取
            temperature: 生成文本的随机性，值越高随机性越大
            max_tokens: 生成回复的最大token数
            timeout: API请求超时时间(秒)
        """
        self.model = model
        # 如果指定的模型不在可用列表中，默认使用gpt-4
        if self.model not in self.AVAILABLE_MODELS and model != "auto":
            print(f"警告: 模型 '{model}' 可能不可用。如需自动选择速度最快的模型，请使用'auto'。")
        
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "your_api_key_here")
        if not self.api_key:
            raise ValueError("未提供API密钥，请直接提供或设置OPENAI_API_KEY环境变量")
            
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.api_base = "https://api.openai.com/v1"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # 如果指定了auto，则使用最快的模型
        if model == "auto":
            self.model = self.AVAILABLE_MODELS[0]
            print(f"自动选择最快模型: {self.model}")
        
    def chat(self, prompt: str, system_message: Optional[str] = None) -> str:
        """发送聊天请求到LLM
        
        Args:
            prompt: 聊天提示文本
            system_message: 可选的系统消息，用于设置LLM行为
            
        Returns:
            str: LLM的回复文本
        """
        messages = []
        
        if system_message:
            messages.append({"role": "system", "content": system_message})
            
        messages.append({"role": "user", "content": prompt})
        
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            }
            
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"].strip()
            else:
                raise ValueError("API返回了无效的响应格式")
                
        except (requests.RequestException, ValueError) as e:
            print(f"API请求失败: {e}")
            # 尝试使用备选模型
            try:
                return self.try_alternative_model(prompt, system_message)
            except Exception as alt_e:
                print(f"备选模型也失败: {alt_e}")
                return f"API请求失败: {e}"
        except Exception as e:
            print(f"发生错误: {e}")
            # 尝试使用备选模型
            try:
                return self.try_alternative_model(prompt, system_message)
            except Exception as alt_e:
                print(f"备选模型也失败: {alt_e}")
                return f"发生错误: {e}"
    
    def try_alternative_model(self, prompt: str, system_message: Optional[str] = None) -> str:
        """尝试使用其他可用模型发送请求
        
        Args:
            prompt: 聊天提示文本
            system_message: 可选的系统消息
            
        Returns:
            str: LLM的回复文本
        """
        original_model = self.model
        
        # 尝试其他模型
        for model in self.AVAILABLE_MODELS:
            if model == original_model:
                continue
                
            print(f"尝试使用备选模型: {model}")
            self.model = model
            
            try:
                messages = []
                
                if system_message:
                    messages.append({"role": "system", "content": system_message})
                    
                messages.append({"role": "user", "content": prompt})
                
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens
                }
                
                response = requests.post(
                    f"{self.api_base}/chat/completions",
                    headers=self.headers,
                    json=payload,
                    timeout=self.timeout
                )
                
                response.raise_for_status()
                result = response.json()
                
                if "choices" in result and len(result["choices"]) > 0:
                    # 恢复原始模型
                    self.model = original_model
                    return result["choices"][0]["message"]["content"].strip()
            except:
                pass
        
        # 恢复原始模型
        self.model = original_model
        return "所有模型请求失败"
            
    def get_player_action(self, prompt: str, role: str, valid_actions: List[str]) -> str:
        """获取角色的行动
        
        Args:
            prompt: 提示内容
            role: 角色类型
            valid_actions: 有效的行动列表
            
        Returns:
            str: 行动内容
        """
        try:
            response = self.chat(prompt)
            
            # 从LLM响应中提取行动
            action = self._extract_action(response, valid_actions)
            
            if not action and valid_actions:
                # 如果无法提取有效行动，则随机选择一个
                action = random.choice(valid_actions)
                print(f"警告: {role}无法做出有效决策，随机选择: {action}")
                
            return action
        except Exception as e:
            print(f"获取{role}行动失败: {e}")
            if valid_actions:
                fallback = random.choice(valid_actions)
                print(f"使用随机行动: {fallback}")
                return fallback
            return ""
            
    def get_player_action_with_thought(self, prompt: str, role: str, valid_actions: List[str]) -> Tuple[str, str]:
        """获取角色的行动和思考过程
        
        Args:
            prompt: 提示内容
            role: 角色类型
            valid_actions: 有效的行动列表
            
        Returns:
            Tuple[str, str]: (行动内容, 思考过程)
        """
        thought_prompt = prompt + "\n\n请先详细说明你的思考过程，然后再给出最终决定。"
        
        try:
            full_response = self.chat(thought_prompt)
            
            # 从LLM响应中提取行动
            action = self._extract_action(full_response, valid_actions)
            
            if not action and valid_actions:
                # 如果无法提取有效行动，则随机选择一个
                action = random.choice(valid_actions)
                print(f"警告: {role}无法做出有效决策，随机选择: {action}")
                full_response += f"\n\n无法做出有效决策，随机选择: {action}"
                
            return action, full_response
        except Exception as e:
            print(f"获取{role}行动和思考过程失败: {e}")
            if valid_actions:
                fallback = random.choice(valid_actions)
                print(f"使用随机行动: {fallback}")
                return fallback, f"API调用出错，使用随机行动: {fallback}"
            return "", "API调用出错，无法获取行动"
        
    def get_player_speech_with_thought(self, prompt: str) -> Tuple[str, str]:
        """获取角色的发言和思考过程
        
        Args:
            prompt: 提示内容
            
        Returns:
            Tuple[str, str]: (发言内容, 思考过程)
        """
        thought_prompt = prompt + "\n\n请先详细说明你的思考过程，然后在最后给出最终发言。"
        
        try:
            full_response = self.chat(thought_prompt)
            
            # 从响应中提取最终发言
            # 首先尝试查找带有"最终发言："标记的内容
            speech_match = re.search(r"(?:最终|最后)发言[:：](.*?)(?=$|\n\n)", full_response, re.DOTALL)
            
            if speech_match:
                speech = speech_match.group(1).strip()
            else:
                # 如果没有找到标记，使用最后一段作为发言
                paragraphs = full_response.strip().split('\n\n')
                speech = paragraphs[-1].strip()
            
            # 完整响应作为思考过程
            thought = full_response
                
            return speech, thought
        except Exception as e:
            print(f"获取角色发言和思考过程失败: {e}")
            # 生成一个简单的回退发言
            fallback = "我需要更多时间思考当前的情况。"
            return fallback, f"API调用出错，使用默认发言: {fallback}"
        
    def _extract_action(self, response: str, valid_actions: List[str]) -> str:
        """从响应中提取有效行动
        
        Args:
            response: 模型响应
            valid_actions: 有效的行动列表
            
        Returns:
            str: 提取的有效行动，如果没有找到则返回空字符串
        """
        # 如果没有有效行动列表，返回整个响应
        if not valid_actions:
            return response.strip()
            
        # 提取响应的最后几段，通常决策会在最后
        paragraphs = response.strip().split('\n')
        last_paragraphs = paragraphs[-3:] if len(paragraphs) >= 3 else paragraphs
        
        # 1. 首先检查是否有明确的决策标记
        decision_patterns = [
            r"(?:最终|最后)(?:决定|决策|选择)(?:是|为)?[:：]?\s*([^,，.。\s]+)",  # 最终决定：玩家X
            r"(?:选择|决定)(?:了|是|为)?[:：]?\s*([^,，.。\s]+)",  # 选择：玩家X
            r"(?:目标|对象)(?:是|为)?[:：]?\s*([^,，.。\s]+)",     # 目标是：玩家X
            r"我(?:选择|决定)(?:猎杀|杀死|杀掉)?\s*([^,，.。\s]+)",  # 我选择猎杀玩家X
            r"(?:猎杀|杀死|杀掉)(?:目标)?(?:是|为)?\s*([^,，.。\s]+)"  # 猎杀目标是玩家X
        ]
        
        # 从末尾向前检查
        full_text = ' '.join(last_paragraphs)
        for pattern in decision_patterns:
            matches = re.findall(pattern, full_text)
            if matches:
                for match in matches:
                    # 检查匹配结果是否在有效行动中
                    for action in valid_actions:
                        if action in match or match in action:
                            return action
        
        # 2. 检查最后一段是否只包含一个有效行动
        last_paragraph = paragraphs[-1].strip()
        if last_paragraph in valid_actions:
            return last_paragraph
        
        # 3. 检查最后3段中是否包含"我会选择XX"这样的表述
        for para in reversed(last_paragraphs):
            for action in valid_actions:
                action_patterns = [
                    f"{action}$",  # 段落以行动结束
                    f"选择{action}",
                    f"决定{action}",
                    f"是{action}",
                    f"猎杀{action}",
                    f"查验{action}",
                    f"毒死{action}"
                ]
                
                for pattern in action_patterns:
                    if re.search(pattern, para):
                        return action
        
        # 4. 最后一段中是否只出现了一个有效行动
        found_actions = []
        for action in valid_actions:
            if action in last_paragraph:
                found_actions.append(action)
        
        if len(found_actions) == 1:
            return found_actions[0]
            
        # 5. 回退到全文搜索，优先找出现在句尾或独立成段的行动
        for para in reversed(paragraphs):
            for action in valid_actions:
                # 检查行动是否出现在段落末尾
                if para.strip().endswith(action):
                    return action
                    
                # 检查行动是否单独成段
                if para.strip() == action:
                    return action
                
        # 6. 如果仍然找不到，尝试传统的匹配方法作为后备
        for action in valid_actions:
            if action in response:
                return action
                
        # 如果仍然找不到，返回空字符串
        return ""
    
    def set_model(self, model: str) -> None:
        """设置使用的模型
        
        Args:
            model: 模型名称
        """
        self.model = model
        if model == "auto":
            self.model = self.AVAILABLE_MODELS[0]
            print(f"自动选择最快模型: {self.model}")
        
    def set_temperature(self, temperature: float) -> None:
        """设置生成文本的随机性
        
        Args:
            temperature: 随机性参数(0.0-1.0)
        """
        self.temperature = max(0.0, min(1.0, temperature))
        
    def set_api_key(self, api_key: str) -> None:
        """设置API密钥
        
        Args:
            api_key: 新的API密钥
        """
        self.api_key = api_key
        self.headers["Authorization"] = f"Bearer {self.api_key}"


# 使用示例
if __name__ == "__main__":
    # 从环境变量或配置获取API密钥
    api_key = os.environ.get("OPENAI_API_KEY", "your_api_key_here")
    
    # 创建LLM客户端，使用自动选择最快模型
    llm_client = LLMClient(model="auto", api_key=api_key)
    
    # 测试狼人夜晚行动
    werewolf_prompt = """
    你是狼人，需要选择一名玩家猎杀。
    当前存活玩家: 玩家1, 玩家2, 玩家3, 玩家4, 玩家5
    请选择一个目标。只回复目标名称，不要有任何解释。
    """
    
    response = llm_client.get_player_action(
        werewolf_prompt, 
        role="狼人",
        valid_actions=["玩家1", "玩家2", "玩家3", "玩家4", "玩家5"]
    )
    
    print(f"狼人选择猎杀: {response}")