import json
import os
import copy
import uuid
import random
from flask import session
# from flask_session import SqlAlchemySessionInterface, current_app

from version import version_code
from engine import timestamp_now
from version import migrate_loaded_save
from constants import Constant

from bundle import VILLAGES_DIR, SAVES_DIR, ENEMIES_DIR

__villages = {}  # ALL static neighbors
__saves = {}  # ALL saved villages

# PVP pool data
__pvp_data = {}
__pvp_pool = []
__pvp_search_result = {}

__initial_village = json.load(open(os.path.join(VILLAGES_DIR, "initial.json")))

# pvp blacklist - arthur
_pvp_pool_blacklist = [ "100000030", "100000031", "100000032" ]

SESSION_SAVE = 0
SESSION_VILLAGE = 1
SESSION_ENEMY = 2

# Load saved villages

def load_saved_villages():
	global __villages
	global __pvp_data
	global __saves
	global __pvp_pool
	global __pvp_search_result
	# Empty in memory
	__villages = {}
	__saves = {}
	__pvp_pool = []

	load_saves(True)
	load_static_villages(True)
	load_enemies(True)

	pvp_pool_size = len(__pvp_pool)
	print(f" [*] PVP pool size: {pvp_pool_size}")

def reload_saves():
	__saves = {}

	# Saves dir check
	if not os.path.exists(SAVES_DIR):
		try:
			print(f"Creating '{SAVES_DIR}' folder...")
			os.mkdir(SAVES_DIR)
		except:
			print(f"Could not create '{SAVES_DIR}' folder.")
			exit(1)
	if not os.path.isdir(SAVES_DIR):
		print(f"'{SAVES_DIR}' is not a folder... Move the file somewhere else.")
		exit(1)
	
	load_saves()

	pvp_pool_size = len(__pvp_pool)
	print(f" [*] PVP pool size: {pvp_pool_size}")

def load_static_villages(add_to_pvp = False):
	# Static neighbors in /villages
	for file in os.listdir(VILLAGES_DIR):
		if file == "initial.json" or not file.endswith(".json"):
			continue
		print(f" * Loading static neighbour {file}... ", end='')
		village = json.load(open(os.path.join(VILLAGES_DIR, file)))
		if not is_valid_village(village):
			print("Invalid neighbour")
			continue
		USERID = village["playerInfo"]["pid"]
		if str(USERID) in __villages:
			print(f"Ignored: duplicated PID '{USERID}'.")
		else:
			__villages[str(USERID)] = village
			if add_to_pvp:
				pvp_pool_add(USERID, village, SESSION_VILLAGE, 0)
			print("Ok.")

def load_saves(add_to_pvp = False):
	# Saves in /saves
	for file in os.listdir(SAVES_DIR):
		if not file.endswith(".save.json"):
			continue
		print(f" * Loading save at {file}... ", end='')
		try:
			save = json.load(open(os.path.join(SAVES_DIR, file)))
		except json.decoder.JSONDecodeError as e:
			print("Corrupted JSON.")
			continue
		if not is_valid_village(save):
			print("Invalid Save.")
			continue
		USERID = save["playerInfo"]["pid"]
		try:
			map_name = save["playerInfo"]["map_names"][ save["playerInfo"]["default_map"] ]
		except:
			map_name = '?'
		print(f"({map_name}) Ok.")
		__saves[str(USERID)] = save
		if add_to_pvp:
			pvp_pool_add(USERID, save, SESSION_SAVE, 0)
		modified = migrate_loaded_save(save) # check save version for migration
		if modified:
			save_session(USERID)

def load_enemies(add_to_pvp = False):
	# Static enemies in /enemy
	print(" * Loading enemies...")
	if not os.path.exists(ENEMIES_DIR):
		os.mkdir(ENEMIES_DIR)

	for file in os.listdir(ENEMIES_DIR):
		if file == "initial.json" or not file.endswith(".json"):
			continue
		# print(f" * Loading static enemy {file}... ", end='')
		try:
			village = json.load(open(os.path.join(ENEMIES_DIR, file)))
		except json.decoder.JSONDecodeError as e:
			print(f"Corrupt enemy {file}")
			continue
		if not is_valid_village(village):
			print(f"Invalid enemy {file}")
			continue
		USERID = village["playerInfo"]["pid"]
		if str(USERID) in __pvp_data:
			print(f"Ignored: duplicated enemy PID '{USERID}'.")
		else:
			# migrate pvp save
			if "version" in village:
				print(f"migrating enemy file for {USERID}...")
				migrate_loaded_save(village)
				with open(os.path.join(ENEMIES_DIR, file), 'w') as f:
					json.dump(village, f, indent='\t')

			if add_to_pvp:
				pvp_pool_add(USERID, village, SESSION_ENEMY, 0)

