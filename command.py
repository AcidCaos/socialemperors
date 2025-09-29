import json

from sessions import session, save_session
from op import *
from commands_old import do_command as do_old_command

commands = {
	"set_variables":			cmd_set_variables,
	"game_status":				cmd_game_status,
	"buy":						UNKNOWN,
	"complete_tutorial":		UNKNOWN,
	"move":						UNKNOWN,
	"collect_new":				UNKNOWN,
	"sell":						UNKNOWN,
	"kill":						UNKNOWN,
	"complete_mission":			UNKNOWN,
	"reward_mission":			UNKNOWN,
	"push_unit":				UNKNOWN,
	"pop_unit":					UNKNOWN,
	"rt_level_up":				UNKNOWN,
	"rt_publish_score":			UNKNOWN,
	"expand":					UNKNOWN,
	"name_map":					UNKNOWN,
	"exchange_cash_new":		UNKNOWN,
	"store_item":				UNKNOWN,
	"place_gift":				UNKNOWN,
	"sell_gift":				UNKNOWN,
	"activate_dragon":			UNKNOWN,
	"desactivate_dragon":		UNKNOWN,
	"next_step":				UNKNOWN,
	"next_dragon":				UNKNOWN,
	"buy_step_cash":			UNKNOWN,
	"rider_buy_step_cash":		UNKNOWN,
	"rider_next_step":			UNKNOWN,
	"rider_select":				UNKNOWN,
	"orient":					UNKNOWN,
	"buy_monster_step_cash":	UNKNOWN,
	"activate_monster":			UNKNOWN,
	"desactivate_monster":		UNKNOWN,
	"next_monster_step":		UNKNOWN,
	"next_monster":				UNKNOWN,
	"win_bonus":				UNKNOWN,
	"admin_add_animal":			UNKNOWN,
	"graveyard_buy_potions":	UNKNOWN,
	"buy_super_offer_pack":		UNKNOWN,
	"buy_super_offer_pack":		UNKNOWN,
	"set_strategy":				UNKNOWN,
	"start_quest":				UNKNOWN,
	"add_collectable":			UNKNOWN,
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
		commands[cmd](save, cmd, args)
		return
	else:
		# print(f" [!] UNKNOWN COMMAND: {cmd} {args}")
		do_old_command(save, cmd, args)