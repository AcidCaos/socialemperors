import random
import logging

log = logging.getLogger('__main__')

# grab server settings
from server_config import get_server_config

from engine import timestamp_now, spaghetti_resurrected_units, hire_friends
from get_game_config import *

version_name = "nerroth rewrite - beyond 0.04a"
version_code = ""

quest_ids = [
	"100000006",
	"100000007",
	"100000008",
	"100000012",
	"100000002",
	"100000021",
	"100000022",
	"100000003",
	"100000027",
	"100000028",
	"100000014",
	"100000013",
	"100000020",
	"100000015",
	"100000023",
	"100000019",
	"100000018",
	"100000011",
	"100000033",
	"100000040",	# arena
	"100000041",
	"100000042",
	"100000043",
	"100000044",
	"100000045",
	"100000046",
	"100000047",
	"100000051",	# forge island
	"100000052",
	"100000053",
	"100000054",
	"100000055",
	"100000090",	# gods
	"100000091",
	"100000092",
]

survival_arenas = [
	"100000035",
	"100000036",
	"100000037"
]

quest_entry_seconds = int(get_server_config()["misc"]["quests_reset_hours"] * 3600)

_warehouse_default_cap = int(get_game_config()["globals"]["WAREHOUSE_CAPACITIES"][0])
_market_reset_time = 3600 * 20

def remove_variable(dictionary, key):
	if key in dictionary:
		del dictionary[key]
		return True
	return False

def fix_variable(dictionary, key, expected):
	if key not in dictionary:
		dictionary[key] = expected
		return True
	elif dictionary[key] == None:
		dictionary[key] = expected
		return True
	elif type(dictionary[key]) != type(expected):
		dictionary[key] = expected
		return True
	return False

def fix_variable_array(arr, idx, expected):
	if idx >= len(arr):
		while idx >= len(arr):
			arr.append(None)
		arr[idx] = expected
		return True
	elif arr[idx] == None:
		arr[idx] = expected
		return True
	elif type(arr[idx]) != type(expected):
		arr[idx] = expected
		return True
	return False

def _fix_quest_ranks(ranks, quests):
	for quest in quests:
		if quest not in ranks:
			ranks[quest] = None

def _fix_survival_maps(maps, arenas):
	for arena in arenas:
		if arena not in maps:
			maps[arena] = { "ts": 0, "tp": 0 }

def _fix_map_items(maps):
	ts_now = timestamp_now()
	for map in maps:
		items = map["items"]
		for item in items:
			item[4] = ts_now
			fix_variable_array(item, 5, 0)
			fix_variable_array(item, 6, [])
			fix_variable_array(item, 7, {})

def array_to_dict(items, remove_zero = False):
	fixed = {}

	idx = 0
	for item in items:
		if remove_zero:
			if item != 0:
				fixed[str(idx)] = item
		else:
			fixed[str(idx)] = item
		idx += 1

	return fixed

def check_quest_times(times, ts_now):
	# removes any quest timestamps after X hours passed
	idx = 0
	num = len(times)
	while idx < num:
		if abs(ts_now - times[idx]) > quest_entry_seconds:
			del times[idx]
			idx -= 1
			num -= 1
		idx += 1

def check_shield_times(privateState, ts_now):
	if ts_now >= privateState["shieldCooldown"]:
		privateState["shieldCooldown"] = 0
		privateState["purchasedShields"] = []

def fix_collections(privateState):
	cols = [ [] ]	# ELEMENT 0 MUST BE EMPTY OR THE GAME BREAKS, DON'T ASK ME WHY, SP CAN'T CODE!!!
	idx = 0
	while idx < 23:
		cols.append([ 0, 0, 0, 0, 0, 0 ]) # completed, item_count_1, ..., item_count_5
		idx += 1
	privateState["collections"] = cols

def fix_collections_completed(privateState):
	collections = privateState["collections"]
	finished = privateState["collectionsCompleted"]

	idx = 1
	while idx <= 23:
		if collections[idx][0]:
			if idx not in finished:
				finished.append(idx)
		idx += 1

def _fix_bought_unit(collection, item_id, ignored_race):
	item_id = int(item_id)
	data = get_item_from_id(item_id)
	if not data:
		return
	if data["type"] == "b" or data["race"] == ignored_race:
		return
	if item_id not in collection:
		collection.append(item_id)

