import json
import math
import logging

log = logging.getLogger('__main__')

# grab server settings
from server_config import get_server_config
_allow_shield_bug = get_server_config()["pvp"]["shield_allow_original_bug"]
_allow_shield_stacking = get_server_config()["pvp"]["allow_shield_stacking"]

from sessions import *
from get_game_config import *
from constants import Constant
from engine import *
from event_system import hellforge_buy_all_price
from daily_bonus import claim_daily_bonus

def cmd_nop(player, cmd, args, gameversion):
	return True

def cmd_ping(player, cmd, args, gameversion):
	# id
	return True

def cmd_game_status(player, cmd, args, gameversion):
	if len(args) == 3:
		if args[0] == "MapLoaded" and args[1] == "INIT":
			if "0926" not in gameversion:
				claim_daily_bonus(player, timestamp_now())

	return True

def cmd_buy(player, cmd, args, gameversion):
	# item_id, x, y, orientation, town_id, is_free, price_multiplier, reason
	item_id = args[0]
	x = args[1]
	y = args[2]
	orientation = args[3]
	town_id = args[4]
	is_free = args[5]
	price_mult = args[6]
	reason = args[7]
	
	_map = player["maps"][town_id]

	item = get_item_from_id(item_id)
	if not item:
		return False

	if not is_free:
		if not pay_resource_type(player, _map, item["cost_type"], int(int(item["cost"]) * price_mult)):
			return False
		
	add_map_currency(_map, "xp", int(item["xp"]))
	map_add_item(_map, item_id, x, y, orientation = orientation, userid = player["playerInfo"]["pid"])

	register_bought_unit(player, item_id, town_id)

	return True

def cmd_buy_cash(player, cmd, args, gameversion):
	# item_id, x, y, orientation, town_id
	item_id = args[0]
	x = args[1]
	y = args[2]
	orientation = args[3]
	town_id = args[4]

	_map = player["maps"][town_id]

	item = get_item_from_id(item_id)
	if not item:
		return False

	cfg_globals = get_game_config()["globals"]
	if item_id not in cfg_globals["HEROES"]:
		return False

	if not pay_cash(player, int(item["cost_unit_cash"])):
		return False

	add_map_currency(_map, "xp", int(item["xp"]))
	map_add_item(_map, item_id, x, y, orientation = orientation, userid = player["playerInfo"]["pid"])
	register_bought_unit(player, item_id, town_id)

	return True

def cmd_move(player, cmd, args, gameversion):
	# x1, y1, item_id, x2, y2, orientation, town_id, reason
	# reason varies from  "Unitat", "moveTo", "colisio", "MouseUsed"
	x1 = args[0]
	y1 = args[1]
	item_id = args[2]
	x2 = args[3]
	y2 = args[4]
	orientation = args[5]
	town_id = args[6]
	reason = args[7]

	_map = player["maps"][town_id]
	map_move_item(_map, item_id, x1, y1, x2, y2, orientation = orientation)

	return True

def cmd_orient(player, cmd, args, gameversion):
	# x, y, orientation, town_id
	x = args[0]
	y = args[1]
	orientation = args[2]
	town_id = args[3]

	_map = player["maps"][town_id]
	map_orient_item(_map, x, y, orientation)

	return True

def cmd_sell(player, cmd, args, gameversion):
	# x, y, item_id, town_id, is_free, reason
	
	x = args[0]
	y = args[1]
	item_id = args[2]
	town_id = args[3]
	is_free = args[4]
	reason = args[5]

	resurrectable = False
	if reason == "KILL":
		resurrectable = True
	
	_map = player["maps"][town_id]
	item = get_item_from_id(item_id)
	if not item:
		return False
	
	if map_remove_item(_map, x, y, item_id) == 0:
		return True

	if not is_free:
		cost_type = item["cost_type"]
		if cost_type != "c":
			give_resource_type(player, _map, cost_type, int(int(item["cost"]) * SELL_DIVISOR))
	if resurrectable:
		try_push_graveyard(player, item_id)

	return True

def cmd_pop_sell(player, cmd, args, gameversion):
	# bx, by, town_id, bitem_id, uitem_id
	bx = args[0]
	by = args[1]
	town_id = args[2]
	bitem_id = args[3]
	uitem_id = args[4]

	item = get_item_from_id(uitem_id)
	if not item:
		return False

	_map = player["maps"][town_id]

	building = map_get_item(_map, bx, by, bitem_id)
	if len(building) <= 0:
		return False

	cost_type = item["cost_type"]
	if cost_type != "c":
		give_resource_type(player, _map, cost_type, int(int(item["cost"]) * SELL_DIVISOR))

	return map_pop_unit_short(_map, building[0], uitem_id)

def cmd_kill(player, cmd, args, gameversion):
	# x, y, item_id, town_id, item_type
	x = args[0]
	y = args[1]
	item_id = args[2]
	town_id = args[3]
	item_type = args[4] # b or u

	_map = player["maps"][town_id]
	map_kill_item(_map, x, y, item_id, item_type)
	
	return True

def cmd_activate(player, cmd, args, gameversion):
	# bx, by, town_id, bitem_id, toggle
	bx = args[0]
	by = args[1]
	town_id = args[2]
	bitem_id = args[3]
	toggle = args[4]

	_map = player["maps"][town_id]
	item = map_get_item(_map, bx, by, bitem_id)

	if len(item) <= 0:
		return False

	building_activate(item[0], toggle)
	return True

def cmd_collect_new(player, cmd, args, gameversion):
	# bx, by, town_id, bitem_id, num_vills, resource_multipler, cash_spent
	# bx, by, town_id, bitem_id -> for round table
	bx = args[0]
	by = args[1]
	town_id = args[2]
	bitem_id = args[3]
	if len(args) > 4:
		vills = args[4]
		res_multiplier = args[5]
		cash_spent = args[6]

		_map = player["maps"][town_id]
		item = map_get_item(_map, bx, by, bitem_id)

		if len(item) <= 0:
			return False

		if cash_spent > 0:
			if not pay_cash(player, cash_spent):
				return False

		return building_collect(player, _map, item[0], vills, res_multiplier)
	else:
		# round table
		_map = player["maps"][town_id]
		item = map_get_item(_map, bx, by, bitem_id)
		if len(item) <= 0:
			return False

		return building_collect(player, _map, item[0], 0, 0)

def cmd_buy_si_help(player, cmd, args, gameversion):
	# bx, by, town_id, bitem_id
	# bx, by, town_id, bitem_id, no_cash == 1
	bx = args[0]
	by = args[1]
	town_id = args[2]
	bitem_id = args[3]
	no_cash = False
	if len(args) > 4:
		no_cash = args[4] == 1

	_map = player["maps"][town_id]
	item = map_get_item(_map, bx, by, bitem_id)

	if len(item) <= 0:
		return False

	si_info = get_si_info(int(bitem_id))
	if not si_info:
		return False
	if not no_cash:
		if not pay_cash(player, si_info["worker_cost"]):
			return False

	push_si(item[0], "0")

	return True

def cmd_roundtable_ask_help(player, cmd, args, gameversion):
	# bx, by, town_id, bitem_id, friend_uid
	bx = args[0]
	by = args[1]
	town_id = args[2]
	bitem_id = args[3]
	friend_uid = args[4]

	_map = player["maps"][town_id]
	item = map_get_item(_map, bx, by, bitem_id)

	if len(item) <= 0:
		return False

	return roundtable_ask_help(item[0], friend_uid)

def cmd_finish_si(player, cmd, args, gameversion):
	# bx, by, town_id, bitem_id
	# bx, by, town_id, bitem_id, gold, xp, hero -> round table
	bx = args[0]
	by = args[1]
	town_id = args[2]
	bitem_id = args[3]
	gold = 0
	xp = 0
	hero = 0

	if len(args) > 4:
		gold = args[4]
		xp = args[5]
		hero = args[6]

	_map = player["maps"][town_id]
	item = map_get_item(_map, bx, by, bitem_id)

	if len(item) <= 0:
		return False

	if gold > 0:
		add_map_currency(_map, "coins", gold)
	if xp > 0:
		add_map_currency(_map, "xp", xp)
	if hero > 0:
		add_store_item(_map, hero)
		register_bought_unit(player, hero, town_id)

	finish_si(player, _map, item[0])

	return True

