# 狼人杀AI游戏

基于大型语言模型（LLM）实现的狼人杀游戏。游戏中的每个角色由大型语言模型提供智能决策，通过API与经典狼人杀玩法相结合，实现AI参与的游戏体验。

## 功能特点

- 支持完整的狼人杀游戏流程，包括夜晚和白天阶段
- 支持多种角色：狼人、村民、预言家、女巫
- 每个角色由AI控制，使用LLM进行决策
- 可定制的游戏配置，包括玩家数量、角色分配等
- 详细的游戏记录，支持回放和分析
- 模板化的提示系统，便于自定义AI角色的行为

## 系统要求

- Python 3.7或更高版本
- 大型语言模型API（如OpenAI API，本地模型等）

## 安装

1. 克隆项目代码

```bash
git clone https://github.com/195376970/wolf-kill.git
cd wolf-kill
```

2. 安装依赖

```bash
pip install -r requirements.txt
```

3. 配置API密钥（可选，如果使用外部LLM API）

在项目根目录创建`.env`文件并添加您的API密钥：

```
OPENAI_API_KEY=your_api_key_here
```

## 使用方法

### 基本运行

运行单场游戏：

```bash
python run_game.py
```

### 高级选项

运行多场游戏并分析结果：

```bash
python run_game.py -n 5 -a -v
```

参数说明：
- `-n, --num-games`：指定运行的游戏场数（默认为1）
- `-c, --config`：指定配置文件路径（默认为game_config.json）
- `-v, --verbose`：显示详细的游戏过程
- `-o, --output`：指定游戏记录输出目录（默认为game_records）
- `-a, --analyze`：游戏结束后分析结果

### 自定义配置

您可以通过修改`game_config.json`文件来自定义游戏配置：

```json
{
  "game_settings": {
    "players_count": 8,
    "werewolves_count": 2,
    "seer_enabled": true,
    "witch_enabled": true
  },
  "players": [
    {
      "name": "玩家1",
      "ai_model": "gpt-3.5-turbo",
      "api_key": "YOUR_API_KEY_HERE"
    },
    // 更多玩家...
  ]
}
```

## 项目结构

```
wolf-kill/
├── roles/               # 角色类定义
│   ├── werewolf.py      # 狼人类
│   ├── villager.py      # 村民类
│   ├── seer.py          # 预言家类
│   ├── witch.py         # 女巫类
│   └── __init__.py
├── prompt/              # 提示模板
│   ├── werewolf_night.txt   # 狼人夜晚行动提示
│   ├── seer_night.txt       # 预言家夜晚行动提示
│   ├── witch_save.txt       # 女巫救人提示
│   ├── witch_poison.txt     # 女巫毒人提示
│   ├── day_discussion.txt   # 白天讨论提示
│   └── day_vote.txt         # 白天投票提示
├── game_records/        # 游戏记录存储目录
├── game.py              # 游戏主类
├── player.py            # 玩家基类
├── game_recorder.py     # 游戏记录器
├── prompt_manager.py    # 提示管理器
├── llm_client.py        # LLM客户端
├── run_game.py          # 游戏运行脚本
├── game_config.json     # 游戏配置
├── requirements.txt     # 项目依赖
└── README.md            # 项目说明
```

## 自定义提示模板

您可以修改`prompt/`目录下的提示模板文件来自定义AI角色的行为。每个模板文件使用特定的占位符（如`{game_state}`, `{living_players}`等），这些占位符将在游戏运行时被替换为实际的游戏状态。

## 游戏记录与分析

游戏结果将保存在`game_records/`目录下，以JSON格式存储。您可以使用`-a`选项在游戏结束后分析结果，获取各角色的存活率、胜率等统计信息。

## HTML游戏记录功能

本项目提供了美观的HTML游戏记录功能，可以将游戏过程以更加直观的方式展示出来。

### 使用方法

1. 运行游戏时，系统将自动保存JSON格式的游戏记录和HTML格式的游戏记录。
2. JSON记录保存在`wolf-kill/game_records/`目录下。
3. HTML记录保存在`wolf-kill/game_records/html/`目录下。

### 保存路径问题

如果遇到HTML记录未生成的问题，请注意以下几点：

1. 确保游戏在`wolf-kill`目录下运行，而不是在上层目录或其他目录运行。
2. 游戏记录应该保存在`wolf-kill/game_records`目录中，而非项目根目录的`game_records`中。
3. 如果游戏中断，HTML记录可能无法生成，请尝试让游戏完整运行或使用`test_game.py`脚本生成测试记录。

### 故障排除

如果没有生成HTML记录，可以尝试以下方法：

1. 运行`test_game.py`脚本，它会创建一个简单的测试游戏记录并尝试生成HTML。
   ```
   python test_game.py
   ```
   
2. 检查`wolf-kill/game_records/html`目录是否存在，如果不存在，请手动创建：
   ```
   mkdir -p wolf-kill/game_records/html/css
   ```
   
3. 手动修复文件路径：
   - HTML记录应保存在`wolf-kill/game_records/html`目录
   - CSS文件应保存在`wolf-kill/game_records/html/css`目录

### HTML记录特点

HTML游戏记录具有以下特点：

1. 现代化设计，美观易读
2. 按天/夜分组的事件记录
3. 角色信息使用不同颜色标识（狼人红色，村民绿色，预言家紫色，女巫黄色）
4. 可点击展开查看玩家的内心活动
5. 详细展示游戏流程和每个玩家的行动

如有其他问题，请参考源代码或联系开发者。

## 贡献

欢迎提交问题和改进建议！如果您想贡献代码，请先开issue讨论您想要更改的内容。

## 许可

[MIT](LICENSE)