import os
from player import Player

class Seer(Player):
    """预言家角色类"""
    
    def __init__(self, name, llm_client, model_name="gpt-3.5-turbo"):
        super().__init__(name, llm_client, model_name)
        self.set_role("预言家")
        self.checked_players = {}  # 用于记录已经查验过的玩家及其身份
    
    def night_action(self, game_state, living_players, prompt_template_path, roles_dict=None):
        """
        预言家夜晚行动 - 查验一名玩家的身份
        """
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        template_path = os.path.join(current_dir, prompt_template_path)
        prompt_template = self._read_file(template_path)
        
        if prompt_template and roles_dict:
            # 提取玩家相关信息
            public_memory = "\n".join(self.get_public_memory())
            private_memory = "\n".join(self.get_private_memory())
            
            # 构建已查验玩家信息
            checked_info = ""
            for player, role in self.checked_players.items():
                checked_info += f"{player}: {role}\n"
            
            # 筛选未查验的活着的玩家作为可查验对象
            unchecked_players = [player for player in living_players if player != self.name and player not in self.checked_players]
            
            # 如果所有玩家都已查验，则无需进行查验
            if not unchecked_players:
                self.add_private_memory("所有玩家都已查验过，今晚无需进行查验。")
                return None
            
            # 生成提示，让预言家选择查验目标
            prompt = prompt_template.format(
                player_name=self.name,
                role=self.role,
                game_state=game_state,
                public_memory=public_memory,
                private_memory=private_memory,
                living_players=", ".join(living_players),
                checked_players=checked_info,
                unchecked_players=", ".join(unchecked_players)
            )
            
            # 请求模型回应选择查验目标
            target_response = self.llm_client.chat(prompt)
            
            # 提取模型回应中的目标玩家名称
            target_player = None
            for player in unchecked_players:
                if player in target_response:
                    target_player = player
                    break
            
            # 如果成功提取到目标玩家，进行查验并记录结果
            if target_player and target_player in roles_dict:
                # 确定目标玩家的身份类型
                target_role = roles_dict[target_player]
                is_werewolf = "狼人" if "狼" in target_role else "好人"
                
                # 记录查验结果
                self.checked_players[target_player] = is_werewolf
                action_info = f"查验了 {target_player}，发现他/她是{is_werewolf}"
                self.add_private_memory(f"夜晚查验: {action_info}")
                
                return target_player
        
        # 如果未能成功执行操作，返回None
        return None