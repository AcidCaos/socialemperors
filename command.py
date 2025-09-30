import json

from sessions import session, save_session
from op import *
from commands_old import do_command as do_old_command

# command OK
def _OKOLD(cmd, args):
	print(f" [C] USING OLD: {cmd} {args}")

def _OK(cmd, args):
	print(f" [C] OK: {cmd} {args}")

def _NOTOK(cmd, args):
	print(f" [C] FAILED: {cmd} {args}")

def NOT_IMPLEMENTED(player, cmd, args):
	print(f" [C] UNKNOWN: {cmd} {args}")
	return True

def USE_OLD(player, cmd, args):
	do_old_command(player, cmd, args)
	return 2

commands = {
	"set_variables":			cmd_set_variables,
	"game_status":				cmd_game_status,

	"buy":						cmd_buy,
	"move":						cmd_move,
	"orient":					cmd_orient,
	"sell":						cmd_sell,
	"kill":						cmd_kill,
	
	"push_unit":				cmd_push_unit,
	"pop_unit":					cmd_pop_unit,
	"push_queue_unit":			cmd_push_queue_unit,
	"speed_up_queue":			cmd_speed_up_queue,
	"pop_queue_unit":			cmd_pop_queue_unit,
	"buy_powerups":				cmd_sm_powerup,			# soul mixer powerup

	"store_item":				cmd_store_item,
	"store_item_frombug":		cmd_store_item_frombug,
	"place_gift":				cmd_place_gift,
	"sell_gift":				cmd_sell_gift,
	"sell_stored_item":			cmd_sell_stored_item,
	"sell_iphone_item":			cmd_sell_stored_item,	# this should modify a different thing perhaps?

	"resurrect_hero":			cmd_resurrect_hero,
	"graveyard_buy_potions":	cmd_graveyard_buy_potions,

	"admin_add_animal":			cmd_admin_add_animal,
	"expand":					USE_OLD,
	"name_map":					USE_OLD,
	"set_strategy":				USE_OLD,

	"start_quest":				USE_OLD,
	"complete_tutorial":		USE_OLD,
	"complete_mission":			USE_OLD,
	"reward_mission":			USE_OLD,
	"add_collectable":			USE_OLD,
	"collect_new":				USE_OLD,
	"win_bonus":				USE_OLD,
	"exchange_cash_new":		USE_OLD,

	"activate_dragon":			USE_OLD,
	"desactivate_dragon":		USE_OLD,
	"next_dragon":				USE_OLD,
	"next_step":				USE_OLD,
	"buy_step_cash":			USE_OLD,

	"rider_select":				USE_OLD,
	"rider_next_step":			USE_OLD,
	"rider_buy_step_cash":		USE_OLD,

	"activate_monster":			USE_OLD,
	"desactivate_monster":		USE_OLD,
	"next_monster":				USE_OLD,
	"next_monster_step":		USE_OLD,

	"buy_monster_step_cash":	USE_OLD,
	"buy_super_offer_pack":		USE_OLD,

	"rt_level_up":				USE_OLD,
	"rt_publish_score":			USE_OLD
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
		result = commands[cmd](save, cmd, args)
		if result == 2:
			_OKOLD(cmd, args)
		elif result == True:
			_OK(cmd, args)
		else:
			_NOTOK(cmd, args)
	else:
		# print(f" [!] UNKNOWN COMMAND: {cmd} {args}")
		do_old_command(save, cmd, args)