def cmd_finish_si_recruitment(player, cmd, args, gameversion):
	# bx, by, town_id, bitem_id, prize_id
	bx = args[0]
	by = args[1]
	town_id = args[2]
	bitem_id = args[3]
	prize_id = int(args[4])

	_map = player["maps"][town_id]
	item = map_get_item(_map, bx, by, bitem_id)

	if len(item) <= 0:
		return False

	prize = get_recruitment_prize(prize_id)
	if not prize:
		return False

	attr = item[0][7]

	num_hired = 0
	if "si" in attr:
		num_hired = len(attr["si"])

	friends_needed = prize["num_recruitments"]
	if num_hired < friends_needed:
		return False

	if _map["level"] < prize["unlock_level"]:
		return False

	rewarded = player["privateState"]["recruitmentPrices"]
	if prize_id in rewarded:
		return False

	units = prize["units"].split(",")
	for unit in units:
		add_store_item(_map, unit)

	# hired friends are capped at 4 and removed right to left (any after 4th are essentially removed)
	n = max(0, min(4, num_hired) - friends_needed)
	attr["si"] = attr["si"][:n]

	rewarded.append(prize_id)

	return True

def cmd_push_unit(player, cmd, args, gameversion):
	# ux, uy, uitem_id, bx, by, town_id
	ux = args[0]
	uy = args[1]
	uitem_id = args[2]
	bx = args[3]
	by = args[4]
	town_id = args[5]

	_map = player["maps"][town_id]
	building = map_get_item(_map, bx, by)
	unit = map_get_item(_map, ux, uy, uitem_id)
	if len(building) <= 0 or len(unit) <= 0:
		return uitem_id == 501	# map error, multiple units or buildings in same location
		# ID 501 is villager spawned by raid events
		# they don't exist in the save so we can ignore the error here

	map_push_unit(_map, unit[0], building[0])

	return True

def cmd_pop_unit(player, cmd, args, gameversion):
	# bx, by, town_id, uitem_id, ux, uy, uorientation
	bx = args[0]
	by = args[1]
	town_id = args[2]
	uitem_id = args[3]
	if len(args) > 4:
		ux = args[4]
		uy = args[5]
		uorientation = args[6]

		_map = player["maps"][town_id]
		building = map_get_item(_map, bx, by)
		if len(building) <= 0:
			return False	# map error, multiple buildings in same location
		if not map_pop_unit(_map, building[0], uitem_id, ux, uy, uorientation):
			return uitem_id == 501
			# ID 501 is villager spawned by raid events
			# they don't exist in the save so we can ignore the error here
	else:
		_map = player["maps"][town_id]
		building = map_get_item(_map, bx, by)
		if len(building) <= 0:
			return False	# map error, multiple buildings in same location
		if not map_pop_unit_short(_map, building[0], uitem_id):
			return uitem_id == 501
			# ID 501 is villager spawned by raid events
			# they don't exist in the save so we can ignore the error here

	register_bought_unit(player, uitem_id, town_id)

	return True

def cmd_push_queue_unit(player, cmd, args, gameversion):
	# bx, by, bitem_id, uitem_id, bq, not_soulmixer
	bx = args[0]
	by = args[1]
	bitem_id = args[2]
	uitem_id = args[3]
	bq = str(args[4])
	not_soulmixer = True
	if len(args) >= 5:
		not_soulmixer = args[5]

	# no support for other town IDs, sad :(
	town_id = get_default_town_id(player, gameversion)
	_map = player["maps"][town_id]

	building = map_get_item(_map, bx, by)
	if len(building) <= 0:
		return False	# map error, multiple buildings in same location

	costs = None

	if not_soulmixer:
		# charge for training costs
		item_data = get_item_from_id(uitem_id)
		cost = get_training_cost(item_data, _map)
		cost_type = item_data["cost_type"]
		
		costs = {}
		costs[cost_type] = cost
		
		cost_food = 0
		if cost_type != "f":
			cost_food = cost << 1			# x2 food
			costs["f"] = cost_food

		refund_res = pay_resource_type(player, _map, cost_type, cost)

		if not refund_res:
			# not paid, no stealing!!!!
			return False

		if not pay_resource_type(player, _map, "f", cost_food):
			if refund_res and cost_type != "c":
				# lets not steal resources for no reason
				give_resource_type(player, _map, cost_type, cost)
			return False

	if not player_push_queue_unit(player, building[0], uitem_id, bq, not not_soulmixer, costs):
		return False	# well damn

	return True

def cmd_speed_up_queue(player, cmd, args, gameversion):
	# bq
	bq = str(args[0])

	building = player_get_item_with_bq(player, bq)
	if len(building) <= 0:
		return False	# map error, multiple buildings in same location

	return player_speed_up_queue(player, building[0], bq)
	
def cmd_pop_queue_unit(player, cmd, args, gameversion):
	# bq, ux, uy, bitem_id
	bq = str(args[0])
	ux = args[1]
	uy = args[2]
	bitem_id = args[3]

	# no support for other town IDs, sad :(
	town_id = get_default_town_id(player, gameversion)
	_map = player["maps"][town_id]

	building = player_get_item_with_bq(player, bq)
	if len(building) <= 0:
		return False	# map error, multiple buildings in same location

	result = player_pop_queue_unit(player, building[0], bq)
	if not result:
		return False
	unit_id = result[0]
	is_soulmixer = result[1]

	if not is_soulmixer:
		item = get_item_from_id(unit_id)
		if not item:
			return False

		add_map_currency(_map, "xp", int(item["xp"]))

	map_add_item(_map, unit_id, ux, uy)

	register_bought_unit(player, unit_id, town_id)

	return True

def cmd_unqueue_unit(player, cmd, args, gameversion):
	# bq, bitem_id
	bq = str(args[0])
	bitem_id = args[1]

	# no support for other town IDs, sad :(
	town_id = get_default_town_id(player, gameversion)
	_map = player["maps"][town_id]

	building = player_get_item_with_bq(player, bq)
	if len(building) <= 0:
		return False	# map error, multiple buildings in same location

	# result is None if fail or unit_id that was unqueued
	unit_id, costs = player_unqueue_unit(player, building[0], bq)
	if not unit_id:
		return False

	# refund
	if not costs:
		item_data = get_item_from_id(unit_id)
		cost = get_training_cost(item_data, _map)
		cost_type = item_data["cost_type"]
		cost_food = cost << 1			# x2 food

		give_resource_type(player, _map, cost_type, cost)
		give_resource_type(player, _map, "f", cost_food)
	else:
		for cost_type in costs:
			give_resource_type(player, _map, cost_type, costs[cost_type])

	return True

def cmd_sm_powerup(player, cmd, args, gameversion):
	# powerup_idx
	powerup_idx = int(args[0])

	powerup = get_game_config()["globals"]["SOUL_MIXER_POWERUPS_LEVELS"][powerup_idx]
	if not pay_cash(player, powerup["cash_cost"]):
		return False

	return True

def cmd_store_item(player, cmd, args, gameversion):
	# x, y, town_id, item_id
	x = args[0]
	y = args[1]
	town_id = args[2]
	item_id = args[3]

	_map = player["maps"][town_id]

	if map_remove_item(_map, x, y, item_id) == 0:
		return False

	add_store_item(_map, item_id, 1)

	return True

