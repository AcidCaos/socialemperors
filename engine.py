import time
import math

from get_game_config import *
from constants import *

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

# sell divisor (divides by 20 in game for 5% sell value, negative so we refund)
SELL_DIVISOR = -1.0 / 20.0
SPEEDUP_COST_PER_HOUR = 1

def timestamp_now():
	return int(time.time())

def map_add_item(map, item, x, y, orientation = 0, timestamp = None, attr = None, store = None, level = 0):
	if not attr:
		attr = {}
	if not store:
		store = []
	if not timestamp:
		timestamp = timestamp_now()

	# TODO: GET THIS WORKING
	# # properties
	# properties = get_attribute_from_item_id(item, "properties")
	# # enable SI (Socially In Construction), because the game expects it
	# if properties:
	# 	properties = json.loads(properties)
	# 	if "friend_assistable" in properties:
	# 		if int(properties["friend_assistable"]) > 0:
	# 			attr["si"] = []
	# # click to build
	# click_to_build = get_attribute_from_item_id(item, "clicks_to_build")
	# if click_to_build:
	# 	if int(click_to_build) > 0:
	# 		attr["nc"] = 0

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
			if item_id and item[0] == item_id:
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
	for item in items:
		item[1] = x2
		item[2] = y2
		item[3] = orientation

def map_orient_item(map, x, y, orientation):
	items = map_get_item(map, x, y)
	for item in items:
		item[3] = orientation

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

def player_push_queue_unit(player, building, item_id, bq, is_soulmixer):
	attr = building[7]

	if is_soulmixer:
		attr["bq"] = str(bq)
		push_queued_unit(player, bq, item_id, 1)

		return True
	else:
		# TODO: VERIFY
		if "nu" in attr:
			attr["nu"] += 1
		else:
			attr["nu"] = 1
		attr["ts"] = timestamp_now()

		raise Exception("crash please")

def player_speed_up_queue(player, building, bq, new_ts = 0):
	queue = get_unit_queue(player, bq)
	if not queue:
		return False

	is_soulmixer = building[0] == Constant.ID_BUILDING_SOUL_MIXER

	training_key = "training_time" # not sure if correct
	if is_soulmixer:
		training_key = "sm_training_time"
	training_time = get_attribute_from_item_id(queue["unit"], training_key)

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
	queue["amount"] -= 1
	if queue["amount"] <= 0:
		# remove queue
		remove_unit_queue(player, bq)
		del building[7]["bq"]

	return [ unit_id, is_soulmixer ]

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

def push_queued_unit(player, queue_id, unit_id, amount = 1):
	barracksQueues = player["privateState"]["barracksQueues"]
	barracksQueues[str(queue_id)] = {
		"ts":		timestamp_now(),
		"amount":	amount,
		"unit":		unit_id
	}

def add_store_item(player, item, quantity = 1):
	itemstr = str(item)
	if itemstr not in player["privateState"]["gifts"]:
		player["privateState"]["gifts"][itemstr] = quantity
	else:
		player["privateState"]["gifts"][itemstr] += quantity

def remove_store_item(player, item, quantity = 1):
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
		graveyard_set(player, item_id, 1)
		return True

	graveyard_add(player, item_id)
	return True

# I hate SP's cringe implementation, why is there 2 different variables between game versions
# what kind of bullshit system is this!?
def graveyard_set(player, item_id, amount):
	resunits = player["privateState"]["resurrectableUnits"]

	while item_id in resunits:
		resunits.remove(item_id)
	while amount > 0:
		_graveyard_add(player, item_id)

	spaghetti_dead_heroes(player["privateState"], resunits)

def graveyard_add(player, item_id):
	_graveyard_add(player, item_id)

	spaghetti_dead_heroes(player["privateState"], resunits = player["privateState"]["resurrectableUnits"])

def _graveyard_add(player, item_id):
	resunits = player["privateState"]["resurrectableUnits"]

	# respect the damn cap
	if len(resunits) >= player["privateState"]["graveyardCapacity"]:
		return

	resunits.append(item_id)

def graveyard_remove(player, item_id):
	resunits = player["privateState"]["resurrectableUnits"]
	resunits.remove(item_id)

	spaghetti_dead_heroes(player["privateState"], resunits)

def spaghetti_dead_heroes(privateState, resunits):
	# I hate this, I really hate this!
	cringe = {}

	for more_cringe in resunits:
		if str(more_cringe) not in cringe:
			cringe[str(more_cringe)] = 1
		else:
			cringe[str(more_cringe)] += 1

	privateState["deadHeroes"] = cringe

def spaghetti_resurrected_units(privateState, deadunits):
	# even more cringe, amazing
	cringe = []

	for more_cringe in deadunits:
		super_cringe = deadunits[more_cringe]
		while super_cringe > 0:
			cringe.append(int(more_cringe))
			super_cringe -= 1

	privateState["resurrectableUnits"] = cringe

