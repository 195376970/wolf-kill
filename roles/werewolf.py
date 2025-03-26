import os
from player import Player

class Werewolf(Player):
    """狼人角色类"""
    
    def __init__(self, name, llm_client, model_name="gpt-3.5-turbo"):
        super().__init__(name, llm_client, model_name)
        self.set_role("狼人")
    
    def night_action(self, game_state, living_players, prompt_template_path):
        """
        狼人夜晚行动 - 选择一名玩家进行袭击
        """
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        template_path = os.path.join(current_dir, prompt_template_path)
        prompt_template = self._read_file(template_path)
        
        if prompt_template:
            # 提取玩家相关信息
            public_memory = "\n".join(self.get_public_memory())
            private_memory = "\n".join(self.get_private_memory())
            
            # 从living_players中移除自己和其他狼人，只能袭击非狼人玩家
            target_options = living_players.copy()
            
            # 如果只剩下自己一个狼人且没有其他玩家，则无法执行袭击
            if len(target_options) <= 1:
                self.add_private_memory("今晚没有合适的目标可以袭击。")
                return None
            
            # 生成提示，让狼人选择袭击目标
            prompt = prompt_template.format(
                player_name=self.name,
                role=self.role,
                game_state=game_state,
                public_memory=public_memory,
                private_memory=private_memory,
                living_players=", ".join(living_players),
                target_options=", ".join(target_options)
            )
            
            # 请求模型回应选择袭击目标
            target_response = self.llm_client.chat(prompt)
            
            # 提取模型回应中的目标玩家名称
            target_player = None
            for player in target_options:
                if player in target_response and player != self.name:
                    target_player = player
                    break
            
            # 如果成功提取到目标玩家，记录行动
            if target_player:
                action_info = f"决定袭击 {target_player}"
                self.add_private_memory(f"夜晚行动: {action_info}")
                return target_player
        
        # 如果未能成功执行操作，返回None
        return None