def cmd_place_gift(player, cmd, args, gameversion):
	# item_id, x, y, orientation, town_id
	item_id = args[0]
	x = args[1]
	y = args[2]
	orientation = args[3]
	town_id = args[4]

	_map = player["maps"][town_id]

	item = get_item_from_id(item_id)
	if not item:
		return False
	add_map_currency(_map, "xp", int(item["xp"]))

	map_add_item(_map, item_id, x, y, orientation = orientation, userid = player["playerInfo"]["pid"])
	remove_gift_item(player, item_id, 1)

	register_bought_unit(player, item_id, town_id)

	return True

def cmd_sell_gift(player, cmd, args, gameversion):
	# item_id, town_id
	item_id	= args[0]
	town_id = args[1]
	
	_map = player["maps"][town_id]
	item = get_item_from_id(item_id)

	if not item:
		return False

	cost_type = item["cost_type"]
	if cost_type != "c":
		give_resource_type(player, _map, cost_type, int(int(item["cost"]) * SELL_DIVISOR))

	remove_gift_item(player, item_id, 1)

	return True

def cmd_place_stored_item(player, cmd, args, gameversion):
	# item_id, x, y, orientation, town_id
	item_id = args[0]
	x = args[1]
	y = args[2]
	orientation = args[3]
	town_id = args[4]

	_map = player["maps"][town_id]

	map_add_item(_map, item_id, x, y, orientation = orientation, userid = player["playerInfo"]["pid"])
	remove_store_item(_map, item_id, 1)

	register_bought_unit(player, item_id, town_id)

	return True

def cmd_sell_stored_item(player, cmd, args, gameversion):
	# item_id, town_id
	item_id	= args[0]
	town_id = args[1]
	
	_map = player["maps"][town_id]
	item = get_item_from_id(item_id)

	if not item:
		return False

	cost_type = item["cost_type"]
	if cost_type != "c":
		give_resource_type(player, _map, cost_type, int(int(item["cost"]) * SELL_DIVISOR))

	remove_store_item(_map, item_id, 1)

	return True

def cmd_tm_buy_packet(player, cmd, args, gameversion):
	# packet_id
	packet_id = int(args[0])
	packet = get_time_machine_packet(packet_id)

	if not packet:
		return False

	cost = packet["price"]
	if not pay_cash(player, cost):
		return False

	player["privateState"]["countTimePacket"][packet_id] += 1

	return True

def cmd_tm_use_packet(player, cmd, args, gameversion):
	# packet_id
	packet_id = int(args[0])
	packet = get_time_machine_packet(packet_id)

	if not packet:
		return False

	packets = player["privateState"]["countTimePacket"]
	if packets[packet_id] <= 0:
		return False

	packets[packet_id] -= 1

	player_fast_forward(player, int(packet["hours"] * 3600), True)

	return True

def cmd_graveyard_buy_potions(player, cmd, args, gameversion):
	potion_data = get_game_config()["globals"]["GRAVEYARD_POTIONS"]
	potion_amount = int(potion_data["amount"])
	price = int(potion_data["price"]["c"])

	if pay_cash(player, price):
		add_potions(player, potion_amount)
		return True

	return False
	
def cmd_graveyard_reset_potions_received(player, cmd, args, gameversion):
	player["privateState"]["potionsReceived"] = 0

	return True

def cmd_resurrect_hero(player, cmd, args, gameversion):
	# item_id, x, y, town_id, used_potion -> graveyard
	# item_id, x, y, town_id -> heroes grave
	item_id = args[0]
	x = args[1]
	y = args[2]
	town_id = args[3]
		
	_map = player["maps"][town_id]

	item = get_item_from_id(item_id)
	if not item:
		return False

	if len(args) > 4:
		# graveyard
		used_potion = args[4]

		if not in_graveyard(player, item_id):
			return False

		if used_potion:
			potion_price = item["potion"]
			if not potion_price:
				return False
			if not pay_potions(player, potion_price):
				return False

			graveyard_remove(player, item_id)
		else:
			# charge for training costs
			item_data = get_item_from_id(item_id)
			cost = int(round(get_training_cost(item_data, _map, False) * RESURRECT_MULTIPLIER_GRAVEYARD))
			cost_type = item_data["cost_type"]
		
			cost_food = 0
			if cost_type != "f":
				cost_food = cost << 1			# x2 food

			refund_res = pay_resource_type(player, _map, cost_type, cost)

			if not refund_res:
				# not paid, no stealing!!!!
				return False

			if not pay_resource_type(player, _map, "f", cost_food):
				if refund_res and cost_type != "c":
					# lets not steal resources for no reason
					give_resource_type(player, _map, cost_type, cost)
				return False

			graveyard_remove(player, item_id)
	else:
		# heroes grave
		if not in_heroes_grave(player, item_id):
			return False

		gold_price = int(int(item["cost_unit_cash"]) * RESURRECT_MULTIPLIER)
		if not pay_map_currency(_map, "coins", gold_price):
			return False

		graveyard_remove_hero(player, item_id)

	map_add_item(_map, item_id, x, y)
	
	register_bought_unit(player, item_id, town_id)

	return True

def cmd_buy_mana(player, cmd, args, gameversion):
	# town_id, use_cash
	town_id = args[0]
	use_cash = args[1] == 1
	_map = player["maps"][town_id]

	cfg_globals = get_game_config()["globals"]

	if use_cash:
		if not pay_cash(player, cfg_globals["COST_MANA_CASH"]):
			return False
	else:
		if not pay_map_currency(_map, "coins", cfg_globals["COST_MANA_GOLD"]):
			return False

	add_mana(player, cfg_globals["MANA_PER_PURCHASE"])

	return True

def cmd_buy_magic(player, cmd, args, gameversion):
	# spell_id, town_id, use_cash
	spell_id = args[0]
	town_id = args[1]
	use_cash = args[2] == 1

	learned = player["privateState"]["magics"]
	if str(spell_id) in learned:
		return False

	spell = get_spell(spell_id)
	if not spell:
		return False

	_map = player["maps"][town_id]
	if use_cash:
		if not pay_cash(player, spell["cash"]):
			return False
	else:
		if not pay_map_currency(_map, "coins", spell["gold"]):
			return False

	learned[str(spell_id)] = 0
	add_mana(player, spell["mana"])

	return True

def cmd_use_magic(player, cmd, args, gameversion):
	# spell_id
	spell_id = args[0]

	learned = player["privateState"]["magics"]
	if str(spell_id) not in learned:
		return False

	spell = get_spell(spell_id)
	if not spell:
		return False

	if not pay_mana(player, spell["mana"]):
		return False

	learned[str(spell_id)] += 1

	return True

def cmd_add_warehoused_item(player, cmd, args, gameversion):
	# ux, uy, town_id, uitem_id
	ux = args[0]
	uy = args[1]
	town_id = args[2]
	uitem_id = args[3]

	_map = player["maps"][town_id]

	items = map_get_item(_map, ux, uy, uitem_id)
	if len(items) <= 0:	# teleporting units are broken
		items = map_get_items_of_id(_map, uitem_id)
	if len(items) <= 0:
		return uitem_id == 501
		# ID 501 is villager spawned by raid events
		# they don't exist in the save so we can ignore the error here
	
	warehouse_add(_map, items[0])

	return True

def cmd_place_warehoused_item(player, cmd, args, gameversion):
	# uitem_id, ux, uy, 0, town_id
	uitem_id = args[0]
	ux = args[1]
	uy = args[2]
	zero = args[3]	# always 0
	town_id = args[4]

	_map = player["maps"][town_id]

	if not warehouse_remove(_map, uitem_id):
		return uitem_id == 501
		# ID 501 is villager spawned by raid events
		# they don't exist in the save so we can ignore the error here

	map_add_item(_map, uitem_id, ux, uy)

	register_bought_unit(player, uitem_id, town_id)

	return True

