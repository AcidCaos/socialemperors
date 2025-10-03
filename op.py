import json

from sessions import session, save_session, pvp_pool_modify, pvp_modify_victim
from get_game_config import get_game_config, get_level_from_xp, get_name_from_item_id, get_attribute_from_mission_id, get_xp_from_level, get_attribute_from_item_id, get_item_from_subcat_functional
from constants import Constant
from engine import *

def cmd_nop(player, cmd, args, gameversion):
	return True

def cmd_ping(player, cmd, args, gameversion):
	# id
	return True

def cmd_game_status(player, cmd, args, gameversion):
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
	map_add_item(_map, item_id, x, y, orientation = orientation)

	if not is_free:
		apply_cost(player["playerInfo"], _map, item_id, price_mult)
		apply_xp_for_item(_map, item_id)

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
	map_remove_item(_map, x, y, item_id)
	
	if not is_free:
		if get_attribute_from_item_id(item_id, "cost_type") != "c":
			# you sell at 5% value
			apply_cost(player["playerInfo"], _map, item_id, -SELL_DIVISOR)
	if resurrectable:
		try_push_graveyard(player, item_id)

	return True

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
	if len(building) != 1 or len(unit) <= 0:
		return False	# map error, multiple units or buildings in same location

	map_push_unit(_map, unit[0], building[0])

	return True

def cmd_pop_unit(player, cmd, args, gameversion):
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
	town_id = 0
	_map = player["maps"][town_id]

	building = map_get_item(_map, bx, by)
	if len(building) != 1:
		return False	# map error, multiple buildings in same location

	if not_soulmixer:
		# charge for training costs
		item_data = get_item_from_id(uitem_id)
		cost = int(item_data["cost"])
		cost_type = item_data["cost_type"]
		cost_food = cost << 1			# x2 food

		refund_res =  pay_resource_type(_map, cost_type, cost)
		if not refund_res:
			# not paid, no stealing!!!!
			return False

		if not pay_resource_type(_map, "f", cost_food):
			if refund_res and cost_type != "c":
				# lets not steal resources for no reason
				give_resource_type(player["playerInfo"], _map, cost_type, cost_food)
			return False

	if not player_push_queue_unit(player, building[0], uitem_id, bq, not not_soulmixer):
		return False	# well damn

	return True

def cmd_speed_up_queue(player, cmd, args, gameversion):
	# bq
	bq = str(args[0])

	building = player_get_item_with_bq(player, bq)
	if len(building) != 1:
		return False	# map error, multiple buildings in same location

	return player_speed_up_queue(player, building[0], bq)
	
def cmd_pop_queue_unit(player, cmd, args, gameversion):
	# bq, ux, uy, bitem_id
	bq = str(args[0])
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

def cmd_unqueue_unit(player, cmd, args, gameversion):
	# bq, bitem_id
	bq = str(args[0])
	bitem_id = args[1]

	# no support for other town IDs, sad :(
	town_id = 0
	_map = player["maps"][town_id]

	building = player_get_item_with_bq(player, bq)
	print(building)
	if len(building) != 1:
		return False	# map error, multiple buildings in same location

	# result is None if fail or unit_id that was unqueued
	unit_id = player_unqueue_unit(player, building[0], bq)
	if not unit_id:
		return False

	item_data = get_item_from_id(unit_id)
	cost = int(item_data["cost"])
	cost_type = item_data["cost_type"]
	cost_food = cost << 1			# x2 food

	# refund
	give_resource_type(player["playerInfo"], _map, cost_type, cost)
	give_resource_type(player["playerInfo"], _map, "f", cost_food)

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

	map_remove_item(_map, x, y, item_id)
	add_store_item(player, item_id, 1)

	return True

def cmd_sell_gift(player, cmd, args, gameversion):
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

def cmd_sell_stored_item(player, cmd, args, gameversion):
	# item_id, town_id
	item_id	= args[0]
	town_id = args[1]
	
	_map = player["maps"][town_id]

	remove_store_item(player, item_id, 1)
	if get_attribute_from_item_id(item_id, "cost_type") != "c":
		# you sell at 5% value
		apply_cost(player["playerInfo"], _map, item_id, -SELL_DIVISOR)

	return True

def cmd_place_gift(player, cmd, args, gameversion):
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

def cmd_graveyard_buy_potions(player, cmd, args, gameversion):
	potion_data = get_game_config()["globals"]["GRAVEYARD_POTIONS"]
	potion_amount = int(potion_data["amount"])
	price = int(potion_data["price"]["c"])

	if pay_cash(player, price):
		add_potions(player, potion_amount)
		return True

	return False

def cmd_resurrect_hero(player, cmd, args, gameversion):
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
		return False
	
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
		return False

	map_add_item(_map, uitem_id, ux, uy)

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
	warehouse_reset(player, _map)

	return True

def cmd_name_map(player, cmd, args, gameversion):
	# town_id, name
	town_id = args[0]
	name = str(args[1])

	player["playerInfo"]["map_names"][town_id] = name
	player["playerInfo"]["name"] = name # allow renaming of profile too

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

	cfg_global = get_game_config()["globals"]
	cash_amount = cfg_global["EXCHANGE_CASH"]
	gold_amount = cfg_global["EXCHANGE_GOLD"]

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
	town_id = 0
	_map = player["maps"][town_id]
	level_old = _map["level"]

	gained = max(0, level_now - level_old)

	levels = get_game_config()["levels"]
	level_data = levels[level_now - 1]

	give_levelup_reward(player, _map, level_data)

	_map["level"] = level_now
	_map["xp"] = max(get_xp_from_level(max(0, level_now - 1)), _map["xp"])

	pvp_pool_modify(player)

	return True

def cmd_rt_publish_score(player, cmd, args, gameversion):
	# xp_now 
	xp_now = int(args[0])

	# no support for other town IDs, sad :(
	town_id = 0
	_map = player["maps"][town_id]

	_map["xp"] = xp_now

	pvp_pool_modify(player)

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

	_map["questTimes"][str(quest_id)] = ts_now
	_map["lastQuestTimes"].append(ts_now)

	return True

def cmd_end_quest(player, cmd, args, gameversion):
	# json
	data = json.loads(args[0])
	#print(json.dumps(data, indent='\t'))

	privateState = player["privateState"]

	units = data["units"]
	quest_id = data["quest_id"]
	next_index = None
	set_unlocked_index = False
	if "set_unlocked_index" in data:
		set_unlocked_index = data["set_unlocked_index"] == 1
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

	if win:
		#if set_unlocked_index == 1:
		# if we won then unlock next quest
		old_index = privateState["unlockedQuestIndex"]
		if old_index == None:
			old_index = -1
		if next_index - old_index <= 1:
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
	town_id = 0
	_map = player["maps"][town_id]
	privateState = player["privateState"]

	shield = get_shield_data(shield_id)
	if not shield:
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
	player["playerInfo"]["cash"] += int(shield["price"]) << 1

	# This implementation however doesn't require you to do the step of visiting your friend's empire
	# -----------------------------------------------------------------------------------------------------------

	shield_duration = shield["protection_time"]
	shield_cooldown = shield["cooldown"]

	bought = privateState["purchasedShields"]
	if not shield_id in bought:
		bought.append(shield_id)
	
	end_time = privateState["shieldEndTime"]
	cooldown = privateState["shieldCooldown"]

	ts_now = timestamp_now()
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
	town_id = 0
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
	town_id = 0
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