import os
from player import Player

class Hunter(Player):
    """猎人角色类"""
    
    def __init__(self, name, llm_client, model_name="gpt-3.5-turbo"):
        super().__init__(name, llm_client, model_name)
        self.set_role("猎人")
        self.can_shoot = True  # 是否可以开枪，被女巫毒死或被狼人撕票时无法开枪
        self.is_dying = False  # 是否正在死亡
    
    def night_action(self, game_state, living_players, prompt_template_path):
        """
        猎人夜晚行动 - 猎人在夜晚没有特殊行动
        但我们添加一些思考分析
        """
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        template_path = os.path.join(current_dir, prompt_template_path)
        prompt_template = self._read_file(template_path)
        
        if prompt_template:
            # 提取玩家相关信息
            public_memory = "\n".join(self.get_public_memory())
            private_memory = "\n".join(self.get_private_memory())
            
            # 生成提示，让猎人在夜晚进行思考
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
        
        # 猎人没有夜晚行动，返回None
        return None
    
    def shoot(self, living_players, prompt_template_path):
        """
        猎人死亡时开枪带走一名玩家
        """
        # 如果不能开枪或没有正在死亡
        if not self.can_shoot or not self.is_dying:
            return None
        
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        template_path = os.path.join(current_dir, prompt_template_path)
        prompt_template = self._read_file(template_path)
        
        if prompt_template:
            # 提取玩家相关信息
            public_memory = "\n".join(self.get_public_memory())
            private_memory = "\n".join(self.get_private_memory())
            
            # 从living_players中移除自己，只能射击其他玩家
            target_options = [player for player in living_players if player != self.name]
            
            # 如果没有可射击的目标，则不能开枪
            if not target_options:
                self.add_private_memory("没有可以射击的目标。")
                return None
            
            # 生成提示，让猎人选择射击目标
            prompt = prompt_template.format(
                player_name=self.name,
                role=self.role,
                public_memory=public_memory,
                private_memory=private_memory,
                living_players=", ".join(living_players),
                target_options=", ".join(target_options)
            )
            
            # 请求模型回应选择射击目标
            target_response = self.llm_client.chat(prompt)
            
            # 提取模型回应中的目标玩家名称
            target_player = None
            for player in target_options:
                if player in target_response:
                    target_player = player
                    break
            
            # 如果成功提取到目标玩家，记录射击行动
            if target_player:
                action_info = f"死亡时射杀了 {target_player}"
                self.add_private_memory(f"射击行动: {action_info}")
                # 标记猎人已经开枪
                self.can_shoot = False
                return target_player
        
        # 如果未能成功执行操作，返回None
        return None
    
    def set_dying(self, is_dying=True):
        """设置猎人是否正在死亡状态"""
        self.is_dying = is_dying
    
    def set_can_shoot(self, can_shoot=True):
        """设置猎人是否可以开枪"""
        self.can_shoot = can_shoot