def cmd_buy_warehouse_capacity(player, cmd, args, gameversion):
	# town_id
	town_id = args[0]

	_map = player["maps"][town_id]

	cfg_globals = get_game_config()["globals"]
	cost = cfg_globals["WAREHOUSE_CAPACITY_INCREASE_PRICE_SINGLE"]
	cap = cfg_globals["WAREHOUSE_MAX_CAPACITY"]

	# can't go over the cap
	if _map["warehouseAditionalCapacitySingle"] >= cap:
		return False
	if not pay_cash(player, cost):
		return False

	_map["warehouseAditionalCapacitySingle"] = min(cap, _map["warehouseAditionalCapacitySingle"] + 1)

	return True

def cmd_reset_warehouse(player, cmd, args, gameversion):
	# town_id
	town_id = args[0]

	_map = player["maps"][town_id]
	warehouse_reset(_map)

	return True

def cmd_name_map(player, cmd, args, gameversion):
	# town_id, name
	town_id = args[0]
	name = str(args[1])

	player["playerInfo"]["map_names"][town_id] = name
	# player["playerInfo"]["name"] = name # allow renaming of profile too

	return True

def cmd_unlock_skin(player, cmd, args, gameversion):
	# skin_id
	skin_id = str(args[0])

	privateState = player["privateState"]
	if skin_id not in privateState["unlockedSkins"] and skin_id != "0":
		skin_cost = get_game_config()["globals"]["COST_UNLOCK_SKIN"]
		if not pay_cash(player, skin_cost):
			return False

	privateState["unlockedSkins"][skin_id] = True

	return True

def cmd_set_skin(player, cmd, args, gameversion):
	# town_id, skin_id
	town_id = args[0]
	skin_id = str(args[1])

	privateState = player["privateState"]
	if skin_id not in privateState["unlockedSkins"] and skin_id != "0":
		return False

	_map = player["maps"][town_id]
	_map["skin"] = skin_id

	return True

def cmd_set_strategy(player, cmd, args, gameversion):
	# strategy
	strategy = args[0]

	save["privateState"]["strategy"] = strategy

	return True

def cmd_exchange_cash(player, cmd, args, gameversion):
	town_id = args[0]

	cfg_globals = get_game_config()["globals"]
	cash_amount = cfg_globals["EXCHANGE_CASH"]
	gold_amount = cfg_globals["EXCHANGE_GOLD"]

	_map = player["maps"][town_id]
	if not pay_cash(player, cash_amount):
		return False

	add_map_currency(_map, "coins", gold_amount)

	return True

def cmd_expand(player, cmd, args, gameversion):
	# land_idx, currency_type, town_id
	land_idx = args[0]
	currency_type = args[1]
	town_id = args[2]

	_map = player["maps"][town_id]
	expansions = _map["expansions"]
	if land_idx in expansions:
		return False

	prices = get_game_config()["expansion_prices"]
	price = prices[len(expansions) - 1]

	if currency_type == "cash":
		if not pay_cash(player, price["cash"]):
			return False
	elif currency_type == "gold":
		if not pay_map_currency(_map, "coins", price["coins"]):
			return False
	else:
		return False

	expansions.append(land_idx)
	return True

def cmd_rt_level_up(player, cmd, args, gameversion):
	# level_now
	level_now = int(args[0])

	# no support for other town IDs, sad :(
	town_id = get_default_town_id(player, gameversion)
	_map = player["maps"][town_id]
	level_old = _map["level"]

	gained = max(0, level_now - level_old)

	levels = get_game_config()["levels"]
	level_data = levels[level_now - 1]

	give_levelup_reward(player, _map, level_data)

	_map["level"] = level_now

	# add mana
	cfg_globals = get_game_config()["globals"]
	if level_now >= cfg_globals["START_LEVEL_MANA_REWARD"]:
		add_mana(player, cfg_globals["MANA_REWARD_PER_LEVEL"])

	pvp_pool_modify(player)

	return True

def cmd_rt_publish_score(player, cmd, args, gameversion):
	# xp_now 
	xp_now = int(args[0])

	# no support for other town IDs, sad :(
	town_id = get_default_town_id(player, gameversion)
	_map = player["maps"][town_id]

	_map["xp"] = xp_now

	pvp_pool_modify(player)

	return True

def cmd_rt_publish_achievement_unit(player, cmd, args, gameversion):
	# unit_id
	unit_id = int(args[0])

	achieved = player["privateState"]["achievedUnits"]
	if unit_id in achieved:
		return True

	achieved.append(unit_id)

	return True

def cmd_set_attack_team(player, cmd, args, gameversion):
	# team_name, team_units, formation
	team_name = args[0]
	team_units = args[1]
	formation = None
	if len(args) >= 2:
		formation = args[2]

	privateState = player["privateState"]
	privateState["teams"][team_name] = json.loads(team_units)
	if formation:
		privateState["tournamentFormation"] = formation

	return True

def cmd_start_quest(player, cmd, args, gameversion):
	# quest_id, town_id
	quest_id = args[0]
	town_id = args[1]

	ts_now = timestamp_now()
	_map = player["maps"][town_id]

	if not is_forge_quest(quest_id):
		_map["questTimes"][str(quest_id)] = ts_now

	return True

def cmd_start_quest_new(player, cmd, args, gameversion):
	# no support for other town IDs, sad :(
	town_id = get_default_town_id(player, gameversion)
	_map = player["maps"][town_id]

	_map["lastQuestTimes"].append(timestamp_now())

	return True

def cmd_end_quest(player, cmd, args, gameversion):
	# json
	data = json.loads(args[0])
	#log.info(json.dumps(data, indent='\t'))

	privateState = player["privateState"]

	units = data["units"]
	quest_id = data["quest_id"]
	next_index = None
	set_unlocked_index = False
	forge_quest = is_forge_quest(quest_id)
	if "set_unlocked_index" in data:
		set_unlocked_index = data["set_unlocked_index"] == 1
	if not forge_quest:
		next_index = get_quest_index(quest_id) + 1

	win = False
	if "win" in data:
		win = data["win"] == 1
	elif "voluntary_end" in data:
		win = data["voluntary_end"] == 0

	resources = data["resources"]
	difficulty = data["difficulty"]
	town_id = data["map"]

	_map = player["maps"][town_id]

	cfg_globals = get_game_config()["globals"]
	if win:
		#if set_unlocked_index == 1:
		# if we won then unlock next quest
		if not forge_quest:
			old_index = privateState["unlockedQuestIndex"]
			if old_index == None:
				old_index = -1
			if next_index - old_index <= 1:
				privateState["unlockedQuestIndex"] = max(next_index, old_index)

		# if we won, also set quest rank and add honor points
		rank = privateState["questsRank"][str(quest_id)]
		honor_points = 0
		if rank == None:
			rank = 0
		if difficulty > rank:
			honor_points = cfg_globals["HONOR_POINT_QUEST_FIRST_TIME"][difficulty - 1]
		else:
			honor_points = cfg_globals["HONOR_POINT_QUEST"][difficulty - 1]
			
		privateState["questsRank"][str(quest_id)] = max(difficulty, rank)
		player["playerInfo"]["honor_points"] += honor_points
	else:
		player["playerInfo"]["honor_points"] += cfg_globals["HONOR_POINT_QUEST_LOSE"]

	# give player gold and xp
	add_map_currency(_map, "coins", resources["g"])
	add_map_currency(_map, "xp", resources["x"])

	# remove lost units and send them to graveyard
	handle_unit_loss(player, _map, units)

	return True

def cmd_reset_shield(player, cmd, args, gameversion):
	# disables player shield without resetting cooldown
	privateState = player["privateState"]
	privateState["shieldEndTime"] = 0

	pvp_pool_modify(player)

	return True

