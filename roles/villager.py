import os
from player import Player

class Villager(Player):
    """村民角色类"""
    
    def __init__(self, name, llm_client, model_name="gpt-3.5-turbo"):
        super().__init__(name, llm_client, model_name)
        self.set_role("村民")
    
    def night_action(self, game_state, living_players, prompt_template_path):
        """
        村民夜晚行动 - 村民在夜晚没有特殊行动
        但我们添加一些思考分析
        """
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        template_path = os.path.join(current_dir, prompt_template_path)
        prompt_template = self._read_file(template_path)
        
        if prompt_template:
            # 提取玩家相关信息
            public_memory = "\n".join(self.get_public_memory())
            private_memory = "\n".join(self.get_private_memory())
            
            # 生成提示，让村民在夜晚进行思考
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
        
        # 村民没有夜晚行动，返回None
        return None