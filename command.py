import json
import logging

from datetime import datetime
from sessions import session, save_session
from op import *
from commands_old import do_command as do_old_command

def get_time():
	return datetime.fromtimestamp(timestamp_now()).strftime("%m/%d/%Y, %H:%M:%S")

# command OK
def _OKOLD(cmd, args):
	ts = get_time()
	print(f"[{ts}][C] USING OLD: {cmd} {args}")

def _OK(cmd, args):
	ts = get_time()
	print(f"[{ts}][C] OK: {cmd} {args}")

def _NOTOK(cmd, args):
	ts = get_time()
	print(f"[{ts}][C] FAILED: {cmd} {args}")
	raise Exception(f"Illegal server command")

def NOT_IMPLEMENTED(player, cmd, args, gameversion):
	ts = get_time()
	print(f"[{ts}][C] UNKNOWN: {cmd} {args}")
	return True

def USE_OLD(player, cmd, args, gameversion):
	do_old_command(player, cmd, args, gameversion)
	return 2

def EXCEPTION(player, cmd, args, gameversion):
	raise Exception(f" [C] EXCEPTION: {cmd} {args}")

commands = {
	"set_variables":					cmd_set_variables,
	"fast_forward":						cmd_ff,
	"game_status":						cmd_game_status,

	"buy":								cmd_buy,
	"move":								cmd_move,
	"orient":							cmd_orient,
	"sell":								cmd_sell,
	"kill":								cmd_kill,
	
	"push_unit":						cmd_push_unit,
	"pop_unit":							cmd_pop_unit,
	"push_queue_unit":					cmd_push_queue_unit,
	"speed_up_queue":					cmd_speed_up_queue,
	"pop_queue_unit":					cmd_pop_queue_unit,
	"unqueue_unit":						cmd_unqueue_unit,
	"buy_powerups":						cmd_sm_powerup,			# soul mixer powerup

	"store_item":						cmd_store_item,
	"store_item_frombug":				cmd_store_item_frombug,
	"place_gift":						cmd_place_gift,
	"place_stored_item":				cmd_place_gift,
	"sell_gift":						cmd_sell_gift,
	"sell_stored_item":					cmd_sell_stored_item,
	"sell_iphone_item":					cmd_sell_stored_item,	# this should modify a different thing perhaps?

	"add_unit_warehouse":				cmd_add_warehoused_item,
	"place_warehoused_item":			cmd_place_warehoused_item,
	"buy_warehouse_capacity":			NOT_IMPLEMENTED,	# not used
	"buy_warehouse_capacity_single":	cmd_buy_warehouse_capacity,
	"reset_warehouse":					cmd_reset_warehouse,

	"resurrect_hero":					cmd_resurrect_hero,
	"graveyard_buy_potions":			cmd_graveyard_buy_potions,

	"expand":							cmd_expand,
	"name_map":							cmd_name_map,
	"set_strategy":						cmd_set_strategy,
	"exchange_cash_new":				cmd_exchange_cash,
	"buy_shield":						cmd_buy_shield,
	"rt_level_up":						cmd_rt_level_up,
	"rt_publish_score":					cmd_rt_publish_score,
	"admin_add_animal":					cmd_admin_add_animal,

	"start_quest":						cmd_start_quest,
	"end_quest":						cmd_end_quest,

	"complete_tutorial":				USE_OLD,
	"complete_mission":					USE_OLD,
	"reward_mission":					USE_OLD,
	"add_collectable":					USE_OLD,
	"collect_new":						USE_OLD,
	"win_bonus":						NOT_IMPLEMENTED,

	"activate_dragon":					USE_OLD,
	"desactivate_dragon":				USE_OLD,
	"next_dragon":						USE_OLD,
	"next_step":						USE_OLD,
	"buy_step_cash":					USE_OLD,

	"rider_select":						USE_OLD,
	"rider_next_step":					USE_OLD,
	"rider_buy_step_cash":				USE_OLD,

	"activate_monster":					USE_OLD,
	"desactivate_monster":				USE_OLD,
	"next_monster":						USE_OLD,
	"next_monster_step":				USE_OLD,

	"buy_monster_step_cash":			USE_OLD,
	"buy_super_offer_pack":				USE_OLD
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

def command(USERID, data, gameversion):
	timestamp = data["ts"]
	first_number = data["first_number"]
	accessToken = data["accessToken"]
	tries = data["tries"]
	publishActions = data["publishActions"]
	commands = data["commands"]
    
	for i, comm in enumerate(commands):
		cmd = comm["cmd"]
		args = comm["args"]
		do_command(USERID, cmd, args, gameversion)
	save_session(USERID) # Save session

def do_command(USERID, cmd, args, gameversion):
	save = session(USERID)
	# print(" [+] COMMAND: ", cmd, "(", args, ") -> ", sep='', end='')

	if cmd in commands:
		result = commands[cmd](save, cmd, args, gameversion)
		if result == 2:
			_OKOLD(cmd, args)
		elif result == True:
			_OK(cmd, args)
		else:
			_NOTOK(cmd, args)
	else:
		NOT_IMPLEMENTED(save, cmd, args, gameversion)