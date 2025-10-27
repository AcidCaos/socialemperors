import time
import math
import random
import logging

from get_game_config import *
from constants import *
from event_system import get_active_events

# grab server settings
from server_config import get_server_config

log = logging.getLogger('__main__')

# cannot be resurrected
resurrectable_items_blocklist = [
	Constant.ID_UNIT_PEASANT_MALE,
	Constant.ID_UNIT_PEASANT_FEMALE
]
# subcats that cannot be resurrected
resurrectable_sub_blocklist = [
	Constant.SUBCATFUNC_UNIT_COW,
	Constant.SUBCATFUNC_UNIT_SHEEP,
	Constant.SUBCATFUNC_UNIT_HORSE,
	Constant.SUBCATFUNC_UNIT_BOAR
]
# races that cannot be resurrected
resurrectable_race_blocklist = [
	"t" # trolls
]
# set resurrectable amount to 1
resurrectable_heroes = [
	Constant.ID_UNIT_RANGER,
	Constant.ID_UNIT_XENA,
	Constant.ID_UNIT_ARTHUR,
	Constant.ID_UNIT_MERLIN,
	Constant.ID_UNIT_VALKIRIA,
	Constant.ID_UNIT_WALLACE,
	Constant.ID_UNIT_THOR,
	Constant.ID_UNIT_HIGHELF
]

# training discount subcats
blacksmith_discount_subcats = [
	Constant.SUBCATFUNC_UNIT_ARCHER,
	Constant.SUBCATFUNC_UNIT_FOOTMAN,
	Constant.SUBCATFUNC_UNIT_MOUNTED
]
university_discount_subcats = [
	Constant.SUBCATFUNC_UNIT_SIEGE
]
BUILDING_BLACKSMITH = get_blacksmith_id()
BUILDING_UNIVERSITY = get_university_id()

# collect multipliers
collect_multiplier = [
	0.0,
	0.5,
	1.0,
	2.0,
	3.0
]

# nest lookup table
_nest_lut = {
	"dragon": {
		"cost": {
			"c":		"ACTIVATE_DRAGON_NEST_CASH",
			"g":		"ACTIVATE_DRAGON_NEST_GOLD"
		},
		"flag":			"dragonNestActive",
		"num":			"dragonNumber",
		"step":			"stepNumber",
		"ts":			"timeStampTakeCare"
	},
	"monster": {
		"cost": {
			"c":		"ACTIVATE_MONSTER_NEST_CASH",
			"g":		"ACTIVATE_MONSTER_NEST_GOLD"
		},
		"flag":			"monsterNestActive",
		"num":			"monsterNumber",
		"step":			"stepMonsterNumber",
		"ts":			"timeStampTakeCareMonster"
	}
}

# rider lookup "table"
_rider_lut = {
	"flag":				"riderNumber",
	"step":				"riderStepNumber",
	"ts":				"riderTimeStamp",
}

# bahamut temple lookup "table"
_sb_lut = {
	"step":				"templeStep",
	"ts":				"timeStampTemple",
}

# hell forge quests
_forge_quests = [
	"100000051",
	"100000052",
	"100000053",
	"100000054",
	"100000055"
]

SELL_DIVISOR = 1.0 / 20.0 # sell divisor (divides by 20 in game for 5% sell value, negative so we refund)
SPEEDUP_COST_PER_HOUR = 1
FRIENDS_ASSIST_DIVISOR = 1.0 / 4.0
FRIENDS_ASSIST_EXPERIENCE = 10
MARKET_BASE_COSTS = {
	"f": 100,
	"s": 150,
	"w": 100
}

MARKET_SELL_PERCENTAGE = 0.75
MARKET_INCREMENT = 0.02
MARKET_MAX_INCREMENTS = 200
MARKET_MAX_DECREMENTS = 25
MARKET_AMOUNT_TRADE = [
	100,
	200,
	300
]
HELLFORGE_INVITE_ITEM = 5
RESURRECT_MULTIPLIER = 500
REDUCTION_MULTIPLIER_BLACKSMITH = 0.9
REDUCTION_MULTIPLIER_UNIVERSITY = 0.9
POTIONS_PER_FRIEND = get_server_config()["misc"]["graveyard_potions_per_friend"]

