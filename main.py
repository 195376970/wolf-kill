import os
import argparse
from game import WerewolfGame

def main():
    """主程序入口"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='狼人杀游戏')
    parser.add_argument('--api-key', help='OpenAI API密钥')
    parser.add_argument('--model', default='gpt-3.5-turbo', help='使用的模型名称，默认为gpt-3.5-turbo')
    parser.add_argument('--create-templates', action='store_true', help='创建默认提示模板')
    args = parser.parse_args()
    
    # 获取API密钥（优先使用命令行参数，其次使用环境变量）
    api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("错误：未提供OpenAI API密钥，请使用--api-key参数或设置OPENAI_API_KEY环境变量")
        return
    
    try:
        # 创建游戏实例
        game = WerewolfGame(api_key, args.model)
        
        # 如果需要创建模板
        if args.create_templates:
            game.create_default_prompt_templates()
            print("已创建默认提示模板")
            return
        
        # 初始化游戏
        print("=== 狼人杀游戏初始化 ===")
        print("使用模型:", args.model)
        
        # 添加玩家
        setup_game(game)
        
        # 开始游戏
        game.start_game()
        
    except Exception as e:
        print(f"游戏运行出错: {e}")

def setup_game(game):
    """设置游戏，添加玩家和角色"""
    # 默认9人局配置
    print("\n添加玩家中...")
    
    # 添加玩家
    game.add_player("张三", "werewolf")
    game.add_player("李四", "werewolf")
    game.add_player("王五", "werewolf")
    game.add_player("赵六", "villager")
    game.add_player("钱七", "seer")
    game.add_player("孙八", "witch")
    game.add_player("周九", "hunter")
    game.add_player("吴十", "guard")
    game.add_player("郑十一", "idiot")
    
    print("已添加9名玩家:")
    for name, role in game.roles_dict.items():
        print(f"- {name}: {role}")

if __name__ == "__main__":
    main()