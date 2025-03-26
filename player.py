import os

class Player:
    """玩家基类，所有角色都继承自该类"""
    
    def __init__(self, name, llm_client, model_name="gpt-3.5-turbo"):
        self.name = name
        self.role = None
        self.is_alive = True
        self.public_memory = []   # 公共记忆，用于存储游戏公开信息
        self.private_memory = []  # 私有记忆，用于存储玩家个人信息
        self.llm_client = llm_client
        self.model_name = model_name
    
    def set_role(self, role):
        """设置玩家角色"""
        self.role = role
        self.add_private_memory(f"我是{role}角色")
    
    def get_role(self):
        """获取玩家角色"""
        return self.role
    
    def is_werewolf(self):
        """判断是否为狼人阵营"""
        return "狼" in self.role
    
    def add_public_memory(self, memory):
        """添加公共记忆"""
        self.public_memory.append(memory)
    
    def add_private_memory(self, memory):
        """添加私有记忆"""
        self.private_memory.append(memory)
    
    def get_public_memory(self):
        """获取公共记忆"""
        return self.public_memory
    
    def get_private_memory(self):
        """获取私有记忆"""
        return self.private_memory
    
    def get_name(self):
        """获取玩家名称"""
        return self.name
    
    def set_alive(self, is_alive):
        """设置玩家生存状态"""
        self.is_alive = is_alive
        status = "存活" if is_alive else "死亡"
        self.add_private_memory(f"我的状态变为: {status}")
    
    def is_player_alive(self):
        """获取玩家生存状态"""
        return self.is_alive
    
    def vote(self, living_players, prompt_template_path):
        """
        白天投票选择要放逐的玩家
        """
        # 读取投票提示模板
        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(current_dir, prompt_template_path)
        prompt_template = self._read_file(template_path)
        
        if prompt_template:
            # 提取玩家相关信息
            public_memory = "\n".join(self.get_public_memory())
            private_memory = "\n".join(self.get_private_memory())
            
            # 从living_players中移除自己，只能投票给其他玩家
            vote_options = [player for player in living_players if player != self.name]
            
            # 如果没有可投票的对象，则无法进行投票
            if not vote_options:
                return None
            
            # 生成提示，让玩家决定投票
            prompt = prompt_template.format(
                player_name=self.name,
                role=self.role,
                public_memory=public_memory,
                private_memory=private_memory,
                living_players=", ".join(living_players),
                vote_options=", ".join(vote_options)
            )
            
            # 请求模型回应进行投票
            vote_response = self.llm_client.chat(prompt)
            
            # 提取投票目标
            vote_target = None
            for player in vote_options:
                if player in vote_response:
                    vote_target = player
                    break
            
            # 记录投票行为
            if vote_target:
                self.add_private_memory(f"我投票给了 {vote_target}")
                return vote_target
        
        # 如果无法进行投票，返回None
        return None
    
    def speak(self, speaking_context, prompt_template_path):
        """
        玩家发言
        """
        # 读取发言提示模板
        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(current_dir, prompt_template_path)
        prompt_template = self._read_file(template_path)
        
        if prompt_template:
            # 提取玩家相关信息
            public_memory = "\n".join(self.get_public_memory())
            private_memory = "\n".join(self.get_private_memory())
            
            # 生成提示，让玩家进行发言
            prompt = prompt_template.format(
                player_name=self.name,
                role=self.role,
                public_memory=public_memory,
                private_memory=private_memory,
                speaking_context=speaking_context
            )
            
            # 请求模型回应进行发言
            speech = self.llm_client.chat(prompt)
            
            # 记录发言内容
            self.add_private_memory(f"我的发言: {speech}")
            
            return speech
        
        # 如果无法进行发言，返回None
        return None
    
    def can_vote(self):
        """
        检查玩家是否可以投票
        某些角色可能会失去投票权
        默认情况下，所有活着的玩家都可以投票
        """
        return self.is_alive
    
    def night_action(self, game_state, living_players, prompt_template_path):
        """
        夜晚行动，由具体角色实现
        """
        # 基类不实现任何行动
        return None
    
    def _read_file(self, file_path):
        """读取文件内容的辅助方法"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"读取文件 {file_path} 时出错: {e}")
            return None