map_cost_multiple = [ "coins", "wood", "food", "stone" ]
allies_market_resources = [ "n", "g", "w", "f", "s" ]
ROUND_TABLE = get_game_config()["globals"]["ROUND_TABLE"]
autohire_ignore_buildings = [
	ROUND_TABLE,
	get_game_config()["globals"]["ALLIES_BUILDING"],
	361, # allies building for trolls
	get_game_config()["globals"]["ALLIES_MARKET"],
	get_game_config()["globals"]["ALLIES_MARKET_TROLLS"]
]
allies_market_ids = [ 
	get_game_config()["globals"]["ALLIES_MARKET"], 
	get_game_config()["globals"]["ALLIES_MARKET_TROLLS"]
]

def get_nest(nest_type):
	if nest_type in _nest_lut:
		return _nest_lut[nest_type]
	return None

def get_rider():
	return _rider_lut

def get_sb_temple():
	return _sb_lut

def timestamp_now():
	return int(time.time())

def map_add_item(map, item, x, y, orientation = 0, timestamp = None, attr = None, store = None, level = 0, userid = None):
	if not attr:
		attr = {}
	if not store:
		store = []
	if not timestamp:
		timestamp = timestamp_now()

	item_int = int(item)

	si_info = get_si_info(item_int)
	
	if si_info:
		if item_int in autohire_ignore_buildings:
			# no auto hire for specific buildings
			attr["si"] = []
			if item_int == ROUND_TABLE:
				attr["sif"] = {}
		else:
			if userid:
					attr["si"] = hire_friends(userid, si_info, item_int == 470)
			else:
				if item_int == 470:
					# great church
					attr["si"] = []
				else:
					attr["si"] = [ "0" ]

	map["items"].append([item, x, y, orientation, timestamp, level, store, attr])

def map_remove_item(map, x, y, item_id = None):
	items = map_get_item(map, x, y, item_id)
	for item in items:
		map["items"].remove(item)

def map_kill_item(map, x, y, item_id, item_type = None):
	items = map_get_item(map, x, y, item_id)
	for item in items:
		map["items"].remove(item)
		if item_type == "u":
			apply_collect_xp(map, item_id)

def map_get_item(map, x, y, item_id = None):
	found = []
	for item in map["items"]:
		if item[1] == x and item[2] == y:
			if item_id:
				if item_id == item[0]:
					found.append(item)
			else:
				found.append(item)
	return found

def map_get_items_of_id(map, item_id):
	found = []
	for item in map["items"]:
		if item[0] == item_id:
			found.append(item)
	return found

def player_get_item_with_bq(player, bq):
	found = []
	maps = player["maps"]
	for map in maps:
		for item in map["items"]:
			if "bq" in item[7]:
				if item[7]["bq"] == bq:
					found.append(item)

	return found

def map_move_item(map, item_id, x1, y1, x2, y2, orientation):
	items = map_get_item(map, x1, y1, item_id)
	if len(items) > 0:
		item = items[0]
		item[1] = x2
		item[2] = y2
		item[3] = orientation

def map_orient_item(map, x, y, orientation):
	items = map_get_item(map, x, y)
	if len(items) > 0:
		item = items[0]
		item[3] = orientation

def building_activate(item, toggle):
	if toggle > 0:
		item[4] = timestamp_now()
		item[7]["cp"] = toggle
	else:
		item[4] = timestamp_now()
		del item[7]["cp"]

def set_allies_market_resource(map, item, resource):
	if resource not in allies_market_resources:
		return False

	map["resourceAlliesMarket"] = resource
	item[4] = timestamp_now()
	item[7]["si"] = []
	return True

def building_collect(player, _map, item, vills = 1, res_multiplier = 1.0):
	item_id = item[0]
	data = get_item_from_id(item_id)
	if not data:
		return

	amount = int(data["collect"])
	resource_type = data["collect_type"]
	xp = int(data["collect_xp"])

	if int(data["subcat_functional"]) == Constant.SUBCATFUNC_BUILDING_FARM:
		# farms cost 1/3rd of the amount collected in wood
		wood_cost = int(round(amount / 3))
		if not pay_map_currency(_map, "wood", wood_cost):
			return False
	else:
		# amount based on cp
		if "cp" in item[7]:
			amount *= collect_multiplier[int(item[7]["cp"])]

	# amount based on vills
	if vills > 1:
		amount *= 1.0 + (vills - 1) * 0.2

	# resource multiplier in command
	amount = int(amount * res_multiplier)

	give_resource_type(player, _map, resource_type, amount)
	add_map_currency(_map, "xp", xp)

	item[4] = timestamp_now()

	return True