def fix_bought_units(maps, privateState):
	collection = []
	ignored_race = "t"

	# MAPS
	for map in maps:
		race = map["race"]

		# race check
		ignored_race = "t"
		if race == "t":
			ignored_race == "h"

		# items:
		for item in map["items"]:
			_fix_bought_unit(collection, item[0], ignored_race)
			# building item slots
			for item_id in item[6]:
				_fix_bought_unit(collection, item_id, ignored_race)
		# item storage
		for item_id in map["store"]:
			_fix_bought_unit(collection, item_id, ignored_race)
		# warehouse
		for item_id in map["warehousedUnits"]:
			_fix_bought_unit(collection, item_id, ignored_race)

	# PRIVATE STATE
	# gifts
	for item_id in privateState["gifts"]:
		_fix_bought_unit(collection, item_id, "")
	# graveyard
	for item_id in privateState["deadHeroes"]:
		_fix_bought_unit(collection, item_id, "")

	privateState["boughtUnits"] = collection

def _fix_level_mana(map, privateState):
	# applies fix for mana not being gained after specific level
	cfg_globals = get_game_config()["globals"]
	gain = int(max(0, 1 + min(100, map["level"]) - cfg_globals["START_LEVEL_MANA_REWARD"]) * cfg_globals["MANA_REWARD_PER_LEVEL"])
	if gain > 0:
		privateState["mana"] += gain

def _fix_hellforge():
	idx = 1
	collect_game = {}
	while idx <= 6:
		collect_game[str(idx)] = {
			"id": idx,
			"counter": 0,
			"timestamp": 0
		}
		idx += 1
	return collect_game

def _fix_events():
	idx = 1
	events = {}
	while idx <= 5:
		events[str(idx)] = {
			"id": idx,
			"friends": [],
			"rewarded": []
		}
		idx += 1
	return events

def migrate_loaded_save(save):
	# Migration always happens now, we check the data type this time and insert any new data if necessary
	# This should make sure the save file isn't "half fixed"

	playerInfo = save["playerInfo"]
	privateState = save["privateState"]
	maps = save["maps"]
	ts_now = timestamp_now()
	darts_seed = abs(int((2**16 - 1) * random.random()))

	# whoops, these go into maps
	remove_variable(privateState, "questTimes")
	remove_variable(privateState, "lastQuestTimes")

	# player avatar
	fix_variable(playerInfo, "pic", "")

	remove_variable(playerInfo, "__#__coins")
	remove_variable(playerInfo, "__#__xp")
	remove_variable(playerInfo, "__#__level")
	# neighbor mistake cleanup
	remove_variable(playerInfo, "coins")
	remove_variable(playerInfo, "xp")
	remove_variable(playerInfo, "level")
	remove_variable(playerInfo, "stone")
	remove_variable(playerInfo, "wood")
	remove_variable(playerInfo, "food")

	# fixes for maps
	for _map in maps:
		remove_variable(_map, "__#__ITEMS_hint")
		fix_variable(_map, "timestamp", ts_now)
		fix_variable(_map, "questTimes", {})
		fix_variable(_map, "lastQuestTimes", [])
		fix_variable(_map, "warehouseAditionalCapacitySingle", _warehouse_default_cap)
		fix_variable(_map, "warehousedUnits", {})
		fix_variable(_map, "timestampLastTrade", 0)
		fix_variable(_map, "numTradesDone", 0)
		fix_variable(_map, "store", {})

	# darts rng seed if missing
	fix_variable(privateState, "dartsRandomSeed", darts_seed)

	fix_variable(privateState, "arrayAnimals", {})					# fix no animal spawning
	fix_variable(privateState, "strategy", 8)						# fix crash when attacking player
	fix_variable(privateState, "universAttackWin", [])				# pvp current island progress (old game builds)
	
	graveyard_cap = get_server_config()["misc"]["graveyard_max_slots"]
	fix_variable(privateState, "graveyardCapacity", graveyard_cap)			# graveyard cap
	if privateState["graveyardCapacity"] != graveyard_cap:
		privateState["graveyardCapacity"] = graveyard_cap
	fix_variable(privateState, "potionsReceived", {})				# graveyard potions received
	fix_variable(privateState, "barracksQueues", {})				# unit queues (and soul mixer)
	fix_variable(privateState, "unlockedQuestIndex", 0)				# quest index
	fix_variable(privateState, "PVPattacksReceived", {})			# PVP attack log
	fix_variable(privateState, "unlockedSkins", {})					# weather machine
	fix_variable(privateState, "countTimePacket", [])				# time machine
	if len(privateState["countTimePacket"]) < 6:
		privateState["countTimePacket"] = [ 0, 0, 0, 0, 0, 0 ]
	fix_variable(privateState, "helpMap", [])						# shown help pages
	fix_variable(privateState, "unitPacks", {})						# unit packs
	fix_variable(privateState, "teams", {})							# teams
	fix_variable(privateState["teams"], "tournament", [
		0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
		0, 0, 0, 0, 0, 0, 0, 0, 0, 0
	])
	fix_variable(privateState, "neighborAssists", {})				# neighbour assists
	fix_variable(privateState, "templeStep", [])					# supreme bahamut
	fix_variable(privateState, "timeStampTemple", 0)

	# item collections
	if fix_variable(privateState, "collections", []):
		fix_collections(privateState)

	fix_variable(privateState, "collectionsCompleted", [])
	if len(privateState["collectionsCompleted"]) == 0:
		fix_collections_completed(privateState)						# oopsie daisy

	# SP's spaghetti is annoying
	fix_variable(privateState, "deadHeroes", {})					# graveyard old version
	if fix_variable(privateState, "resurrectableUnits", []):		# graveyard new version
		spaghetti_resurrected_units(privateState, privateState["deadHeroes"])

	# survival arena
	fix_variable(privateState, "survivalVidaTimeStamp", [])
	fix_variable(privateState, "survivalVidasExtra", 0)
	fix_variable(privateState, "survivalMaps", {})
	_fix_survival_maps(privateState["survivalMaps"], survival_arenas)

	# questsRank fix
	fix_variable(privateState, "questsRank", {})
	_fix_quest_ranks(privateState["questsRank"], quest_ids)

	# goals fix
	fix_variable(privateState, "completedMissions", [])
	fix_variable(privateState, "rewardedMissions", [])

	# team selection window formations
	fix_variable(privateState, "tournamentFormation", 0)

	# pvp shields
	fix_variable(privateState, "shieldEndTime", 0)
	fix_variable(privateState, "shieldCooldown", 0)
	fix_variable(privateState, "purchasedShields", [])

	# player profile info
	fix_variable(playerInfo, "country", "Social World")
	fix_variable(playerInfo, "attacks_won", 0)
	fix_variable(playerInfo, "attacks_lost", 0)
	fix_variable(playerInfo, "honor_points", 0)

	check_shield_times(privateState, ts_now)

	# item storage
	if type(privateState["gifts"]) != dict:
		privateState["gifts"] = array_to_dict(privateState["gifts"], True)
	fix_variable(privateState, "iphoneBox", {})

	# unit collections
	if fix_variable(privateState, "boughtUnits", []):
		fix_bought_units(maps, privateState)
	elif len(privateState["boughtUnits"]) == 0:
		fix_bought_units(maps, privateState)
	fix_variable(privateState, "unitCollectionsCompleted", [])

	# events
	fix_variable(privateState, "viralOffers", {})
	if len(privateState["viralOffers"]) != 5:
		privateState["viralOffers"] = _fix_events()

	# island forge
	fix_variable(privateState, "collectGame", {})
	if len(privateState["collectGame"]) != 6:
		privateState["collectGame"] = _fix_hellforge()
	fix_variable(privateState, "collectGameGivenPrizes", {})

	# remove version tag as it's useless now
	if "version" in save:
		_fix_map_items(maps)
		_fix_level_mana(maps[0], privateState)
		privateState["monsterNestActive"] = 1
		save.pop("version")

	return True

