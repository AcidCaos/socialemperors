import json

from sessions import session, save_session
from get_game_config import get_game_config, get_level_from_xp, get_name_from_item_id, get_attribute_from_mission_id, get_xp_from_level, get_attribute_from_item_id, get_item_from_subcat_functional
from constants import Constant
from engine import *

def UNKNOWN(player, cmd, args):
	print(f" [!] UNKNOWN COMMAND: {cmd} {args}")

def cmd_nop(player, cmd, args):
	# do nothing, command not implemented
	pass

def cmd_game_status(player, cmd, args):
	print("GAME STATUS: " + " ".join(args))

def cmd_buy(player, cmd, args):
	pass

def cmd_set_variables(player, cmd, args):
	playerInfo = player["playerInfo"]
	town_id = args[7]

	_map = player["maps"][town_id]
	_map["gold"] = args[0]
	playerInfo["cash"] = args[1]
	_map["xp"] = args[2]
	_map["level"] = args[3]
	_map["stone"] = args[4]
	_map["wood"] = args[5]
	_map["food"] = args[6]