def cmd_buy_shield(player, cmd, args, gameversion):
	# shield_id
	shield_id = args[0]

	# no support for other town IDs, sad :(
	town_id = get_default_town_id(player, gameversion)
	_map = player["maps"][town_id]
	privateState = player["privateState"]

	shield = get_shield_data(shield_id)
	if not shield:
		return False

	bought = privateState["purchasedShields"]
	if shield_id in bought:
		return False

	price = shield["price"]
	price_type = shield["price_type"]
	if price_type == "c":
		if not pay_cash(player, shield["price"]):
			return False
	else:
		return False

	# SP SERVER BUG ---------------------------------------------------------------------------------------------
	# So back in the day, SP had a bug where if you bought a shield
	# Went to visit a friend's empire and came back to your own empire
	# you permanently gained the same amount of cash spent on the shields, basically -10 cash but gain +20 cash
	# This bug was NEVER fixed so I will leave this as a feature for anyone
	# who wishes to get themselves free 80 cash every day
	# for 80 cash every day, buy all 3 shields right to left then next day repeat it

	# Yes this was an actual bug, I am not making this up
	# Go dig up old facebook comments on the official SE page and you'll find someone
	# talking about this!
	if _allow_shield_bug:
		player["playerInfo"]["cash"] += int(shield["price"]) << 1

	# This implementation however doesn't require you to do the step of visiting your friend's empire
	# -----------------------------------------------------------------------------------------------------------

	shield_duration = shield["protection_time"]
	shield_cooldown = shield["cooldown"]

	bought.append(shield_id)
	
	end_time = privateState["shieldEndTime"]
	cooldown = privateState["shieldCooldown"]

	ts_now = timestamp_now()

	if not _allow_shield_stacking:
		if cooldown < ts_now and len(bought) == 1:
			# no shield time stacking allowed
			end_time = 0

	if ts_now >= end_time:
		end_time = ts_now + shield_duration
	else:
		end_time += shield_duration
	privateState["shieldEndTime"] = end_time

	# If you buy shields right to left, you can get 1d cooldown on all
	# I don't care, this feature was broken to begin with so it will work like this
	privateState["shieldCooldown"] = ts_now + shield_cooldown

	pvp_pool_modify(player)
	
	return True

def cmd_pvp_get_enemy_new(player, cmd, args, gameversion):
	# cost, searches_before_attack
	cost = args[0]
	searches = args[1]

	# no support for other town IDs, sad :(
	town_id = get_default_town_id(player, gameversion)
	_map = player["maps"][town_id]

	if not pay_map_currency(_map, "coins", cost):
		return False

	return True

def cmd_pvp_begin_attack_new(player, cmd, args, gameversion):
	# timestamp
	ts = args[0]

	return True

def cmd_pvp_end_attack_new(player, cmd, args, gameversion):
	# g, f, w, s, eid, uid, ulevel, ts, winner_id, voluntary_end, attack_is_reply, dmg > shield% limit, damage_pct, xp 
	gold = args[0]
	food = args[1]
	wood = args[2]
	stone = args[3]
	enemy_id = args[4]
	user_id = args[5]	# game sends the wrong thing here
	user_level = args[6]
	ts = args[7]
	winner_id = args[8]
	voluntary_end = args[9]
	attack_is_reply = args[10] # revenge flag or what?
	damage_is_over_shield_percentage = args[11] # damage (0-100) over some shield%
	damage_pct = args[12] # (0-100) how much damage was done
	xp = args[13]

	#if player["playerInfo"]["pid"] != user_id:
	#	# what are you doing!?
	#	return False

	# no support for other town IDs, sad :(
	town_id = get_default_town_id(player, gameversion)
	_map = player["maps"][town_id]

	add_map_currency(_map, "coins", gold)
	add_map_currency(_map, "food", food)
	add_map_currency(_map, "wood", wood)
	add_map_currency(_map, "stone", stone)
	add_map_currency(_map, "xp", xp)

	pvp_pool_modify(player)

	return True

def cmd_pvp_end_attack(player, cmd, args, gameversion):
	# data
	data = json.loads(args[0])
	
	# data.townhall_gold -> int
	# data.duration -> int
	# data.attacker_units -> array [ id, entered, died, recovered ]
	# data.attacker -> dict
	#	race
	#	level
	#	world_id
	#	name
	#	map -> town_id
	#	user_id -> player user id
	# data.victim -> dict
	#	pic -> image url
	#	unitsToHide -> { index, life }
	#	map -> town_id
	#	level
	#	resources -> { s, f, g, w, wood, gold, stone, food }
	#	name
	#	race
	#	user_id -> enemy user id
	# resources -> { x, s, f, w, g } -> the gained stuff
	# resources_victim -> { g } -> idk?
	# honor -> int -> honor gained
	# voluntary_end -> int
	# victim_units -> array [ id, entered, died, recovered ] -> do not use 
	# win -> int -> did user win against enemy win?

	town_id = data["attacker"]["map"]
	_map = player["maps"][town_id]

	#if player["playerInfo"]["pid"] != data["attacker"]["user_id"]:
	#	# what are you doing!?
	#	return False

	add_map_currency(_map, "coins", data["resources"]["g"])
	add_map_currency(_map, "food", data["resources"]["f"])
	add_map_currency(_map, "wood", data["resources"]["w"])
	add_map_currency(_map, "stone", data["resources"]["s"])
	add_map_currency(_map, "xp", data["resources"]["x"])

	# remove lost units and send them to graveyard
	handle_unit_loss(player, _map, data["attacker_units"])

	pvp_pool_modify(player)

	return True

def cmd_buy_super_offer_pack(player, cmd, args, gameversion):
	# town_id, pack_id, items, cost
	town_id = args[0]
	pack_id = args[1]
	items = args[2]
	cost = args[3]

	items = items.split(",")
	pack = get_offer_pack_id(pack_id)

	if not pack:
		return False
	if pack["enabled"] == 0:
		return False

	for item_id in items:
		_id = int(item_id)
		found = False
		for thing in pack["items"]:
			if type(thing) == list:
				if _id in thing:
					found = True
					break
			elif _id == thing:
				found = True
				break

		if not found:
			return False

	if not pay_cash(player, cost):
		return False

	_map = player["maps"][town_id]

	add_map_currency(_map, "coins", pack["gold"])
	add_map_currency(_map, "food", pack["food"])
	add_map_currency(_map, "wood", pack["wood"])
	add_map_currency(_map, "stone", pack["stone"])
	add_map_currency(_map, "xp", pack["xp"])
	add_mana(player, pack["mana"])

	for item_id in items:
		add_store_item(_map, item_id)
		register_bought_unit(player, item_id, town_id)

	return True

def cmd_buy_offer_pack(player, cmd, args, gameversion):
	# town_id, pack_id
	# town_id, pack_id, winning_id
	town_id = args[0]
	pack_id = args[1]
	is_gacha = len(args) > 2
	if is_gacha:
		winning_id = args[2]

	pack = get_offer_pack_id(pack_id)

	if not pack:
		return False
	if pack["enabled"] == 0:
		return False

	_map = player["maps"][town_id]

	if is_gacha:
		found = False
		for entry in pack["items"]:
			if entry[0] == winning_id:
				found = True

		if not found:
			return False

		if not pay_cash(player, pack["cost_cash"]):
			return False

		add_store_item(_map, winning_id)
		register_bought_unit(player, winning_id, town_id)
	else:
		if not pay_cash(player, pack["cost_cash"]):
			return False

		for item_id in pack["items"]:
			add_store_item(_map, item_id)
			register_bought_unit(player, item_id, town_id)

	add_map_currency(_map, "coins", pack["gold"])
	add_map_currency(_map, "food", pack["food"])
	add_map_currency(_map, "wood", pack["wood"])
	add_map_currency(_map, "stone", pack["stone"])
	add_map_currency(_map, "xp", pack["xp"])
	add_mana(player, pack["mana"])

	return True

