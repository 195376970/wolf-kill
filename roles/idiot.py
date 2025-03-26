import os
from player import Player

class Idiot(Player):
    """白痴角色类"""
    
    def __init__(self, name, llm_client, model_name="gpt-3.5-turbo"):
        super().__init__(name, llm_client, model_name)
        self.set_role("白痴")
        self.revealed = False  # 是否已经暴露身份
    
    def night_action(self, game_state, living_players, prompt_template_path):
        """
        白痴夜晚行动 - 白痴在夜晚没有特殊行动
        但我们添加一些思考分析
        """
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        template_path = os.path.join(current_dir, prompt_template_path)
        prompt_template = self._read_file(template_path)
        
        if prompt_template:
            # 提取玩家相关信息
            public_memory = "\n".join(self.get_public_memory())
            private_memory = "\n".join(self.get_private_memory())
            
            # 生成提示，让白痴在夜晚进行思考
            prompt = prompt_template.format(
                player_name=self.name,
                role=self.role,
                game_state=game_state,
                public_memory=public_memory,
                private_memory=private_memory,
                living_players=", ".join(living_players)
            )
            
            # 请求模型回应进行思考，但不会实际执行任何行动
            thinking_response = self.llm_client.chat(prompt)
            
            # 将思考内容添加到私有记忆
            self.add_private_memory(f"夜晚思考: {thinking_response}")
        
        # 白痴没有夜晚行动，返回None
        return None
    
    def survive_lynching(self, prompt_template_path):
        """
        白痴被投票出局时展示身份，可以继续存活但失去投票权
        """
        # 如果白痴已经暴露过身份，则不能再次使用此技能
        if self.revealed:
            return False
        
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        template_path = os.path.join(current_dir, prompt_template_path)
        prompt_template = self._read_file(template_path)
        
        if prompt_template:
            # 提取玩家相关信息
            public_memory = "\n".join(self.get_public_memory())
            private_memory = "\n".join(self.get_private_memory())
            
            # 生成提示，让白痴决定是否展示身份
            prompt = prompt_template.format(
                player_name=self.name,
                role=self.role,
                public_memory=public_memory,
                private_memory=private_memory
            )
            
            # 请求模型回应决定是否展示身份
            reveal_response = self.llm_client.chat(prompt)
            
            # 检查回应中是否包含展示身份的意图
            if "展示" in reveal_response or "公开" in reveal_response or "声明" in reveal_response:
                self.revealed = True
                action_info = "被投票出局时展示了白痴身份，继续存活但失去投票权"
                self.add_private_memory(f"特殊能力: {action_info}")
                self.add_public_memory(f"{self.name} 展示了白痴身份，可以继续存活但失去投票权")
                return True
        
        # 如果未能成功执行操作，返回False
        return False
    
    def is_revealed(self):
        """返回白痴是否已经暴露身份"""
        return self.revealed
    
    def can_vote(self):
        """
        白痴暴露身份后失去投票权
        """
        return not self.revealed