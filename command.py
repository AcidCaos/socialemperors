import json

from sessions import session, save_session
from get_game_config import get_game_config, get_level_from_xp, get_name_from_item_id, get_attribute_from_mission_id, get_xp_from_level, get_attribute_from_item_id, get_item_from_subcat_functional
from constants import Constant
from engine import apply_cost, apply_collect, apply_collect_xp, timestamp_now
from op import *
from commands_old import do_command as do_old_command

commands = {
	"set_variables": cmd_set_variables
}

def get_strategy_type(id):
	if id == 8:
		return "Defensive"
	if id == 9:
		return "Mid Defensive"
	if id == 7:
		return "Mid Aggressive"
	if id == 10:
		return "Aggressive"
	return "Unknown Strategy"

def command(USERID, data):
	timestamp = data["ts"]
	first_number = data["first_number"]
	accessToken = data["accessToken"]
	tries = data["tries"]
	publishActions = data["publishActions"]
	commands = data["commands"]
    
	for i, comm in enumerate(commands):
		cmd = comm["cmd"]
		args = comm["args"]
		do_command(USERID, cmd, args)
	save_session(USERID) # Save session

def do_command(USERID, cmd, args):
	save = session(USERID)
	# print(" [+] COMMAND: ", cmd, "(", args, ") -> ", sep='', end='')

	if cmd in commands:
		commands[cmd](save, args)
		return
	else:
		# print(f" [!] UNKNOWN COMMAND: {cmd} {args}")
		do_old_command(USERID, cmd, args)