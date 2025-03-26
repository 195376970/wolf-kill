import os
from player import Player

class Witch(Player):
    """女巫角色类"""
    
    def __init__(self, name, llm_client, model_name="gpt-3.5-turbo"):
        super().__init__(name, llm_client, model_name)
        self.set_role("女巫")
        self.poison_potion = 1  # 毒药
        self.save_potion = 1    # 解药
    
    def night_action(self, game_state, living_players, prompt_template_path, victim=None):
        """
        女巫夜晚行动 - 可以选择使用解药救人或使用毒药杀人
        """
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        template_path = os.path.join(current_dir, prompt_template_path)
        prompt_template = self._read_file(template_path)
        
        if prompt_template:
            # 提取玩家相关信息
            public_memory = "\n".join(self.get_public_memory())
            private_memory = "\n".join(self.get_private_memory())
            
            # 构建女巫可用药剂信息
            potion_info = f"解药: {'可用' if self.save_potion > 0 else '已用完'}, 毒药: {'可用' if self.poison_potion > 0 else '已用完'}"
            
            # 构建被害者信息
            victim_info = f"今晚的受害者是: {victim}" if victim else "今晚没有人被狼人袭击"
            
            # 生成提示，让女巫决定是否使用药剂
            prompt = prompt_template.format(
                player_name=self.name,
                role=self.role,
                game_state=game_state,
                public_memory=public_memory,
                private_memory=private_memory,
                living_players=", ".join(living_players),
                potion_info=potion_info,
                victim_info=victim_info
            )
            
            # 请求模型回应决定使用哪种药剂
            action_response = self.llm_client.chat(prompt)
            
            # 解析女巫的行动
            action = None
            target = None
            
            # 检查是否使用解药
            if "使用解药" in action_response and self.save_potion > 0 and victim:
                self.save_potion -= 1
                action = "解药"
                target = victim
                self.add_private_memory(f"夜晚行动: 使用解药救了 {victim}")
                return ("save", victim)
            
            # 检查是否使用毒药
            elif "使用毒药" in action_response and self.poison_potion > 0:
                # 从回应中提取目标玩家
                for player in living_players:
                    # 避免毒害自己
                    if player != self.name and player in action_response:
                        self.poison_potion -= 1
                        action = "毒药"
                        target = player
                        self.add_private_memory(f"夜晚行动: 使用毒药毒死了 {player}")
                        return ("poison", player)
            
            # 如果女巫选择不使用任何药剂
            if action is None:
                self.add_private_memory("夜晚行动: 决定不使用任何药剂")
        
        # 如果未能成功执行操作，返回None
        return None