def map_push_unit(map, unit, building, remove = True):
	building[6].append(unit[0]) # append unit id to building store
	if remove:
		map["items"].remove(unit)

def map_pop_unit(map, building, item_id, x, y, orientation):
	if item_id not in building[6]:
		return False
	
	building[6].remove(item_id)
	map_add_item(map, item_id, x, y, orientation)
	return True

def map_pop_unit_short(map, building, item_id):
	if item_id not in building[6]:
		return False
	
	building[6].remove(item_id)
	return True

def player_push_queue_unit(player, building, item_id, bq, is_soulmixer, costs = None):
	attr = building[7]

	if is_soulmixer:
		attr["bq"] = str(bq)
		push_queued_unit(player, bq, item_id, costs)

		return True
	else:
		attr["bq"] = str(bq)
		push_queued_unit(player, bq, item_id, costs)

		return True

def player_speed_up_queue(player, building, bq, new_ts = 0):
	queue = get_unit_queue(player, bq)
	if not queue:
		return False

	is_soulmixer = building[0] == Constant.ID_BUILDING_SOUL_MIXER

	item = get_item_from_id(queue["unit"])
	if not item:
		return False

	training_key = "training_time"
	if is_soulmixer:
		training_key = "sm_training_time"
	training_time = item[training_key]

	if training_time:
		time_left = queue["ts"] + int(training_time) - timestamp_now()
		hours_left = int(math.ceil(time_left / 3600))
		cash_cost = hours_left * SPEEDUP_COST_PER_HOUR

		if not pay_cash(player, cash_cost):
			return False
	else:
		return False
	
	queue["ts"] = new_ts
	return True

def player_pop_queue_unit(player, building, bq):
	queue = get_unit_queue(player, bq)
	if not queue:
		return None

	is_soulmixer = building[0] == Constant.ID_BUILDING_SOUL_MIXER

	unit_id = queue["unit"]
	costs = None
	if "r" in queue:
		costs = queue["r"].pop(str(queue["amount"]), None)

	queue["amount"] -= 1
	if queue["amount"] <= 0:
		# remove queue
		remove_unit_queue(player, bq)
		del building[7]["bq"]

	return [ unit_id, is_soulmixer ]

def player_unqueue_unit(player, building, bq):
	queue = get_unit_queue(player, bq)
	if not queue:
		return None

	unit_id = queue["unit"]
	costs = None
	if "r" in queue:
		costs = queue["r"].pop(str(queue["amount"]), None)

	queue["amount"] -= 1
	if queue["amount"] <= 0:
		# remove queue
		remove_unit_queue(player, bq)
		del building[7]["bq"]

	return unit_id, costs

def get_unit_queue(player, queue_id):
	barracksQueues = player["privateState"]["barracksQueues"]
	if not str(queue_id) in barracksQueues:
		return None

	return barracksQueues[str(queue_id)]

def remove_unit_queue(player, queue_id):
	barracksQueues = player["privateState"]["barracksQueues"]
	if not str(queue_id) in barracksQueues:
		return

	del barracksQueues[str(queue_id)]

def push_queued_unit(player, queue_id, unit_id, costs = None):
	barracksQueues = player["privateState"]["barracksQueues"]
	if str(queue_id) in barracksQueues:
		q = barracksQueues[str(queue_id)]
		q["amount"] += 1
		if "r" in q:
			q["r"][str(q["amount"])] = costs

		# SP butchered this code hard, so don't extend timestamp
		# after a reload you can train 5 at the time of 1
	else:
		barracksQueues[str(queue_id)] = {
			"ts":		timestamp_now(),
			"amount":	1,
			"unit":		unit_id,
			"r":		{ "1": costs }
		}

def add_store_item(map, item, quantity = 1):
	itemstr = str(item)
	if itemstr not in map["store"]:
		map["store"][itemstr] = quantity
	else:
		map["store"][itemstr] += quantity