def get_enemy_save(userid):
	path = os.path.join(ENEMIES_DIR, userid)
	if os.path.exists(path + ".save.json"):
		return json.load(open(path + ".save.json"))
	if os.path.exists(path + ".json"):
		return json.load(open(path + ".json"))
	return None

# New village
def new_village():
	# Generate USERID
	USERID: str = str(uuid.uuid4())
	assert USERID not in all_userid()
	# Copy init
	village = copy.deepcopy(__initial_village)
	# Custom values
	village["version"] = "migrateme"
	village["playerInfo"]["pid"] = USERID
	village["maps"][0]["timestamp"] = timestamp_now()
	village["privateState"]["dartsRandomSeed"] = abs(int((2**16 - 1) * random.random()))
	# fix stuff
	migrate_loaded_save(village)
	# Memory saves
	__saves[USERID] = village
	pvp_pool_add(USERID, village, SESSION_SAVE, 0)
	# Generate save file
	save_session(USERID)
	print("Done.")
	return USERID

# Access functions
def pvp_pool_add(userid, village, session_type, town_id = 0):
	if not pvp_pool_allowed(userid, village, town_id):
		return

	__pvp_data[userid] = pvp_data(village, session_type, town_id)
	if "userid" not in __pvp_pool:
		__pvp_pool.append(userid)

def pvp_pool_allowed(userid, village, town_id = 0):
	# pvp not allowed until level 8
	if village["maps"][town_id]["level"] < 8:
		return False
	# pvp not allowed for these saves
	if userid in _pvp_pool_blacklist:
		return False

	return True

# set pvp enemy search result for this user
def set_pvp_enemy_for(userid, enemyid):
	if not enemyid:
		del __pvp_search_result[userid]
		return

	__pvp_search_result[userid] = enemyid

# get search result
def get_pvp_enemy_for(userid):
	if userid not in __pvp_search_result:
		return None

	enemyid = __pvp_search_result[userid]
	del __pvp_search_result[userid]
	return enemyid

# get random pvp enemy
def pvp_enemy(my_userid, town_id):
	me = session(my_userid)
	level = me["maps"][town_id]["level"]
	ts_now = timestamp_now()

	# search favors players around your level
	# if pvp shield is on, the enemy is skipped

	range_min = level - 5
	range_max = level + 5
	retries = 0
	retries_level = 0
	while retries < 1000:
		if retries_level > 50:
			retries_level = 0
			range_min -= 5
			range_max += 5

		retries += 1
		retries_level += 1

		user = random.choice(__pvp_pool)
		if user == my_userid:
			continue

		data = __pvp_data[user]

		# check if shield is on and level is in range
		if ts_now < data["shield"]:
			continue
		if data["level"] < range_min or data["level"] > range_max:
			continue

		print(json.dumps(data, indent="\t"))

		# TODO: try and match similar level
		print(f"PVP enemy found after {retries} retries: {user}")
		return user

	print("No enemy found! :(")
	return None

def pvp_data(player, session_type, town_id = 0):
	data = {
		"level": player["maps"][town_id]["level"],
		"shield": player["privateState"]["shieldEndTime"],
		"type": session_type,
	}
	return data

def get_pvp_session(userid):
	if userid in __pvp_data:
		data = __pvp_data[userid]
		session_type = data["type"]
		if session_type == SESSION_ENEMY:
			return get_enemy_save(userid)
		elif session_type == SESSION_VILLAGE:
			return __villages[userid]
		else:
			return __saves[userid]

	return None

def all_saves_userid() -> list:
	"Returns a list of the USERID of every saved village."
	return list(__saves.keys())

def all_userid() -> list:
	"Returns a list of the USERID of every village."
	return list(__villages.keys()) + list(__saves.keys())

def save_info(USERID: str) -> dict:
	save = __saves[USERID]
	migrate_loaded_save(save)
	default_map = int(save["playerInfo"]["default_map"])
	empire_name = str(save["playerInfo"]["map_names"][default_map])
	xp = save["maps"][default_map]["xp"]
	level = save["maps"][default_map]["level"]
	return{"userid": USERID, "name": empire_name, "xp": xp, "level": level}

