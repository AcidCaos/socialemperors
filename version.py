import random

from engine import timestamp_now, spaghetti_resurrected_units

version_name = "alpha 0.04"
version_code = "0.04a"

_quest_ids = [
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
	"100000041",
	"100000042",
	"100000043",
	"100000044",
	"100000045",
	"100000046",
	"100000047",
	"100000090",
	"100000091",
	"100000092"
]

_survival_arenas = [
	"100000035",
	"100000036",
	"100000037"
]

# this is in the game client, sorry about that!
# 6 hours * 3 attempts = 18 * 3600
quest_entry_seconds = 6 * 3 * 3600

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
			item[5] = 0
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

	# fixes for maps
	for _map in maps:
		remove_variable(_map, "__#__ITEMS_hint")
		fix_variable(_map, "timestamp", ts_now)
		fix_variable(_map, "questTimes", {})
		fix_variable(_map, "lastQuestTimes", [])

		# make sure very old timestamps are removed
		check_quest_times(_map["lastQuestTimes"], ts_now)

	# darts rng seed if missing
	fix_variable(privateState, "dartsRandomSeed", darts_seed)

	fix_variable(privateState, "arrayAnimals", {})					# fix no animal spawning
	fix_variable(privateState, "strategy", 8)						# fix crash when attacking player
	fix_variable(privateState, "universAttackWin", [])				# pvp current island progress (old game builds)
	fix_variable(privateState, "graveyardCapacity", 10000)			# graveyard cap
	if privateState["graveyardCapacity"] != 10000:
		privateState["graveyardCapacity"] = 10000
	fix_variable(privateState, "potionsReceived", {})				# graveyard potions received
	fix_variable(privateState, "barracksQueues", {})				# unit queues (and soul mixer)
	fix_variable(privateState, "unlockedQuestIndex", 0)				# quest index

	# SP's spaghetti is annoying
	fix_variable(privateState, "deadHeroes", {})					# graveyard old version
	if fix_variable(privateState, "resurrectableUnits", []):		# graveyard new version
		spaghetti_resurrected_units(privateState, privateState["deadHeroes"])

	# survival arena
	fix_variable(privateState, "survivalVidaTimeStamp", [])
	fix_variable(privateState, "survivalVidasExtra", 0)
	fix_variable(privateState, "survivalMaps", {})
	_fix_survival_maps(privateState["survivalMaps"], _survival_arenas)

	# questsRank fix
	fix_variable(privateState, "questsRank", {})
	_fix_quest_ranks(privateState["questsRank"], _quest_ids)

	# team selection window formations
	fix_variable(privateState, "tournamentFormation", 0)

	# pvp shields
	fix_variable(privateState, "shieldEndTime", 0)
	fix_variable(privateState, "shieldCooldown", 0)
	fix_variable(privateState, "purchasedShields", [])

	check_shield_times(privateState, ts_now)

	# gifts convert to dict
	if type(privateState["gifts"]) != dict:
		privateState["gifts"] = array_to_dict(privateState["gifts"], True)

	# remove version tag as it's useless now
	if "version" in save:
		_fix_map_items(maps)
		save.pop("version")

	return True