def remove_store_item(map, item, quantity = 1):
	itemstr = str(item)
	if itemstr in map["store"]:
		new_quantity = map["store"][itemstr] - quantity
		if new_quantity <= 0:
			del map["store"][itemstr]
		else:
			map["store"][itemstr] = new_quantity

def add_gift_item(player, item, quantity = 1):
	# DO NOT USE, THIS IS ONLY FOR WHEN PLAYERS SEND EACHOTHER GIFTS
	# USE ADD_STORE_ITEM()
	itemstr = str(item)
	if itemstr not in player["privateState"]["gifts"]:
		player["privateState"]["gifts"][itemstr] = quantity
	else:
		player["privateState"]["gifts"][itemstr] += quantity

def remove_gift_item(player, item, quantity = 1):
	# DO NOT USE, THIS IS ONLY FOR WHEN PLAYERS SEND EACHOTHER GIFTS
	# USE REMOVE_STORE_ITEM()
	itemstr = str(item)
	if itemstr in player["privateState"]["gifts"]:
		new_quantity = player["privateState"]["gifts"][itemstr] - quantity
		if new_quantity <= 0:
			del player["privateState"]["gifts"][itemstr]
		else:
			player["privateState"]["gifts"][itemstr] = new_quantity

def try_push_graveyard(player, item_id, amount = 1):
	# Based on game checks
	
	item = get_item_from_id(item_id)
	if item == None:
		return False
	if item_id in resurrectable_items_blocklist:
		return False
	if item["race"] in resurrectable_race_blocklist:
		return False
	if int(item["subcat_functional"]) in resurrectable_sub_blocklist:
		return False
	
	if item_id in resurrectable_heroes:
		graveyard_add_hero(player, item_id)
		return True

	graveyard_add(player, item_id)
	return True

def graveyard_add(player, item_id):
	resunits = player["privateState"]["resurrectableUnits"]
	resunits.append(item_id)

def graveyard_remove(player, item_id):
	resunits = player["privateState"]["resurrectableUnits"]
	resunits.remove(item_id)

def graveyard_add_hero(player, item_id):
	dead = player["privateState"]["deadHeroes"]
	if str(item_id) in dead:
		dead[str(item_id)] += 1
	else:
		dead[str(item_id)] = 1

def graveyard_remove_hero(player, item_id):
	dead = player["privateState"]["deadHeroes"]
	if str(item_id) not in dead:
		return

	dead[str(item_id)] -= 1
	if dead[str(item_id)] <= 0:
		del dead[str(item_id)]

def player_lose_item(player, map, item_id, amount, push_graveyard = True):
	items = map_get_items_of_id(map, item_id)
	while len(items) > 0 and amount > 0:
		if push_graveyard:
			try_push_graveyard(player, item_id)
		map["items"].remove(items[0])
		del items[0]
		amount -= 1