def cmd_buy_unit_pack(player, cmd, args, gameversion):
	# pack_id, n
	pack_id = int(args[0])
	n = int(args[1])


	userid = player["playerInfo"]["pid"]
	pack_state = get_unit_pack_state(userid)

	if pack_state:
		# stop, we already have a state
		return True

	# no support for other town IDs, sad :(
	town_id = get_default_town_id(player, gameversion)
	_map = player["maps"][town_id]

	# if n is between >= 2 and < 8, apply 10% discount (* 0.9)
	# if n is between >= 8, apply 15% discount (* 0.85)
	cost = 0
	cost_type = None
	pack = get_unit_pack(pack_id)
	
	if not pack:
		return False
	if pack["in_store"] == 0:
		return False

	# check if we can even buy it
	max_packs = pack["max_purchable"]
	packs_bought = player["privateState"]["unitPacks"]
	if max_packs != 0:
		if str(pack_id) in packs_bought:
			if packs_bought[str(pack_id)] + n > max_packs:
				return True

	if str(pack_id) not in packs_bought:
		packs_bought[str(pack_id)] = n
	else:
		packs_bought[str(pack_id)] += n

	discount = 1.0
	
	if n >= 8:
		discount = 0.85
	elif n >= 2:
		discount = 0.9

	price = pack["price"]
	if "c" in price:
		cost = int(math.ceil(int(price["c"]) * n * discount))
		if not pay_cash(player, cost):
			return False
	elif "g" in price:
		cost = int(math.ceil(int(price["g"]) * n * discount))
		if not pay_map_currency(_map, "coins", cost):
			return False
	else:
		return False

	# set state
	set_unit_pack_state(userid, get_unit_pack_randoms(n))

	return True

def cmd_store_add_items(player, cmd, args, gameversion):
	# items
	items = json.loads(args[0])

	# no support for other town IDs, sad :(
	town_id = get_default_town_id(player, gameversion)
	_map = player["maps"][town_id]

	for item_id in items:
		add_store_item(_map, item_id)
		register_bought_unit(player, item_id, town_id)
	
	return True

def cmd_add_collectable(player, cmd, args, gameversion):
	# collection_id, index
	collection_id = args[0]
	index = args[1]

	if collection_id <= 0:
		return False
	if index < 1 or index > 6:
		return False

	collections = player["privateState"]["collections"]
	collections[collection_id][index] += 1

	return True

def cmd_finish_collection(player, cmd, args, gameversion):
	# collection_id - if free
	# collection_id, used_cash (always 1), cost

	collection_id = args[0]
	if collection_id <= 0:
		return False

	collections = player["privateState"]["collections"]
	data = collections[collection_id]
	reward = get_collection_reward(collection_id)
	if not reward:
		return False

	if len(args) >= 3:
		used_cash = args[1]
		cost = args[2]

		if used_cash != 1:
			return False
		if not pay_cash(player, cost):
			return False
	else:
		# check if we have 1 of each
		one_of_each = True
		idx = 1
		while idx <= 5:
			if data[idx] <= 0:
				return False
			idx += 1

	data[0] = 1
	
	if len(args) < 3:
		# subtract one of each (if no cash was used)
		idx = 1
		while idx <= 5:
			data[idx] -= 1
			idx += 1

	finished = player["privateState"]["collectionsCompleted"]
	if collection_id not in finished:
		finished.append(collection_id)

	# no support for other town IDs, sad :(
	town_id = get_default_town_id(player, gameversion)
	_map = player["maps"][town_id]

	add_store_item(_map, reward)
	register_bought_unit(player, reward, town_id)

	return True

def cmd_buy_stored_item_cash(player, cmd, args, gameversion):
	# town_id, uitem_id, cost
	town_id = args[0]
	uitem_id = int(args[1])
	cost = int(args[2])

	_map = player["maps"][town_id]

	if cost > 0:
		if not pay_cash(player, cost):
			return False

	add_store_item(_map, uitem_id)
	register_bought_unit(player, uitem_id, town_id)

	return True

def cmd_unit_collections_completed(player, cmd, args, gameversion):
	# collection_id
	collection_id = int(args[0])
	if collection_id not in player["privateState"]["unitCollectionsCompleted"]:
		player["privateState"]["unitCollectionsCompleted"].append(collection_id)
		add_cash(player, 1)
		return True

	return False

def cmd_set_variables(player, cmd, args, gameversion):
	playerInfo = player["playerInfo"]
	town_id = args[7]

	_map = player["maps"][town_id]
	_map["coins"] = args[0]
	playerInfo["cash"] = args[1]
	_map["xp"] = args[2]
	_map["level"] = args[3]
	_map["stone"] = args[4]
	_map["wood"] = args[5]
	_map["food"] = args[6]

	pvp_pool_modify(player)

	return True

def cmd_ff(player, cmd, args, gameversion):
	# seconds
	seconds = args[0]
	player_fast_forward(player, int(seconds))

	pvp_pool_modify(player)

	return True

def cmd_admin_add_animal(player, cmd, args, gameversion):
	# subcategory, amount
	subcategory = str(args[0])
	amount = int(args[1])

	animals = player["privateState"]["arrayAnimals"]
	prev = 0
	if subcategory in animals:
		prev = animals[subcategory]

	animals[subcategory] = prev + amount

	return True

def cmd_set_help_map(player, cmd, args, gameversion):
	# key
	key = str(args[0])

	help_map = player["privateState"]["helpMap"]
	if key not in help_map:
		help_map.append(key)

	return True
	
def cmd_assist_neighbor(player, cmd, args, gameversion):
	# userid, assist_id, town_id
	userid = str(args[0])
	assist_id = args[1]
	town_id = args[2]

	_map = player["maps"][town_id]
	cfg_globals = get_game_config()["globals"]

	add_map_currency(_map, "coins", int(cfg_globals["ASSIST_REWARD_GOLD"]))
	add_map_currency(_map, "xp", int(cfg_globals["ASSIST_REWARD_XP"]))

	privateState = player["privateState"]
	privateState["neighborAssists"][userid] = timestamp_now()

	return True

def cmd_assist_neighbor_new(player, cmd, args, gameversion):
	# userid, town_id, assists
	userid = str(args[0])
	town_id = args[1]
	assists = json.loads(args[2])

	status = assist_neighbor(userid, town_id, assists, player["playerInfo"]["pid"])
	if not status:
		return False

	privateState = player["privateState"]
	privateState["neighborAssists"][userid] = timestamp_now()
	
	if len(assists) >= 5:
		cfg_globals = get_game_config()["globals"]
		player["playerInfo"]["honor_points"] += cfg_globals["HONOR_POINT_HELP_FRIEND"]

	return True

def cmd_assist_receive(player, cmd, args, gameversion):
	# town_id, building_id
	town_id = args[0]
	building_id = args[1]

	return player_assist_receive(player, player["maps"][town_id], building_id)

def cmd_clean_received_assists(player, cmd, args, gameversion):
	# userid, town_id
	userid = str(args[0])
	town_id = args[1]

	_map = player["maps"][town_id]
	assists = _map["receivedAssists"]
	if userid in assists:
		del assists[userid]

	return True

def cmd_market_trade_resource(player, cmd, args, gameversion):
	# town_id, resource_type, is_sell, amount
	town_id = args[0]
	resource_type = args[1]
	is_sell = args[2] == 1
	amount = args[3]

	_map = player["maps"][town_id]
	res_traded = _map["resourcesTraded"]
	
	res_trades = get_resource_trades(res_traded, resource_type)
	res_trades = clamp(res_trades, -MARKET_MAX_DECREMENTS, MARKET_MAX_INCREMENTS)

	base_cost = MARKET_BASE_COSTS[resource_type] * (amount / 100)
	cost = int(round(base_cost + base_cost * res_trades * MARKET_INCREMENT))
	sell_cost = int(round(cost * MARKET_SELL_PERCENTAGE))

	factor = 1
	if not is_sell:
		factor = -1

	if is_sell:
		# buy gold, for resource_type
		if not pay_resource_type(player, _map, resource_type, sell_cost):
			return False

		add_map_currency(_map, "coins", sell_cost)
	else:
		# buy resource_type for gold
		if not pay_map_currency(_map, "coins", cost):
			return False

		give_resource_type(player, _map, resource_type, amount)

	add_resource_trades(res_traded, resource_type, -factor)

	if _map["numTradesDone"] == 0:
		_map["timestampLastTrade"] = timestamp_now()

	_map["numTradesDone"] += 1

	return True

