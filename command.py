import json
import logging
import traceback

from datetime import datetime
from sessions import session, save_session
from op import *

log = logging.getLogger('__main__')

# command OK
def _OK(player, cmd, args):
	name = player["playerInfo"]["name"]
	log.info(f"[C] OK: [{name}] -> {cmd} {args}")

def _NOTOK(player, cmd, args):
	name = player["playerInfo"]["name"]
	log.info(f"[C] FAILED: [{name}] -> {cmd} {args}")
	raise Exception(f"Illegal server command")

def _ERROR(player, cmd, args):
	name = player["playerInfo"]["name"]
	log.info(f"[C] CRASH: [{name}] -> {cmd} {args}")
	raise Exception(f"Illegal server command")

def NOT_IMPLEMENTED(player, cmd, args, gameversion):
	name = player["playerInfo"]["name"]
	log.info(f"[C] UNKNOWN: [{name}] -> {cmd} {args}")
	return True

def EXCEPTION(player, cmd, args, gameversion):
	raise Exception("Command exception")

commands = {
	# utils ---------------------------------------------------------------------------------------------------
	"set_variables":					cmd_set_variables,
	"fast_forward":						cmd_ff,
	"game_status":						cmd_game_status,
	"ping":								cmd_ping,
	# map item placement --------------------------------------------------------------------------------------
	"buy":								cmd_buy,
	"move":								cmd_move,
	"orient":							cmd_orient,
	"sell":								cmd_sell,
	"pop_sell":							cmd_pop_sell,
	"kill":								cmd_kill,
	# production buildings ------------------------------------------------------------------------------------
	"activate":							cmd_activate,
	"collect_new":						cmd_collect_new,
	"buy_si_help":						cmd_buy_si_help,
	"finish_si":						cmd_finish_si,
	# building queues and soul mixer --------------------------------------------------------------------------
	"push_unit":						cmd_push_unit,
	"pop_unit":							cmd_pop_unit,
	"push_queue_unit":					cmd_push_queue_unit,
	"speed_up_queue":					cmd_speed_up_queue,
	"pop_queue_unit":					cmd_pop_queue_unit,
	"unqueue_unit":						cmd_unqueue_unit,
	"buy_powerups":						cmd_sm_powerup,			# soul mixer powerup
	# item storage --------------------------------------------------------------------------------------------
	"store_item":						cmd_store_item,
	"store_item_frombug":				cmd_store_item,
	"place_gift":						cmd_place_gift,
	"place_stored_item":				cmd_place_stored_item,
	"sell_gift":						cmd_sell_gift,
	"sell_stored_item":					cmd_sell_stored_item,
	"sell_iphone_item":					NOT_IMPLEMENTED,
	# warehouse -----------------------------------------------------------------------------------------------
	"add_unit_warehouse":				cmd_add_warehoused_item,
	"place_warehoused_item":			cmd_place_warehoused_item,
	"buy_warehouse_capacity":			NOT_IMPLEMENTED,	# not used
	"buy_warehouse_capacity_single":	cmd_buy_warehouse_capacity,
	"reset_warehouse":					cmd_reset_warehouse,
	# graveyard -----------------------------------------------------------------------------------------------
	"resurrect_hero":					cmd_resurrect_hero,
	"graveyard_buy_potions":			cmd_graveyard_buy_potions,
	# spell book ----------------------------------------------------------------------------------------------
	"buy_mana_new":						cmd_buy_mana,
	"buy_magic":						cmd_buy_magic,
	"use_magic":						cmd_use_magic,
	# weather machine -----------------------------------------------------------------------------------------
	"unlock_skin":						cmd_unlock_skin,
	"set_skin":							cmd_set_skin,
	# time machine --------------------------------------------------------------------------------------------
	"buy_time_packet":					cmd_tm_buy_packet,
	"time_ff":							cmd_tm_use_packet,
	# great church --------------------------------------------------------------------------------------------
	"increase_population":				cmd_increase_population,
	# dragon nest ---------------------------------------------------------------------------------------------
	"activate_dragon":					cmd_activate_dragon,
	"desactivate_dragon":				cmd_deactivate_dragon,
	"next_dragon":						cmd_next_dragon,
	"next_step":						cmd_next_step_dragon,
	"buy_step_cash":					cmd_buy_step_dragon,
	# monster nest --------------------------------------------------------------------------------------------
	"activate_monster":					cmd_activate_monster,
	"desactivate_monster":				cmd_deactivate_monster,
	"next_monster":						cmd_next_monster,
	"next_monster_step":				cmd_next_step_monster,
	"buy_monster_step_cash":			cmd_buy_step_monster,
	# dragon riding -------------------------------------------------------------------------------------------
	"rider_select":						cmd_rider_select,
	"rider_next_step":					cmd_rider_next_step,
	"rider_buy_step_cash":				cmd_rider_buy_step,
	# player general ------------------------------------------------------------------------------------------
	"expand":							cmd_expand,
	"name_map":							cmd_name_map,
	"set_strategy":						cmd_set_strategy,
	"exchange_cash_new":				cmd_exchange_cash,
	"rt_level_up":						cmd_rt_level_up,
	"rt_publish_score":					cmd_rt_publish_score,
	"set_help_map":						cmd_set_help_map,
	"admin_add_animal":					cmd_admin_add_animal,
	# item collections ----------------------------------------------------------------------------------------
	"add_collectable":					cmd_add_collectable,
	"finish_collection":				cmd_finish_collection,
	# unit collections ----------------------------------------------------------------------------------------
	"buy_stored_item_cash":				cmd_buy_stored_item_cash,
	"unit_collections_completed":		cmd_unit_collections_completed,
	# quests, tournament --------------------------------------------------------------------------------------
	"set_attack_team":					cmd_set_attack_team,
	"start_quest":						cmd_start_quest,
	"end_quest":						cmd_end_quest,
	# pvp -----------------------------------------------------------------------------------------------------
	"buy_shield":						cmd_buy_shield,
	"reset_shield":						cmd_reset_shield,
	"get_enemy_new":					cmd_pvp_get_enemy_new,
	"begin_attack_new":					cmd_pvp_begin_attack_new,
	"end_attack":						cmd_pvp_end_attack,
	"end_attack_new":					cmd_pvp_end_attack_new,
	# market --------------------------------------------------------------------------------------------------
	"trade_resource_b":					cmd_market_trade_resource,
	# shop ----------------------------------------------------------------------------------------------------
	"buy_super_offer_pack":				cmd_buy_super_offer_pack,
	"buy_offer_pack":					NOT_IMPLEMENTED,
	# unit packs ----------------------------------------------------------------------------------------------
	"buy_unit_pack":					cmd_buy_unit_pack,
	"store_add_items":					cmd_store_add_items,
	# neighbour assist ----------------------------------------------------------------------------------------
	"assist_neighbor":					cmd_assist_neighbor,
	"assist_neighbor_new":				cmd_assist_neighbor_new,
	"clean_received_assists":			cmd_clean_received_assists,
	"assist_receive":					cmd_assist_receive,
	# old -----------------------------------------------------------------------------------------------------
	"complete_tutorial":				NOT_IMPLEMENTED,
	"complete_mission":					NOT_IMPLEMENTED,
	"reward_mission":					NOT_IMPLEMENTED,
	"win_bonus":						NOT_IMPLEMENTED,
}

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

	if cmd in commands:
		try:
			result = commands[cmd](save, cmd, args, gameversion)
		except:
			# traceback.print_exc()
			_ERROR(save, cmd, args)
			return

		if result == True:
			_OK(save, cmd, args)
		else:
			_NOTOK(save, cmd, args)
	else:
		NOT_IMPLEMENTED(save, cmd, args, gameversion)