def player_fast_forward(player, seconds, time_machine = False):
	maps = player["maps"]
	privateState = player["privateState"]

	# stuff in maps
	for map in maps:
		# quests
		questTimes = map["questTimes"]
		for quest in questTimes:
			modify_ts(questTimes, quest, -seconds)

		lastQuestTimes = map["lastQuestTimes"]
		idx = len(lastQuestTimes) - 1
		while idx >= 0:
			modify_ts_array(lastQuestTimes, idx, -seconds)
			idx -= 1

		# item timestamps
		for item in map["items"]:
			modify_ts_array(item, 4, -seconds)

			if item[0] == ROUND_TABLE:
				if "sif" in item[7]:
					sif = item[7]["sif"]
					for user in sif:
						modify_ts(sif, user, -seconds)

		# market
		modify_ts(map, "timestampLastTrade", -seconds)

		# ? (probably 0.9.26b stuff)
		modify_ts(map, "timestampLastTreasure", -seconds)

	# privateState stuff
	modify_ts(privateState, "kompuLastTimeStamp", -seconds)
	modify_ts(privateState, "timestampLastBonus", -seconds)
	modify_ts(privateState, "timeStampHeavySiegePeriod", -seconds)
	modify_ts(privateState, "timeStampHeavySiegeAttack", -seconds)
	modify_ts(privateState, "timeStampDartsReset", -seconds)
	modify_ts(privateState, "timeStampDartsNewFree", -seconds)

	# nests, rider, supreme bahamut
	for n in _nest_lut:
		nest = _nest_lut[n]
		modify_ts(privateState, nest["ts"], -seconds)
	modify_ts(privateState, _rider_lut["ts"], -seconds)
	modify_ts(privateState, _sb_lut["ts"], -seconds)
	
	if not time_machine:
		# shields
		modify_ts(privateState, "shieldEndTime", -seconds)
		modify_ts(privateState, "shieldCooldown", -seconds)

		# neighbour assists
		assists = privateState["neighborAssists"]
		for user in assists:
			modify_ts(assists, user, -seconds)

		# new daily login bonus
		modify_ts(privateState, "_tsNewDailyBonus", -seconds)

	# survival arena
	survivalVidaTimeStamp = privateState["survivalVidaTimeStamp"]
	idx = len(survivalVidaTimeStamp) - 1
	while idx >= 0:
		modify_ts_array(survivalVidaTimeStamp, idx, -seconds)
		idx -= 1

	survivalMaps = privateState["survivalMaps"]
	for entry in survivalMaps:
		data = survivalMaps[entry]
		modify_ts(data, "ts", -seconds)

	# unit training queues
	barracksQueues = privateState["barracksQueues"]
	for queue in barracksQueues:
		q = barracksQueues[queue]
		modify_ts(q, "ts", -seconds)

	# events
	collect_game = privateState["collectGame"]
	for it in collect_game:
		item = collect_game[it]
		modify_ts(item, "counter", -seconds)

def warehouse_add(map, item):
	item_id = str(item[0])
	if item_id not in map["warehousedUnits"]:
		map["warehousedUnits"][item_id] = 1
	else:
		map["warehousedUnits"][item_id] += 1

	map["items"].remove(item)

def warehouse_remove(map, item_id):
	item_id = str(item_id)
	if item_id not in map["warehousedUnits"]:
		return False

	map["warehousedUnits"][item_id] -= 1
	if map["warehousedUnits"][item_id] <= 0:
		del map["warehousedUnits"][item_id]

	return True

def warehouse_reset(map):
	# push all units from warehouse to storage
	warehoused = map["warehousedUnits"]
	for item_id in warehoused:
		add_store_item(map, item_id, warehoused[item_id])
	map["warehousedUnits"] = {}

def modify_ts(dictionary, key, seconds):
	if key not in dictionary:
		dictionary[key] = 0
	elif dictionary[key] == None:
		dictionary[key] = 0
	else:
		dictionary[key] = max(dictionary[key] + seconds, 0)

def modify_ts_array(arr, idx, seconds):
	if arr[idx] == None:
		arr[idx] = 0
	else:
		arr[idx] = max(arr[idx] + seconds, 0)

def apply_collect_xp(map, item_id):
	item = get_item_from_id(item_id)
	if not item:
		return

	amount = item["collect_xp"]
	if not amount:
		return

	add_map_currency(map, "xp", int(amount))
	add_map_currency(map, "coins", 5)

def add_cash(player, amount):
	player["playerInfo"]["cash"] += int(amount)

def pay_cash(player, amount):
	if player["playerInfo"]["cash"] < int(amount):
		# not enough cash, stranger...
		return False
	player["playerInfo"]["cash"] -= int(amount)
	return True

def add_mana(player, amount):
	player["privateState"]["mana"] += int(amount)

def pay_mana(player, amount):
	if player["privateState"]["mana"] < int(amount):
		return False
	player["privateState"]["mana"] -= int(amount)
	return True

def add_map_currency(map, currency, amount):
	map[currency] += int(amount)

def pay_map_currency(map, currency, amount):
	if map[currency] < int(amount):
		return False

	map[currency] -= int(amount)
	return True

def add_map_mulitple(map, amount):
	for cost_type in map_cost_multiple:
		map[cost_type] += amount

def pay_map_multiple(map, amount):
	for cost_type in map_cost_multiple:
		if map[cost_type] < int(amount):
			return False

	for cost_type in map_cost_multiple:
		map[cost_type] -= int(amount)
	return True
	
def add_potions(player, amount = 1):
	player["privateState"]["potion"] += amount

def pay_potions(player, amount):
	if player["privateState"]["potion"] < int(amount):
		return False

	player["privateState"]["potion"] -= int(amount)
	return True