def all_saves_info() -> list:
	saves_info = []
	for userid in __saves:
		saves_info.append(save_info(userid))
	return list(saves_info)

def session(USERID: str) -> dict:
	assert(isinstance(USERID, str))
	return __saves[USERID] if USERID in __saves else None

def neighbor_session(USERID: str) -> dict:
	assert(isinstance(USERID, str))
	if USERID in __pvp_data:
		return __pvp_data[USERID]
	if USERID in __saves:
		return __saves[USERID]
	if USERID in __villages:
		return __villages[USERID]

def fb_friends_str(USERID: str) -> list:
	DELETE_ME = [{"uid": "1111", "pic_square":"http://127.0.0.1:5050/img/profile/Paladin_Justiciero.jpg"},
		{"uid": "aa_002", "pic_square":"/1025.png"}]
	friends = []
	# static villages
	for key in __villages:
		vill = __villages[key]
		# Avoid Arthur being loaded as friend.
		if vill["playerInfo"]["pid"] == Constant.NEIGHBOUR_ARTHUR_GUINEVERE_1 \
		or vill["playerInfo"]["pid"] == Constant.NEIGHBOUR_ARTHUR_GUINEVERE_2 \
		or vill["playerInfo"]["pid"] == Constant.NEIGHBOUR_ARTHUR_GUINEVERE_3:
			continue
		frie = {}
		frie["uid"] = vill["playerInfo"]["pid"]
		frie["pic_square"] = vill["playerInfo"]["pic"]
		if not frie["pic_square"]: frie["pic_square"] = "/img/profile/1025.png"
		friends += [frie]
	# other players
	for key in __saves:
		vill = __saves[key]
		if vill["playerInfo"]["pid"] == USERID:
			continue
		frie = {}
		frie["uid"] = vill["playerInfo"]["pid"]
		frie["pic_square"] = vill["playerInfo"]["pic"]
		if not frie["pic_square"]: frie["pic_square"] = "/img/profile/1025.png"
		friends += [frie]
	return friends

def neighbors(USERID: str) -> list:
	neighbors = []
	# static villages
	for key in __villages:
		vill = __villages[key]
		# Avoid Arthur being loaded as multiple neigtbors.
		if vill["playerInfo"]["pid"] == Constant.NEIGHBOUR_ARTHUR_GUINEVERE_1 \
		or vill["playerInfo"]["pid"] == Constant.NEIGHBOUR_ARTHUR_GUINEVERE_2 \
		or vill["playerInfo"]["pid"] == Constant.NEIGHBOUR_ARTHUR_GUINEVERE_3:
			continue
		neigh = vill["playerInfo"]
		neigh["coins"] = vill["maps"][0]["coins"]
		neigh["xp"] = vill["maps"][0]["xp"]
		neigh["level"] = vill["maps"][0]["level"]
		neigh["stone"] = vill["maps"][0]["stone"]
		neigh["wood"] = vill["maps"][0]["wood"]
		neigh["food"] = vill["maps"][0]["food"]
		neigh["stone"] = vill["maps"][0]["stone"]
		neighbors += [neigh]
	# other players
	for key in __saves:
		vill = __saves[key]
		if vill["playerInfo"]["pid"] == USERID:
			continue
		neigh = vill["playerInfo"]
		neigh["coins"] = vill["maps"][0]["coins"]
		neigh["xp"] = vill["maps"][0]["xp"]
		neigh["level"] = vill["maps"][0]["level"]
		neigh["stone"] = vill["maps"][0]["stone"]
		neigh["wood"] = vill["maps"][0]["wood"]
		neigh["food"] = vill["maps"][0]["food"]
		neigh["stone"] = vill["maps"][0]["stone"]
		neighbors += [neigh]
	return neighbors

# Check for valid village
# The reason why this was implemented is to warn the user if a save game from Social Wars was used by accident

def is_valid_village(save: dict):
	if "playerInfo" not in save or "maps" not in save or "privateState" not in save:
		# These are obvious
		return False
	for map in save["maps"]:
		if "oil" in map or "steel" in map:
			return False
		if "stone" not in map or "food" not in map:
			return False
		if "items" not in map:
			return False
		if type(map["items"]) != list:
			return False

	return True

# Persistency

def backup_session(USERID: str):
	# TODO 
	return

def save_session(USERID: str):
	# TODO 
	file = f"{USERID}.save.json"
	village = session(USERID)
	with open(os.path.join(SAVES_DIR, file), 'w') as f:
		json.dump(village, f, indent='\t')