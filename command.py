import json

from sessions import session, save_session
from op import *
from commands_old import do_command as do_old_command

# command OK
def _OK(cmd, args):
	print(f" [C] OK: {cmd} {args}")

def _NOTOK(cmd, args):
	print(f" [C] FAILED: {cmd} {args}")

def NOT_IMPLEMENTED(player, cmd, args):
	print(f" [C] UNKNOWN: {cmd} {args}")

commands = {
	"set_variables":			cmd_set_variables,
	"game_status":				cmd_game_status,

	"buy":						cmd_buy,
	"move":						cmd_move,
	"orient":					cmd_orient,
	"sell":						cmd_sell,
	"kill":						cmd_kill,

	"store_item":				cmd_store_item,
	"store_item_frombug":		cmd_store_item_frombug,
	"place_gift":				cmd_place_gift,

	"complete_tutorial":		NOT_IMPLEMENTED,
	"collect_new":				NOT_IMPLEMENTED,
	"complete_mission":			NOT_IMPLEMENTED,
	"reward_mission":			NOT_IMPLEMENTED,
	"push_unit":				NOT_IMPLEMENTED,
	"pop_unit":					NOT_IMPLEMENTED,
	"rt_level_up":				NOT_IMPLEMENTED,
	"rt_publish_score":			NOT_IMPLEMENTED,
	"expand":					NOT_IMPLEMENTED,
	"name_map":					NOT_IMPLEMENTED,
	"exchange_cash_new":		NOT_IMPLEMENTED,
	"sell_gift":				NOT_IMPLEMENTED,
	"activate_dragon":			NOT_IMPLEMENTED,
	"desactivate_dragon":		NOT_IMPLEMENTED,
	"next_step":				NOT_IMPLEMENTED,
	"next_dragon":				NOT_IMPLEMENTED,
	"buy_step_cash":			NOT_IMPLEMENTED,
	"rider_buy_step_cash":		NOT_IMPLEMENTED,
	"rider_next_step":			NOT_IMPLEMENTED,
	"rider_select":				NOT_IMPLEMENTED,
	"buy_monster_step_cash":	NOT_IMPLEMENTED,
	"activate_monster":			NOT_IMPLEMENTED,
	"desactivate_monster":		NOT_IMPLEMENTED,
	"next_monster_step":		NOT_IMPLEMENTED,
	"next_monster":				NOT_IMPLEMENTED,
	"win_bonus":				NOT_IMPLEMENTED,
	"admin_add_animal":			NOT_IMPLEMENTED,
	"graveyard_buy_potions":	NOT_IMPLEMENTED,
	"buy_super_offer_pack":		NOT_IMPLEMENTED,
	"buy_super_offer_pack":		NOT_IMPLEMENTED,
	"set_strategy":				NOT_IMPLEMENTED,
	"start_quest":				NOT_IMPLEMENTED,
	"add_collectable":			NOT_IMPLEMENTED
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
		if commands[cmd](save, cmd, args):
			_OK(cmd, args)
		else:
			_NOTOK(cmd, args)
	else:
		# print(f" [!] UNKNOWN COMMAND: {cmd} {args}")
		do_old_command(save, cmd, args)