def cmd_increase_population(player, cmd, args, gameversion):
	# town_id
	town_id = args[0]

	_map = player["maps"][town_id]
	_map["increasedPopulation"] = min(5, _map["increasedPopulation"] + 1)

	return True

def cmd_set_resource_allies(player, cmd, args, gameversion):
	# resource, bx, by, town_id, bitem_id
	resource = args[0]
	bx = args[1]
	by = args[2]
	town_id = args[3]
	bitem_id = args[4]

	_map = player["maps"][town_id]
	item = map_get_item(_map, bx, by, bitem_id)
	if len(item) <= 0:
		return False

	return set_allies_market_resource(_map, item[0], resource)

def cmd_activate_dragon(player, cmd, args, gameversion):
	return _cmd_activate_nest(player, cmd, args, gameversion, "dragon")

def cmd_activate_monster(player, cmd, args, gameversion):
	return _cmd_activate_nest(player, cmd, args, gameversion, "monster")

def cmd_deactivate_dragon(player, cmd, args, gameversion):
	return _cmd_deactivate_nest(player, cmd, args, gameversion, "dragon")

def cmd_deactivate_monster(player, cmd, args, gameversion):
	return _cmd_deactivate_nest(player, cmd, args, gameversion, "monster")

def cmd_next_dragon(player, cmd, args, gameversion):
	return _cmd_next_nest(player, cmd, args, gameversion, "dragon")

def cmd_next_monster(player, cmd, args, gameversion):
	return _cmd_next_nest(player, cmd, args, gameversion, "monster")

def cmd_next_step_dragon(player, cmd, args, gameversion):
	return _cmd_next_step_nest(player, cmd, args, gameversion, "dragon")

def cmd_next_step_monster(player, cmd, args, gameversion):
	return _cmd_next_step_nest(player, cmd, args, gameversion, "monster")

def cmd_buy_step_dragon(player, cmd, args, gameversion):
	return _cmd_buy_step_nest(player, cmd, args, gameversion, "dragon")

def cmd_buy_step_monster(player, cmd, args, gameversion):
	return _cmd_buy_step_nest(player, cmd, args, gameversion, "monster")

def cmd_reset_dragon(player, cmd, args, gameversion):
	return _cmd_reset_nest(player, cmd, args, gameversion, "dragon")

def cmd_reset_monster(player, cmd, args, gameversion):
	return _cmd_reset_nest(player, cmd, args, gameversion, "monster")

def _cmd_activate_nest(player, cmd, args, gameversion, nest_type):
	# currency
	resource = str(args[0])

	# no support for other town IDs, sad :(
	town_id = get_default_town_id(player, gameversion)
	_map = player["maps"][town_id]

	nest = get_nest(nest_type)
	if not nest:
		log.info("invalid nest")
		return False

	if resource not in nest["cost"]:
		return False
	cost_key = nest["cost"][resource]

	cfg_globals = get_game_config()["globals"]
	cost = cfg_globals[cost_key]
	if not pay_resource_type(player, _map, resource, cost):
		log.info("no funds")
		return False

	privateState = player["privateState"]
	privateState[nest["flag"]] = 1
	privateState[nest["num"]] = 0
	privateState[nest["step"]] = 0
	privateState[nest["ts"]] = 0

	return True

def _cmd_deactivate_nest(player, cmd, args, gameversion, nest_type):
	nest = get_nest(nest_type)
	if not nest:
		return False

	privateState = player["privateState"]
	privateState[nest["flag"]] = 0
	privateState[nest["num"]] = 0
	privateState[nest["step"]] = 0
	privateState[nest["ts"]] = 0
	return True

def _cmd_next_nest(player, cmd, args, gameversion, nest_type):
	# zero
	zero = args[0] # always sent as "0"

	nest = get_nest(nest_type)
	if not nest:
		return False

	privateState = player["privateState"]
	if privateState[nest["flag"]] == 0:
		return False

	privateState[nest["num"]] += 1
	privateState[nest["step"]] = 0
	privateState[nest["ts"]] = 0

	return True
	
def _cmd_next_step_nest(player, cmd, args, gameversion, nest_type):
	# cash_cost
	cash_cost = args[0]

	nest = get_nest(nest_type)
	if not nest:
		return False

	privateState = player["privateState"]
	if privateState[nest["flag"]] == 0:
		return False

	if cash_cost > 0:
		if not pay_cash(player, cash_cost):
			return False

	privateState[nest["step"]] += 1
	privateState[nest["ts"]] = timestamp_now()

	return True

def _cmd_buy_step_nest(player, cmd, args, gameversion, nest_type):
	# cash_cost
	cash_cost = args[0]

	nest = get_nest(nest_type)
	if not nest:
		return False

	privateState = player["privateState"]
	if privateState[nest["flag"]] == 0:
		return False

	if cash_cost > 0:
		if not pay_cash(player, cash_cost):
			return False

	privateState[nest["ts"]] = 0

	return True

def _cmd_reset_nest(player, cmd, args, gameversion, nest_type):
	nest = get_nest(nest_type)
	if not nest:
		return False

	privateState = player["privateState"]
	privateState[nest["flag"]] = 0
	privateState[nest["num"]] = 0
	privateState[nest["step"]] = 0
	privateState[nest["ts"]] = 0

	return True

def cmd_rider_select(player, cmd, args, gameversion):
	# rider_id
	rider_id = int(args[0])
	if rider_id < 0 or rider_id > 3:
		return False

	rider = get_rider()
	privateState = player["privateState"]

	privateState[rider["flag"]] = rider_id
	privateState[rider["step"]] = 0
	privateState[rider["ts"]] = 0
	return True

def cmd_rider_next_step(player, cmd, args, gameversion):
	# success
	success = int(args[0]) == 1

	if not success:
		return False

	rider = get_rider()
	privateState = player["privateState"]

	if privateState[rider["flag"]] == 0:
		return False

	privateState[rider["step"]] += 1
	privateState[rider["ts"]] = timestamp_now()

	return True

def cmd_rider_buy_step(player, cmd, args, gameversion):
	# cost
	cost = int(args[0])

	rider = get_rider()
	privateState = player["privateState"]

	if privateState[rider["flag"]] == 0:
		return False

	if not pay_cash(player, cost):
		return False
	
	privateState[rider["ts"]] = 0

	return True

def cmd_rider_reset(player, cmd, args, gameversion):
	rider = get_rider()

	privateState = player["privateState"]
	privateState[rider["flag"]] = 0
	privateState[rider["step"]] = 0
	privateState[rider["ts"]] = 0

	return True

def cmd_sb_next_step(player, cmd, args, gameversion):
	# offering, step_id
	offering = json.loads(args[0])
	step_id = int(args[1])

	# no support for other town IDs, sad :(
	town_id = get_default_town_id(player, gameversion)
	_map = player["maps"][town_id]

	if len(offering) != 1:
		return False

	for offering_type in offering:
		cost = offering[offering_type]

		if offering_type == "u":				# unit sacrifice
			# the game sells the unit for you with a sell command
			if step_id < 6 or step_id >= 11:
				return False

		elif offering_type == "collection":		# bahamut heart
			# the game does not sell the heart from your inventory when doing this one
			# it is sold when all steps are completed and you obtain the dragon
			if step_id != 11:
				return False
			if cost not in player["privateState"]["collectionsCompleted"]:
				return False
		else:									# resource offering
			if step_id >= 6:
				return False
			if not pay_resource_type(player, _map, offering_type, cost):
				return False

	sb = get_sb_temple()

	privateState = player["privateState"]
	privateState[sb["step"]].append(step_id)
	privateState[sb["ts"]] = timestamp_now()

	return True

def cmd_sb_buy_step_cash(player, cmd, args, gameversion):
	# cost
	cost = int(args[0])
	if cost > 0:
		if not pay_cash(player, cost):
			return False

	sb = get_sb_temple()

	privateState = player["privateState"]
	privateState[sb["ts"]] = 0

	return True

