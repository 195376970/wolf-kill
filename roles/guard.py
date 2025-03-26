import os
from player import Player

class Guard(Player):
    """守卫角色类"""
    
    def __init__(self, name, llm_client, model_name="gpt-3.5-turbo"):
        super().__init__(name, llm_client, model_name)
        self.set_role("守卫")
        self.last_protected = None  # 记录上一晚守护的玩家
    
    def night_action(self, game_state, living_players, prompt_template_path):
        """
        守卫夜晚行动 - 选择一名玩家进行守护
        """
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        template_path = os.path.join(current_dir, prompt_template_path)
        prompt_template = self._read_file(template_path)
        
        if prompt_template:
            # 提取玩家相关信息
            public_memory = "\n".join(self.get_public_memory())
            private_memory = "\n".join(self.get_private_memory())
            
            # 筛选可守护的玩家，不能连续两晚守护同一个人
            protectable_players = [player for player in living_players if player != self.last_protected]
            
            # 如果没有可守护的玩家，则无法执行守护操作
            if not protectable_players:
                self.add_private_memory("今晚没有合适的目标可以守护。")
                return None
            
            # 生成提示，让守卫选择守护目标
            prompt = prompt_template.format(
                player_name=self.name,
                role=self.role,
                game_state=game_state,
                public_memory=public_memory,
                private_memory=private_memory,
                living_players=", ".join(living_players),
                protectable_players=", ".join(protectable_players),
                last_protected=self.last_protected if self.last_protected else "无"
            )
            
            # 请求模型回应选择守护目标
            target_response = self.llm_client.chat(prompt)
            
            # 提取模型回应中的目标玩家名称
            target_player = None
            for player in protectable_players:
                if player in target_response:
                    target_player = player
                    break
            
            # 如果成功提取到目标玩家，记录守护行动
            if target_player:
                self.last_protected = target_player
                action_info = f"守护了 {target_player}"
                self.add_private_memory(f"夜晚行动: {action_info}")
                return target_player
        
        # 如果未能成功执行操作，返回None
        return None