def player_lose_item(player, map, item_id, amount):
	items = map_get_items_of_id(map, item_id)
	while len(items) > 0 and amount > 0:
		try_push_graveyard(player, item_id)
		map["items"].remove(items[0])
		del items[0]
		amount -= 1

def player_fast_forward(player, seconds):
	maps = player["maps"]
	privateState = player["privateState"]

	for map in maps:
		questTimes = map["questTimes"]
		for quest in questTimes:
			modify_ts(questTimes, quest, -seconds)

		lastQuestTimes = map["lastQuestTimes"]
		idx = len(lastQuestTimes) - 1
		while idx >= 0:
			modify_ts_array(lastQuestTimes, idx, -seconds)
			idx -= 1

		# TODO:
		# item timers!

	# TODO:
	# privateState.timestampLastBonus
	# privateState.kompuLastTimeStamp
	# privateState.timeStampHeavySiegePeriod
	# privateState.timeStampHeavySiegeAttack
	# privateState.timeStampDartsReset
	# privateState.timeStampDartsNewFree

	# shields
	modify_ts(privateState, "shieldEndTime", -seconds)
	modify_ts(privateState, "shieldCooldown", -seconds)

	# privateState.survivalVidaTimeStamp
	survivalVidaTimeStamp = privateState["survivalVidaTimeStamp"]
	idx = len(survivalVidaTimeStamp) - 1
	while idx >= 0:
		modify_ts_array(survivalVidaTimeStamp, idx, -seconds)
		idx -= 1

	# privateState.survivalMaps
	survivalMaps = privateState["survivalMaps"]
	for entry in survivalMaps:
		data = survivalMaps[entry]
		modify_ts(data, "ts", -seconds)

	# privateState.barracksQueues
	barracksQueues = privateState["barracksQueues"]
	for queue in barracksQueues:
		q = barracksQueues[queue]
		modify_ts(q, "ts", -seconds)

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

def apply_xp_for_item(map, item_id):
	amount = get_attribute_from_item_id(item_id, "xp")
	if not amount:
		return

	map["xp"] += int(amount)

def apply_cost(playerInfo, map, id, price_multiplier):
	cost = int(price_multiplier * int(get_attribute_from_item_id(id, "cost")))
	cost_type = get_attribute_from_item_id(id, "cost_type")
	if cost_type == "w":
		map["wood"] = max(map["wood"] - cost, 0)
	elif cost_type == "g":
		map["coins"] = max(map["coins"] - cost, 0)
	elif cost_type == "c":
		playerInfo["cash"] = max(playerInfo["cash"] - cost, 0)
	elif cost_type == "s":
		map["stone"] = max(map["stone"] - cost, 0)
	elif cost_type == "f":
		map["food"] = max(map["food"] - cost, 0)

def apply_collect(playerInfo, map, id, resource_multiplier):
	collect = int(resource_multiplier * int(get_attribute_from_item_id(id, "collect")))
	collect_type = get_attribute_from_item_id(id, "collect_type")
	apply_collect_xp(map, id)
	if collect_type == "w":
		map["wood"] = map["wood"] + collect
	elif collect_type == "g":
		map["coins"] = map["coins"] + collect
	elif collect_type == "c":
		playerInfo["cash"] = playerInfo["cash"] + collect
	elif collect_type == "s":
		map["stone"] = map["stone"] + collect
	elif collect_type == "f":
		map["food"] = map["food"] + collect

def apply_collect_xp(map, item_id):
	amount = get_attribute_from_item_id(item_id, "collect_xp")
	if not amount:
		return

	print("applied collext xp for item {str(get_name_from_item_id(item_id))}")

	map["xp"] += int(amount)

def add_cash(player, amount):
	player["playerInfo"]["cash"] += int(amount)

def pay_cash(player, amount):
	if player["playerInfo"]["cash"] < int(amount):
		# not enough cash, stranger...
		return False
	player["playerInfo"]["cash"] -= int(amount)
	return True

def add_map_currency(map, currency, amount):
	map[currency] += int(amount)

def pay_map_currency(map, currency, amount):
	if map[currency] < int(amount):
		return False

	map[currency] -= int(amount)
	return True
	
def add_potions(player, amount = 1):
	player["privateState"]["potion"] += amount

def pay_potions(player, amount):
	if player["privateState"]["potion"] < int(amount):
		return False

	player["privateState"]["potion"] -= int(amount)
	return True

def give_levelup_reward(player, map, level):
	reward_type = level["reward_type"]
	reward_amount = level["reward_amount"]

	give_resource_type(player["playerInfo"], map, reward_type, reward_amount)

def give_resource_type(playerInfo, map, resource, amount):
	if resource == "w":
		map["wood"] += amount
	elif resource == "g":
		map["coins"] += amount
	elif resource == "c":
		playerInfo["cash"] += amount
	elif resource == "s":
		map["stone"] += amount
	elif resource == "f":
		map["food"] += amount

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