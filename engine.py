import time

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

def map_move_item(_map, item_id, x1, y1, x2, y2, orientation):
	items = map_get_item(_map, x1, y1, item_id)
	for item in items:
		item[1] = x2
		item[2] = y2
		item[3] = orientation

def map_orient_item(_map, x, y, orientation):
	items = map_get_item(_map, x, y)
	for item in items:
		item[3] = orientation

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

	name = item["name"]
	print(f"trying to push {name} to graveyard")

	if item_id in resurrectable_items_blocklist:
		print(f"no push, is blacklisted item")
		return False

	if item["race"] in resurrectable_race_blocklist:
		print(f"no push, is blacklisted race")
		return False

	if int(item["subcat_functional"]) in resurrectable_sub_blocklist:
		print(f"no push, is blacklisted subcat_functional")
		return False
	
	if item_id in resurrectable_heroes:
		print(f"yes push, is hero")
		graveyard_set(player, item_id, 1)
		return True

	print(f"yes push, allowed {name}")
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