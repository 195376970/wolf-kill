import os
import time
import random
from collections import Counter

from llm_client import LLMClient
from roles.villager import Villager
from roles.werewolf import Werewolf
from roles.witch import Witch
from roles.seer import Seer
from roles.guard import Guard
from roles.hunter import Hunter
from roles.idiot import Idiot

class WerewolfGame:
    """狼人杀游戏主类"""
    
    def __init__(self, api_key=None, model_name="gpt-3.5-turbo"):
        # 创建LLM客户端
        self.llm_client = LLMClient(api_key, model_name)
        
        # 游戏状态
        self.players = {}  # 玩家字典，键为玩家名称，值为玩家对象
        self.roles_dict = {}  # 角色字典，键为玩家名称，值为角色名称
        self.living_players = []  # 存活玩家列表
        self.day_count = 0  # 天数计数
        self.game_over = False  # 游戏是否结束
        self.winner = None  # 游戏胜利者
        
        # 提示模板路径
        self.prompt_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts")
        
        # 创建提示目录（如果不存在）
        if not os.path.exists(self.prompt_dir):
            os.makedirs(self.prompt_dir)
    
    def add_player(self, name, role):
        """
        添加玩家到游戏
        
        Args:
            name (str): 玩家名称
            role (str): 玩家角色，可以是 villager, werewolf, witch, seer, guard, hunter, idiot
        """
        # 根据角色创建对应的玩家对象
        if role.lower() == "villager":
            player = Villager(name, self.llm_client)
        elif role.lower() == "werewolf":
            player = Werewolf(name, self.llm_client)
        elif role.lower() == "witch":
            player = Witch(name, self.llm_client)
        elif role.lower() == "seer":
            player = Seer(name, self.llm_client)
        elif role.lower() == "guard":
            player = Guard(name, self.llm_client)
        elif role.lower() == "hunter":
            player = Hunter(name, self.llm_client)
        elif role.lower() == "idiot":
            player = Idiot(name, self.llm_client)
        else:
            raise ValueError(f"不支持的角色类型: {role}")
        
        # 将玩家添加到玩家字典和角色字典
        self.players[name] = player
        self.roles_dict[name] = role
        self.living_players.append(name)
        
        # 如果是狼人，告知其他狼人
        if "狼" in role:
            # 获取所有狼人
            werewolves = [p for p, r in self.roles_dict.items() if "狼" in r]
            if len(werewolves) > 1:
                for wolf in werewolves:
                    if wolf != name:
                        self.players[wolf].add_private_memory(f"{name} 也是狼人")
                        player.add_private_memory(f"{wolf} 也是狼人")
        
        return player
    
    def start_game(self):
        """开始游戏"""
        print("=== 游戏开始 ===")
        self.broadcast_message("游戏开始，天黑请闭眼...")
        
        # 游戏循环，直到游戏结束
        while not self.game_over:
            self.day_count += 1
            print(f"\n=== 第 {self.day_count} 天 ===")
            
            # 夜晚阶段
            print("\n--- 夜晚阶段 ---")
            self.night_phase()
            
            # 检查游戏是否结束
            if self.check_game_over():
                break
            
            # 白天阶段
            print("\n--- 白天阶段 ---")
            self.day_phase()
            
            # 检查游戏是否结束
            if self.check_game_over():
                break
        
        # 宣布游戏结果
        self.announce_result()
    
    def night_phase(self):
        """夜晚阶段处理"""
        # 记录夜晚信息
        night_info = f"第 {self.day_count} 天夜晚"
        self.broadcast_private_message(night_info)
        
        # 守卫行动
        protected_player = None
        guard_players = [p for p in self.living_players if isinstance(self.players[p], Guard)]
        if guard_players:
            guard_player = guard_players[0]
            guard_prompt_path = os.path.join("prompts", "guard_night_action.txt")
            protected_player = self.players[guard_player].night_action(
                night_info, 
                self.living_players, 
                guard_prompt_path
            )
            if protected_player:
                print(f"守卫保护了 {protected_player}")
        
        # 狼人行动
        wolf_players = [p for p in self.living_players if "狼" in self.roles_dict[p]]
        victim = None
        
        if wolf_players:
            # 如果有多个狼人，随机选择一个作为决策者
            wolf_leader = random.choice(wolf_players)
            wolf_prompt_path = os.path.join("prompts", "werewolf_night_action.txt")
            victim = self.players[wolf_leader].night_action(
                night_info, 
                self.living_players, 
                wolf_prompt_path
            )
            
            # 如果狼人选择了受害者，并且该玩家没有被守卫保护
            if victim and victim != protected_player:
                print(f"狼人选择袭击 {victim}")
            else:
                # 如果目标被保护或没有选择目标
                victim = None
                print("今晚没有人被狼人杀死")
        
        # 预言家行动
        seer_players = [p for p in self.living_players if isinstance(self.players[p], Seer)]
        if seer_players:
            seer_player = seer_players[0]
            seer_prompt_path = os.path.join("prompts", "seer_night_action.txt")
            checked_player = self.players[seer_player].night_action(
                night_info, 
                self.living_players, 
                seer_prompt_path,
                self.roles_dict
            )
            if checked_player:
                print(f"预言家查验了 {checked_player}")
        
        # 女巫行动
        witch_players = [p for p in self.living_players if isinstance(self.players[p], Witch)]
        if witch_players:
            witch_player = witch_players[0]
            witch_prompt_path = os.path.join("prompts", "witch_night_action.txt")
            witch_action = self.players[witch_player].night_action(
                night_info, 
                self.living_players, 
                witch_prompt_path,
                victim
            )
            
            if witch_action:
                action_type, target = witch_action
                if action_type == "save" and victim:
                    # 女巫使用解药救人
                    victim = None
                    print(f"女巫使用解药救了 {target}")
                elif action_type == "poison":
                    # 女巫使用毒药
                    if not victim:  # 如果没有狼人袭击的受害者
                        victim = target
                    else:  # 如果已有狼人袭击的受害者，则有第二个受害者
                        self.kill_player(target, "女巫毒死")
                    print(f"女巫使用毒药毒死了 {target}")
        
        # 其他玩家的夜间思考（村民，猎人，白痴等）
        for player_name in self.living_players:
            player = self.players[player_name]
            if not isinstance(player, (Werewolf, Witch, Seer, Guard)):
                # 这些角色没有特殊夜晚行动，但可以进行思考
                night_action_prompt_path = os.path.join("prompts", f"{player.get_role().lower()}_night_action.txt")
                if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), night_action_prompt_path)):
                    player.night_action(night_info, self.living_players, night_action_prompt_path)
        
        # 处理夜晚死亡
        if victim:
            # 处理猎人死亡触发技能
            hunter_victim = None
            if isinstance(self.players[victim], Hunter):
                hunter = self.players[victim]
                hunter.set_dying(True)
                hunter.set_can_shoot(True)  # 被狼人杀死可以开枪
                
                # 猎人死亡时选择射杀目标
                hunter_prompt_path = os.path.join("prompts", "hunter_shoot_action.txt")
                hunter_victim = hunter.shoot(self.living_players, hunter_prompt_path)
                
                if hunter_victim:
                    print(f"猎人在死前射杀了 {hunter_victim}")
            
            # 处理夜晚的死亡结果
            self.kill_player(victim, "狼人袭击")
            
            # 处理猎人射杀的玩家死亡
            if hunter_victim:
                self.kill_player(hunter_victim, "猎人射杀")
        
        # 天亮了，宣布夜晚结果
        if victim:
            self.broadcast_message(f"天亮了，昨晚 {victim} 被杀死了。")
        else:
            self.broadcast_message("天亮了，昨晚是平安夜，没有人死亡。")
    
    def day_phase(self):
        """白天阶段处理"""
        # 记录白天信息
        day_info = f"第 {self.day_count} 天白天"
        self.broadcast_private_message(day_info)
        
        # 所有玩家依次发言
        self.player_speak(day_info)
        
        # 投票阶段
        lynched_player = self.voting_phase()
        
        # 处理投票结果
        if lynched_player:
            # 检查是否为白痴角色，白痴被投票出局时可以展示身份继续存活
            if isinstance(self.players[lynched_player], Idiot):
                idiot = self.players[lynched_player]
                idiot_prompt_path = os.path.join("prompts", "idiot_reveal_action.txt")
                if idiot.survive_lynching(idiot_prompt_path):
                    print(f"{lynched_player} 展示了白痴身份，继续存活但失去投票权")
                    self.broadcast_message(f"{lynched_player} 是白痴，免于被处决，但失去投票权")
                    return
            
            # 处理猎人死亡触发技能
            hunter_victim = None
            if isinstance(self.players[lynched_player], Hunter):
                hunter = self.players[lynched_player]
                hunter.set_dying(True)
                hunter.set_can_shoot(True)  # 被投票处决可以开枪
                
                # 猎人死亡时选择射杀目标
                hunter_prompt_path = os.path.join("prompts", "hunter_shoot_action.txt")
                hunter_victim = hunter.shoot(self.living_players, hunter_prompt_path)
                
                if hunter_victim:
                    print(f"猎人在死前射杀了 {hunter_victim}")
            
            # 处理投票处决
            self.kill_player(lynched_player, "投票处决")
            self.broadcast_message(f"{lynched_player} 被投票处决。")
            
            # 处理猎人射杀的玩家死亡
            if hunter_victim:
                self.kill_player(hunter_victim, "猎人射杀")
                self.broadcast_message(f"猎人 {lynched_player} 在死前射杀了 {hunter_victim}。")
        else:
            self.broadcast_message("投票未达成一致，没有人被处决。")
    
    def player_speak(self, day_info):
        """玩家依次发言"""
        print("\n各位玩家开始发言：")
        for player_name in self.living_players:
            player = self.players[player_name]
            speak_prompt_path = os.path.join("prompts", "player_speak.txt")
            speech = player.speak(day_info, speak_prompt_path)
            if speech:
                print(f"\n{player_name} ({player.get_role()}) 说：{speech}")
                # 将发言广播给所有玩家
                for p in self.living_players:
                    if p != player_name:
                        self.players[p].add_public_memory(f"{player_name} 说：{speech}")
    
    def voting_phase(self):
        """投票阶段，返回被投票出局的玩家名称"""
        print("\n开始投票：")
        
        # 收集每个玩家的投票
        votes = {}
        for player_name in self.living_players:
            player = self.players[player_name]
            # 检查玩家是否有投票权
            if player.can_vote():
                vote_prompt_path = os.path.join("prompts", "player_vote.txt")
                vote = player.vote(self.living_players, vote_prompt_path)
                if vote:
                    votes[player_name] = vote
                    print(f"{player_name} 投票给 {vote}")
        
        # 统计投票结果
        vote_count = Counter(votes.values())
        
        # 找出得票最多的玩家
        if not vote_count:
            return None
        
        max_votes = max(vote_count.values())
        most_voted = [p for p, v in vote_count.items() if v == max_votes]
        
        # 如果有平票，随机选择一个（或者返回None表示无人被处决）
        if len(most_voted) > 1:
            # 在这个版本中，我们选择平票不处决任何人
            return None
        
        return most_voted[0]
    
    def kill_player(self, player_name, reason):
        """处理玩家死亡"""
        if player_name in self.living_players:
            self.players[player_name].set_alive(False)
            self.living_players.remove(player_name)
            death_message = f"{player_name} 因{reason}死亡"
            print(death_message)
            self.broadcast_private_message(death_message)
    
    def check_game_over(self):
        """检查游戏是否结束，返回是否结束的布尔值"""
        # 获取存活的狼人和好人数量
        werewolf_count = sum(1 for p in self.living_players if "狼" in self.roles_dict[p])
        villager_count = len(self.living_players) - werewolf_count
        
        # 游戏结束条件
        if werewolf_count == 0:
            self.game_over = True
            self.winner = "好人阵营"
            return True
        elif werewolf_count >= villager_count:
            self.game_over = True
            self.winner = "狼人阵营"
            return True
        
        return False
    
    def announce_result(self):
        """宣布游戏结果"""
        print("\n=== 游戏结束 ===")
        print(f"胜利者: {self.winner}")
        print("\n玩家角色:")
        for player_name, role in self.roles_dict.items():
            status = "存活" if player_name in self.living_players else "死亡"
            print(f"{player_name}: {role} ({status})")
    
    def broadcast_message(self, message):
        """广播公共消息给所有玩家"""
        for player_name in self.players:
            self.players[player_name].add_public_memory(message)
        print(message)
    
    def broadcast_private_message(self, message):
        """广播私有消息给所有玩家"""
        for player_name in self.players:
            self.players[player_name].add_private_memory(message)
    
    def create_default_prompt_templates(self):
        """创建默认的提示模板文件"""
        templates = {
            # 夜晚行动提示
            "werewolf_night_action.txt": """你是一名狼人，现在是{game_state}。请根据以下信息选择一名玩家进行袭击：

游戏公共信息：
{public_memory}

你的私有信息：
{private_memory}

当前存活的玩家: {living_players}
可选择袭击的目标: {target_options}

请选择一名玩家作为袭击目标。只需回复目标玩家的名字即可。""",
            
            "witch_night_action.txt": """你是女巫，现在是{game_state}。请根据以下信息决定是否使用药剂：

游戏公共信息：
{public_memory}

你的私有信息：
{private_memory}

当前存活的玩家: {living_players}
你的药剂情况: {potion_info}
{victim_info}

请决定：
1. 使用解药救人（如果有人被杀且你有解药）
2. 使用毒药杀人（请指明目标）
3. 不使用任何药剂

请简洁回答，直接说明你的决定。""",
            
            "seer_night_action.txt": """你是预言家，现在是{game_state}。请根据以下信息选择一名玩家进行查验：

游戏公共信息：
{public_memory}

你的私有信息：
{private_memory}

当前存活的玩家: {living_players}
你已查验的玩家及结果:
{checked_players}
未查验的玩家: {unchecked_players}

请选择一名未查验的玩家进行查验，只需回复目标玩家的名字即可。""",
            
            "guard_night_action.txt": """你是守卫，现在是{game_state}。请根据以下信息选择一名玩家进行守护：

游戏公共信息：
{public_memory}

你的私有信息：
{private_memory}

当前存活的玩家: {living_players}
可守护的玩家: {protectable_players}
上一晚守护的玩家: {last_protected}

请选择一名玩家进行守护，注意不能连续两晚守护同一名玩家。只需回复目标玩家的名字即可。""",
            
            "villager_night_action.txt": """你是村民，现在是{game_state}。虽然你在夜晚没有特殊行动，但可以思考游戏局势：

游戏公共信息：
{public_memory}

你的私有信息：
{private_memory}

当前存活的玩家: {living_players}

请分析当前局势，判断谁可能是狼人，以及明天应该如何投票。""",
            
            "hunter_night_action.txt": """你是猎人，现在是{game_state}。虽然你在夜晚没有特殊行动，但可以思考游戏局势：

游戏公共信息：
{public_memory}

你的私有信息：
{private_memory}

当前存活的玩家: {living_players}

请分析当前局势，思考如果你被杀死，应该射杀谁，以及为什么。""",
            
            "idiot_night_action.txt": """你是白痴，现在是{game_state}。虽然你在夜晚没有特殊行动，但可以思考游戏局势：

游戏公共信息：
{public_memory}

你的私有信息：
{private_memory}

当前存活的玩家: {living_players}

请分析当前局势，考虑如果明天你被投票出局，是否要揭露身份。""",
            
            # 白天行动提示
            "player_speak.txt": """你是{role}，现在是{speaking_context}。请根据以下信息进行发言：

游戏公共信息：
{public_memory}

你的私有信息：
{private_memory}

请发表一段简短的言论，表达你对游戏局势的看法，可以包括：
1. 对其他玩家的怀疑或信任
2. 对昨晚发生事件的分析
3. 对投票的建议
4. 为自己辩护（如果你被怀疑）

请像真实玩家一样思考并发言，可以适当隐藏自己的身份或误导他人。""",
            
            "player_vote.txt": """你是{role}，现在需要投票决定处决一名玩家。请根据以下信息做出决定：

游戏公共信息：
{public_memory}

你的私有信息：
{private_memory}

当前存活的玩家: {living_players}
可投票的对象: {vote_options}

请选择一名你认为应该被处决的玩家，只需回复目标玩家的名字即可。""",
            
            "hunter_shoot_action.txt": """你是猎人，现在你即将死亡，可以开枪带走一名玩家。请根据以下信息选择目标：

游戏公共信息：
{public_memory}

你的私有信息：
{private_memory}

当前存活的玩家: {living_players}
可射杀的目标: {target_options}

请选择一名你认为应该射杀的玩家，只需回复目标玩家的名字即可。尽量选择你认为是狼人的玩家。""",
            
            "idiot_reveal_action.txt": """你是白痴，现在你被投票处决。你可以选择展示身份，继续存活但失去投票权。请根据以下信息做出决定：

游戏公共信息：
{public_memory}

你的私有信息：
{private_memory}

请决定是否展示身份。回复"展示身份"或"不展示身份"。"""
        }
        
        # 创建提示模板文件
        for filename, content in templates.items():
            file_path = os.path.join(self.prompt_dir, filename)
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"已创建提示模板：{filename}")
            except Exception as e:
                print(f"创建提示模板 {filename} 失败: {e}")

# 示例用法
if __name__ == "__main__":
    # 从环境变量获取API密钥
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("请设置OPENAI_API_KEY环境变量")
        exit(1)
    
    # 创建游戏实例
    game = WerewolfGame(api_key)
    
    # 创建默认提示模板
    game.create_default_prompt_templates()
    
    # 添加玩家
    game.add_player("玩家1", "werewolf")
    game.add_player("玩家2", "werewolf")
    game.add_player("玩家3", "villager")
    game.add_player("玩家4", "seer")
    game.add_player("玩家5", "witch")
    game.add_player("玩家6", "hunter")
    game.add_player("玩家7", "villager")
    game.add_player("玩家8", "guard")
    game.add_player("玩家9", "idiot")
    
    # 开始游戏
    game.start_game()