def save_reset_stuff(save, player_visiting_own_save = False):
	# This function performs some resets in save whenever the game loads the map
	if player_visiting_own_save:
		# Resets market trades
		now = timestamp_now()
		for map in save["maps"]:
			last_trade = map["timestampLastTrade"]
			if abs(now - last_trade) >= _market_reset_time:
				map["numTradesDone"] = 0
				map["resourcesTraded"] = {}

		# Reset targets if start of a new week, game will call darts_reset if timestamp is 0
		privateState = save["privateState"]
		if "timeStampDartsReset" in privateState:
			# take away 3 days since timestamp 0 is thursday, we want reset to happen on monday
			# 3 days = 259200 seconds
			last_darts_reset = privateState["timeStampDartsReset"] + 259200
			temp = now + 259200
			if temp // 604800 != last_darts_reset // 604800:
				privateState["timeStampDartsReset"] = 0

		check_quest_times(map["lastQuestTimes"], now)
		check_animals(save)
		check_si_buildings(save)

def check_si_buildings(save):
	userid = save["playerInfo"]["pid"]
	for map in save["maps"]:
		for item in map["items"]:
			if "si" in item[7]:
				_check_si(userid, item)

def _check_si(userid, item):
	si_info = get_si_info(item[0])
	if not si_info:
		return

	item[7]["si"] = hire_friends(userid, si_info, item[0] == 470)

def check_animals(save):
	animal_data = get_animals()
	animal_counters = {}
	for key in animal_data:
		animal_counters[key] = 0
	for map in save["maps"]:
		for item in map["items"]:
			item_id = item[0]
			stored = item[6]
			for key in animal_data:
				if item_id in animal_data[key]:
					animal_counters[key] += 1
					break
			for item_id in stored:
				for key in animal_data:
					if item_id in animal_data[key]:
						animal_counters[key] += 1
						break

	save["privateState"]["arrayAnimals"] = animal_counters