def push_si(item, friend):
	if "si" not in item[7]:
		return
	item[7]["si"].append(str(friend))

def finish_si(player, map, item):
	if "si" not in item[7]:
		return
	if item[0] in autohire_ignore_buildings:
		if item[0] in allies_market_ids:
			collect_allies_market(player, map, len(item[7]["si"]))
		if item[0] == ROUND_TABLE:
			item[7]["sif"] = {}

		item[7]["si"] = []
	else:
		del item[7]["si"]

def roundtable_ask_help(item, friend_uid):
	if "sif" not in item[7]:
		item[7]["sif"] = {}

	if friend_uid in item[7]["sif"]:
		return False

	item[7]["sif"][friend_uid] = timestamp_now()
	return True

def collect_allies_market(player, map, num_friends):
	resource_type = map["resourceAlliesMarket"]
	cfg_globals = get_game_config()["globals"]
	initial = cfg_globals["ALLIES_MARKET_INITIAL_COLLECT"][resource_type]
	incremental = cfg_globals["ALLIES_MARKET_INCREMENTAL_COLLECT"][resource_type]

	give_resource_type(player, map, resource_type, initial + incremental * num_friends)

def give_levelup_reward(player, map, level):
	reward_type = level["reward_type"]
	reward_amount = level["reward_amount"]

	give_resource_type(player, map, reward_type, reward_amount)

def give_resource_type(player, map, resource, amount):
	if resource == "w":
		map["wood"] += amount
	elif resource == "g":
		map["coins"] += amount
	elif resource == "s":
		map["stone"] += amount
	elif resource == "f":
		map["food"] += amount
	elif resource == "c":
		player["playerInfo"]["cash"] += amount
	elif resource == "m":
		player["privateState"]["mana"] += amount
	elif resource == "p":
		player["privateState"]["potion"] += amount
	elif resource == "all":
		add_map_mulitple(map, amount)

def pay_resource_type(player, map, resource, amount):
	if resource == "w":
		return pay_map_currency(map, "wood", amount)
	elif resource == "g":
		return pay_map_currency(map, "coins", amount)
	elif resource == "s":
		return pay_map_currency(map, "stone", amount)
	elif resource == "f":
		return pay_map_currency(map, "food", amount)
	elif resource == "c":
		return pay_cash(player, amount)
	elif resource == "m":
		return pay_mana(player, amount)
	elif resource == "p":
		return pay_potions(player, amount)
	elif resource == "all":
		return pay_map_multiple(map, amount)
	return False

def sb_offer_unit(player, map, item_id):
	items = map_get_items_of_id(map, item_id)
	print(items)
	if len(items) > 0:
		map["items"].remove(items[0])
		return True

	return False

def get_quest_index(quest_id):
	quests = get_game_config()["globals"]["ISLE_ORDER"]

	try:
		return quests.index(quest_id)
	except:
		return None

def get_shield_data(shield_id):
	shields = get_game_config()["pvp_shields"]
	for shield in shields:
		if shield["id"] == shield_id:
			return shield

	return None

def handle_unit_loss(player, map, units):
	for unit in units:
		uid = unit[0]
		entered = unit[1]
		died = unit[2]
		recovered = unit[3]
		lost = died - recovered

		if lost > 0:
			player_lose_item(player, map, uid, lost)

def pvp_steal_resources(player, town_id, resources, is_winner):
	map = player["maps"][town_id]
	for res in resources:
		pay_resource_type(player, map, res, resources[res])

	if not is_winner:
		player["playerInfo"]["attacks_won"] += 1
	else:
		player["playerInfo"]["attacks_lost"] += 1

def pvp_push_attack_log(player, request, extra_data, attacker):
	attack_log = player["privateState"]["PVPattacksReceived"]
	next_id = len(attack_log)

	# handle revenge attacks
	is_reply = 1
	if extra_data:
		if extra_data["revenge"]:
			pvp_disable_revenge(attacker, request)
			is_reply = 0

	# get next available ID
	while str(next_id) in attack_log:
		next_id += 1

	entry = {
		"name": request["name"],
		"level": request["level"],
		"id": request["user_id"],
		"attackWinner": request["winnerId"],
		"reply": is_reply,
		"attackResourcesLost": request["resources"],
		"attackTime": timestamp_now()
	}

	attack_log[str(next_id)] = entry
	player["playerInfo"]["_pvp_alert"] = True