def cmd_sb_reset(player, cmd, args, gameversion):
	sb = get_sb_temple()

	privateState = player["privateState"]
	privateState[sb["step"]] = []
	privateState[sb["ts"]] = 0
	return True

def cmd_hellforge_add_item(player, cmd, args, gameversion):
	# item_id, use_cash
	item_id = args[0]
	use_cash = args[1] == 1

	collect_game = player["privateState"]["collectGame"]
	data = collect_game[str(item_id)]

	if use_cash:
		item = get_hellforge_item(item_id)
		if not item:
			return False

		cost = item["cost"]
		if data["counter"] == item["required"] - 1:
			cost = item["last_cost"]
		if not pay_cash(player, cost):
			return False

	data["counter"] += 1
	if use_cash:
		data["timestamp"] = 0
	else:
		data["timestamp"] = timestamp_now()
	
	return True

def cmd_hellforge_update_ts(player, cmd, args, gameversion):
	# item_id
	item_id = args[0]

	collect_game = player["privateState"]["collectGame"]
	data = collect_game[str(item_id)]

	data["timestamp"] = timestamp_now()
	
	return True

def cmd_hellforge_speed_up(player, cmd, args, gameversion):
	# item_id
	item_id = args[0]

	item = get_hellforge_item(item_id)
	if not item:
		return False

	if not pay_cash(player, item["speedup_cost"]):
		return False

	collect_game = player["privateState"]["collectGame"]
	data = collect_game[str(item_id)]
	data["timestamp"] = 0

	return True

def cmd_hellforge_buy_all(player, cmd, args, gameversion):
	# hellforge_game_id
	hellforge_game_id = int(args[0])
	if hellforge_game_id != 1:
		return False
	
	event = get_event_data(hellforge_game_id)

	if not pay_cash(player, hellforge_buy_all_price(player)):
		return False

	# fill in all items and friend slots!
	collect_game = player["privateState"]["collectGame"]
	for it in collect_game:
		item = collect_game[it]
		item_data = get_hellforge_item(item["id"])
		required = item_data["required"]
		item["counter"] = required

		if item["id"] == HELLFORGE_INVITE_ITEM:
			friends = player["privateState"]["viralOffers"]["2"]["friends"]
			num_friends = len(friends)
			while num_friends < required:
				friends.append("0")
				num_friends += 1

	return True

def cmd_hellforge_reward_given(player, cmd, args, gameversion):
	# items
	item_id = int(args[0])
	rewards_given = player["privateState"]["collectGameGivenPrizes"]

	if item_id in rewards_given:
		return False
	
	rewards_given.append(item_id)

	return True

def cmd_event_buy_friend(player, cmd, args, gameversion):
	# offer_id
	offer_id = args[0]

	offer = get_event_offer(offer_id)
	if not offer:
		return False

	player_offers = player["privateState"]["viralOffers"]
	offer_data = player_offers[str(offer_id)]
	num_friends = len(offer_data["friends"])
	max_friends = offer["num_workers"]

	if num_friends >= max_friends:
		return False

	if offer_id == 2:
		# hell forge
		invite_item = get_hellforge_item(HELLFORGE_INVITE_ITEM)
		if not invite_item:
			return False

		offer_data["friends"].append("0")
	else:
		if not pay_cash(player, offer["buy_cost"][num_friends]):
			return False

		offer_data["friends"].append("0")
		
	return True

def cmd_event_buy_friend_all(player, cmd, args, gameversion):
	# offer_id
	offer_id = args[0]

	offer = get_event_offer(offer_id)
	if not offer:
		return False

	player_offers = player["privateState"]["viralOffers"]
	offer_data = player_offers[str(offer_id)]
	num_friends = len(offer_data["friends"])
	max_friends = offer["num_workers"]

	if num_friends >= max_friends:
		return False

	if offer_id == 2:
		# hell forge
		return False
	else:
		if not pay_cash(player, offer["buy_all_cost"][num_friends]):
			return False

		while num_friends < max_friends:
			offer_data["friends"].append("0")
			num_friends += 1
		
	return True

def cmd_event_get_reward(player, cmd, args, gameversion):
	# offer_id, x, y, orientation, town_id
	offer_id = args[0]
	x = args[1] # not used
	y = args[2] # not used
	orientation = args[3] # not used
	town_id = args[4] # not used

	# so the game adds the item to the map on the client
	# does NOT tell the server
	# then stores that item immediately in storage
	# but it tells the server to just add the item as if it was a unit pack
	
	offer = get_event_offer(offer_id)
	if not offer:
		return False

	player_offers = player["privateState"]["viralOffers"]
	offer_data = player_offers[str(offer_id)]
	num_friends = len(offer_data["friends"])
	max_friends = offer["num_workers"]

	if type(offer_data["rewarded"]) != int:
		offer_data["rewarded"] = 0
	if offer_data["rewarded"] == 1:
		return False

	if offer_id == 2:
		# hell forge
		offer_data["rewarded"] = 1
	else:
		offer_data["rewarded"] = 1
		
	return True

def cmd_set_first_purchase_ts(player, cmd, args, gameversion):
	player["privateState"]["firstPurchaseTimestamp"] = timestamp_now()

	return True

def cmd_buy_first_purchase(player, cmd, args, gameversion):
	# no support for other town IDs, sad :(
	town_id = get_default_town_id(player, gameversion)
	_map = player["maps"][town_id]

	cfg_globals = get_game_config()["globals"]
	if not pay_cash(player, cfg_globals["POPUP_FIRST_PURCHASE_OFFER_COST"]):
		return False

	rewards = cfg_globals["POPUP_FIRST_PURCHASE_OFFER_REWARD"]
	for r in rewards:
		if r == "units":
			continue
		if r == "exp":
			add_map_currency(_map, "xp", int(rewards[r]))
			continue
		give_resource_type(player, _map, r, int(rewards[r]))

	player["privateState"]["firstPurchaseTimestamp"] = 1

	return True

def cmd_complete_tutorial(player, cmd, args, gameversion):
	# step
	step = str(args[0])

	player["playerInfo"]["completed_tutorial"] = step
	return True

def cmd_complete_goal(player, cmd, args, gameversion):
	# goal_id, [cash_cost]
	# TODO: FIX 1.4.07 GOALS
	goal_id = int(args[0])

	if goal_id <= 0:	# invalid goal (client error)
		return True

	privateState = player["privateState"]
	if goal_id in privateState["completedMissions"]:
		return True

	if len(args) >= 1:
		cash_cost = int(args[1])
		if not pay_cash(player, cash_cost):
			return False

	privateState["completedMissions"].append(goal_id)

	return True
	
def cmd_reward_goal(player, cmd, args, gameversion):
	# town_id, goal_id
	# TODO: FIX 1.4.07 GOALS
	town_id = int(args[0])
	goal_id = int(args[1])

	if goal_id <= 0:	# invalid goal (client error)
		return True

	_map = player["maps"][town_id]

	goal = get_mission(goal_id)
	if not goal:
		return True

	privateState = player["privateState"]
	if goal_id in privateState["rewardedMissions"]:
		return True

	add_map_currency(_map, "coins", goal["reward"])
	privateState["rewardedMissions"].append(goal_id)

	return True

def cmd_win_bonus(player, cmd, args, gameversion):
	# gold, town_id, uitem_id, next_day, cash
	gold = int(args[0])
	town_id = int(args[1])
	uitem_id = int(args[2])
	next_day = int(args[3])
	cash = int(args[4])

	_map = player["maps"][town_id]

	if cash > 0:
		add_cash(player, cash)
	if gold > 0:
		add_map_currency(_map, "coins", gold)
	if uitem_id > 0:
		add_store_item(_map, uitem_id)

	privateState = player["privateState"]
	privateState["bonusNextId"] = next_day + 1
	privateState["timestampLastBonus"] = timestamp_now()

	return True