# 导入角色类以便方便地从roles包中导入
from roles.villager import Villager
from roles.werewolf import Werewolf
from roles.witch import Witch
from roles.seer import Seer
from roles.guard import Guard
from roles.hunter import Hunter
from roles.idiot import Idiot

# 导出所有角色类
__all__ = ["Villager", "Werewolf", "Witch", "Seer", "Guard", "Hunter", "Idiot"]