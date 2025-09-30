import json

from sessions import session, save_session
from get_game_config import get_game_config, get_level_from_xp, get_name_from_item_id, get_attribute_from_mission_id, get_xp_from_level, get_attribute_from_item_id, get_item_from_subcat_functional
from constants import Constant
from engine import *

def cmd_nop(player, cmd, args):
	return True

def cmd_game_status(player, cmd, args):
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

def cmd_speed_up_queue(player, cmd, args):
	# bq
	bq = args[0]

	building = player_get_item_with_bq(player, bq)
	if len(building) != 1:
		return False	# map error, multiple buildings in same location

	return player_speed_up_queue(player, building[0], bq)
	
def cmd_pop_queue_unit(player, cmd, args):
	# bq, ux, uy, bitem_id
	bq = args[0]
	ux = args[1]
	uy = args[2]
	bitem_id = args[3]

	# no support for other town IDs, sad :(
	town_id = 0
	_map = player["maps"][town_id]

	building = player_get_item_with_bq(player, bq)
	if len(building) != 1:
		return False	# map error, multiple buildings in same location

	result = player_pop_queue_unit(player, building[0], bq)
	if not result:
		return False
	unit_id = result[0]
	is_soulmixer = result[1]
	map_add_item(_map, unit_id, ux, uy)

	return True

def cmd_sm_powerup(player, cmd, args):
	# powerup_idx
	powerup_idx = int(args[0])

	powerup = get_game_config()["globals"]["SOUL_MIXER_POWERUPS_LEVELS"][powerup_idx]
	if not pay_cash(player, powerup["cash_cost"]):
		return False

	return True

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
		add_potions(player, potion_amount)
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

def cmd_name_map(player, cmd, args):
	# town_id, name
	town_id = args[0]
	name = str(args[1])

	player["playerInfo"]["map_names"][town_id] = name

	return True

def cmd_set_strategy(player, cmd, args):
	# strategy
	strategy = args[0]

	save["privateState"]["strategy"] = strategy

	return True

def cmd_exchange_cash(player, cmd, args):
	town_id = args[0]

	cfg_global = get_game_config()["globals"]
	cash_amount = cfg_global["EXCHANGE_CASH"]
	gold_amount = cfg_global["EXCHANGE_GOLD"]

	_map = player["maps"][town_id]
	if not pay_cash(player, cash_amount):
		return False

	add_map_currency(_map, "coins", gold_amount)

	return True

def cmd_expand(player, cmd, args):
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

def cmd_rt_level_up(player, cmd, args):
	# level_now
	level_now = int(args[0])

	# no support for other town IDs, sad :(
	town_id = 0
	_map = player["maps"][town_id]
	level_old = _map["level"]

	gained = max(0, level_now - level_old)

	levels = get_game_config()["levels"]
	level_data = levels[level_now - 1]

	give_levelup_reward(player, _map, level_data)

	_map["level"] = level_now
	_map["xp"] = max(get_xp_from_level(max(0, level_now - 1)), _map["xp"])

	return True

def cmd_rt_publish_score(player, cmd, args):
	# xp_now 
	xp_now = int(args[0])

	# no support for other town IDs, sad :(
	town_id = 0
	_map = player["maps"][town_id]

	_map["xp"] = xp_now
	_map["level"] = get_level_from_xp(xp_now)

	return True

def cmd_start_quest(player, cmd, args):
	# quest_id, town_id
	quest_id = args[0]
	town_id = args[1]

	ts_now = timestamp_now()
	_map = player["maps"][town_id]

	_map["questTimes"][str(quest_id)] = ts_now
	_map["lastQuestTimes"].append(ts_now)

	return True

def cmd_end_quest(player, cmd, args):
	# json
	data = json.loads(args[0])
	# print(json.dumps(data, indent='\t'))

	privateState = player["privateState"]

	units = data["units"]
	quest_id = data["quest_id"]
	next_index = None
	if "set_unlocked_index" in data:
		next_index = data["set_unlocked_index"]
	else:
		next_index = get_quest_index(quest_id)

	win = False
	if "voluntary_end" in data:
		win = data["voluntary_end"] == 0
	elif "win" in data:
		win = data["win"] == 1

	resources = data["resources"]
	difficulty = data["difficulty"]
	town_id = data["map"]

	_map = player["maps"][town_id]

	
	if win:
		# if we won then unlock next quest
		old_index = privateState["unlockedQuestIndex"]
		if old_index == None:
			old_index = -1
		privateState["unlockedQuestIndex"] = max(next_index, old_index)

		# if we won, also set quest rank
		rank = privateState["questsRank"][str(quest_id)]
		if rank == None:
			rank = 0
		privateState["questsRank"][str(quest_id)] = max(difficulty, rank)

	# give player gold and xp
	add_map_currency(_map, "coins", resources["g"])
	add_map_currency(_map, "xp", resources["x"])

	# remove lost units and send them to graveyard
	for unit in units:
		uid = unit[0]
		entered = unit[1]
		died = unit[2]
		recovered = unit[3]
		lost = died - recovered

		if lost > 0:
			player_lose_item(player, _map, uid, lost)

	return False

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

def cmd_admin_add_animal(player, cmd, args):
	# subcategory, amount
	subcategory = str(args[0])
	amount = int(args[1])

	animals = player["privateState"]["arrayAnimals"]
	prev = 0
	if subcategory in animals:
		prev = animals[subcategory]

	animals[subcategory] = prev + amount

	return True