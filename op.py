import json

from sessions import session, save_session
from get_game_config import get_game_config, get_level_from_xp, get_name_from_item_id, get_attribute_from_mission_id, get_xp_from_level, get_attribute_from_item_id, get_item_from_subcat_functional
from constants import Constant
from engine import *

def cmd_nop(player, cmd, args):
	# do nothing, command not implemented

	return True

def cmd_game_status(player, cmd, args):
	print("GAME STATUS: " + " ".join(args))

	return True

def cmd_buy(player, cmd, args):
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
	map_add_item(_map, item_id, x, y, orientation = orientation)

	if not is_free:
		apply_cost(player["playerInfo"], _map, item_id, price_mult)
		apply_xp_for_item(_map, item_id)

	return True

def cmd_move(player, cmd, args):
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

def cmd_orient(player, cmd, args):
	# x, y, orientation, town_id
	x = args[0]
	y = args[1]
	orientation = args[2]
	town_id = args[3]

	_map = player["maps"][town_id]
	map_orient_item(_map, x, y, orientation)

	return True

def cmd_sell(player, cmd, args):
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
	map_remove_item(_map, x, y, item_id)
	
	if not is_free:
		if get_attribute_from_item_id(item_id, "cost_type") != "c":
			# you sell at 5% value
			apply_cost(player["playerInfo"], _map, item_id, -SELL_DIVISOR)
	if resurrectable:
		try_push_graveyard(player, item_id)

	return True

def cmd_kill(player, cmd, args):
	# x, y, item_id, town_id, item_type
	x = args[0]
	y = args[1]
	item_id = args[2]
	town_id = args[3]
	item_type = args[4] # b or u

	_map = player["maps"][town_id]
	map_kill_item(_map, x, y, item_id, item_type)
	
	return True

def cmd_push_unit(player, cmd, args):
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
	if len(building) != 1 or len(unit) != 1:
		return False	# map error, multiple units or buildings in same location

	map_push_unit(_map, unit[0], building[0])

	return True

def cmd_pop_unit(player, cmd, args):
	# bx, by, town_id, uitem_id, ux, uy, uorientation
	bx = args[0]
	by = args[1]
	town_id = args[2]
	uitem_id = args[3]
	ux = args[4]
	uy = args[5]
	uorientation = args[6]

	_map = player["maps"][town_id]
	building = map_get_item(_map, bx, by)
	if len(building) != 1:
		return False	# map error, multiple buildings in same location
	if not map_pop_unit(_map, building[0], uitem_id, ux, uy, uorientation):
		return False	# unit was never in this building

	return True

def cmd_push_queue_unit(player, cmd, args):
	# bx, by, bitem_id, uitem_id, bq, not_soulmixer
	bx = args[0]
	by = args[1]
	bitem_id = args[2]
	uitem_id = args[3]
	bq = args[4]
	not_soulmixer = True
	if len(args) >= 5:
		not_soulmixer = args[5]

	# no support for other town IDs, sad :(
	town_id = 0
	_map = player["maps"][town_id]

	building = map_get_item(_map, bx, by)
	if len(building) != 1:
		return False	# map error, multiple buildings in same location

	if not player_push_queue_unit(player, building[0], uitem_id, bq, not not_soulmixer):
		return False	# well damn

	return True
	
def cmd_pop_queue_unit(player, cmd, args):
	return False

def cmd_store_item(player, cmd, args):
	# x, y, town_id, item_id
	x = args[0]
	y = args[1]
	town_id = args[2]
	item_id = args[3]

	_map = player["maps"][town_id]

	map_remove_item(_map, x, y, item_id)
	add_store_item(player, item_id, 1)

	return True

def cmd_sell_gift(player, cmd, args):
	# item_id, town_id
	item_id	= args[0]
	town_id = args[1]
	
	_map = player["maps"][town_id]

	remove_store_item(player, item_id, 1)

	# not sure if gifts should give resources when selling but lets leave it like this
	if get_attribute_from_item_id(item_id, "cost_type") != "c":
		# you sell at 5% value
		apply_cost(player["playerInfo"], _map, item_id, -SELL_DIVISOR)

	return True

def cmd_sell_stored_item(player, cmd, args):
	# item_id, town_id
	item_id	= args[0]
	town_id = args[1]
	
	_map = player["maps"][town_id]

	remove_store_item(player, item_id, 1)
	if get_attribute_from_item_id(item_id, "cost_type") != "c":
		# you sell at 5% value
		apply_cost(player["playerInfo"], _map, item_id, -SELL_DIVISOR)

	return True

def cmd_store_item_frombug(player, cmd, args):
	return cmd_store_item(player, cmd, args)

def cmd_place_gift(player, cmd, args):
	# item_id, x, y, orientation, town_id
	item_id = args[0]
	x = args[1]
	y = args[2]
	orientation = args[3]
	town_id = args[4]

	_map = player["maps"][town_id]

	map_add_item(_map, item_id, x, y, orientation = orientation)
	remove_store_item(player, item_id, 1)

	return True

def cmd_graveyard_buy_potions(player, cmd, args):
	potion_data = get_game_config()["globals"]["GRAVEYARD_POTIONS"]
	potion_amount = int(potion_data["amount"])
	price = int(potion_data["price"]["c"])

	if pay_cash(player, price):
		potion_add(player, potion_amount)
		return True

	return False

def cmd_resurrect_hero(player, cmd, args):
	# item_id, x, y, town_id, [used_potion]
	item_id = args[0]
	x = args[1]
	y = args[2]
	town_id = args[3]
	used_potion = False
	if len(args) >= 4:
		used_potion = args[4]

	if used_potion:
		potion_price = get_attribute_from_item_id(item_id, "potion")
		if not potion_price:
			return False
		if not pay_potions(player, potion_price):
			return False
	else:
		print("cmd_resurrect_hero EDGE CASE NOT IMPLEMENTED!")
		return False
		# TODO: resurrected a dead hero instead? idk

	_map = player["maps"][town_id]
	map_add_item(_map, item_id, x, y)
	graveyard_remove(player, item_id)

	return True

def cmd_set_variables(player, cmd, args):
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

	return True