def pvp_disable_revenge(player, request):
	enemy_id = request["attacked_id"]
	attack_log = player["privateState"]["PVPattacksReceived"]
	for eid in attack_log:
		entry = attack_log[eid]
		if entry["id"] == enemy_id:
			entry["reply"] = 1

def player_assist_receive(player, map, building_id):
	building = get_item_from_id(building_id)
	if not building:
		return False

	collect = int(math.floor(int(building["collect"]) * FRIENDS_ASSIST_DIVISOR))
	collect_type = building["collect_type"]

	give_resource_type(player, map, collect_type, collect)
	add_map_currency(map, "xp", FRIENDS_ASSIST_EXPERIENCE)

	return True

def add_resource_trades(traded, res_type, factor):
	if res_type not in traded:
		traded[res_type] = factor
	else:
		traded[res_type] += factor

def get_resource_trades(traded, res_type):
	if res_type not in traded:
		return 0
	return traded[res_type]

def clamp(value, value_min, value_max):
	return max(value_min, min(value_max, value))

def hire_friends(userid, si_info, is_church):
	# nasty import but I don't care
	from sessions import neighbors

	si = []
	if not is_church:
		si.append("0")	# 1 villager for everything except church

	total = len(si)
	num_needed = len(si_info["workers"].split(","))
	friends = neighbors(userid)
	num_friends = len(friends)
	friend_id = 0
	while total < num_needed:
		if friend_id >= num_friends:
			break
		si.append(friends[friend_id]["pid"])
		friend_id += 1
		total += 1

	return si

def event_recruit_friend(player, friend_uid):
	active_events = get_active_events(get_game_config(), timestamp_now())
	for offer_id in active_events:
		offer = get_event_offer(offer_id)
		data = player["privateState"]["viralOffers"][str(offer_id)]

		if len(data["friends"]) >= offer["num_workers"]:
			continue

		if friend_uid in data["friends"]:
			continue

		data["friends"].append(friend_uid)

def buildings_recruit_friend(player, friend_uid):
	for map in player["maps"]:
		for item in map["items"]:
			if "si" in item[7]:
				if item[0] in allies_market_ids:
					if map["resourceAlliesMarket"] == "n":
						continue
				if item[0] == ROUND_TABLE:
					if "sif" not in item[7]:
						continue
					if friend_uid not in item[7]["sif"]:
						continue
				if friend_uid not in item[7]["si"]:
					item[7]["si"].append(friend_uid)

def is_forge_quest(quest_id):
	return str(quest_id) in _forge_quests

def register_bought_unit(player, item_id, town_id = 0):
	item_id = int(item_id)

	race = player["maps"][town_id]["race"]
	ignored_race = "t"
	if race == "t":
		ignored_race = "h"

	data = get_item_from_id(item_id)
	if not data:
		return
	if data["type"] == "b" or data["race"] == ignored_race:
		return
	
	if item_id not in player["privateState"]["boughtUnits"]:
		player["privateState"]["boughtUnits"].append(item_id)

def get_unit_pack_randoms(n = 1):
	randoms = []

	for i in range(n):
		randoms.append([
			random.random(),
			random.random(),
			random.random()
		])

	return randoms

def get_training_cost(item, map):
	cost = int(item["cost"])
	subcat = int(item["subcat_functional"])

	if subcat in blacksmith_discount_subcats:
		if map_has_blacksmith(map):
			cost = int(math.ceil(cost * REDUCTION_MULTIPLIER_BLACKSMITH))
	elif subcat in university_discount_subcats:
		if map_has_university(map):
			cost = int(math.ceil(cost * REDUCTION_MULTIPLIER_UNIVERSITY))
	
	return cost

def map_has_blacksmith(map):
	return len(map_get_items_of_id(map, BUILDING_BLACKSMITH)) > 0

def map_has_university(map):
	return len(map_get_items_of_id(map, BUILDING_UNIVERSITY)) > 0

def get_default_town_id(player, gameversion):
	return 0
	#return max(player["playerInfo"]["default_map"], len(player["maps"]) - 1)

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