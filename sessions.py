import json
import os
import copy
import shutil
import uuid
import random
from flask import session
# from flask_session import SqlAlchemySessionInterface, current_app

from version import version_code
from engine import *
from version import migrate_loaded_save
from constants import Constant

from bundle import VILLAGES_DIR, SAVES_DIR, ENEMIES_DIR, FRIENDS_DIR

__villages = {}  # ALL static neighbors (excluding friend/ and enemy/)
__saves = {}  # ALL saved villages

# friend info
__friend_info = {}

# PVP ---------------------------------------------------------------------------
# PVP SEARCH SETTINGS
_PVP_SEARCH_MAX_RETRIES = 2200
_PVP_SEARCH_RETRIES_BEFORE_EXPAND = 200
_PVP_SEARCH_LEVEL_RANGE = 10 # -that, +that

# Any saves under this are excluded from search
# This is because PVP unlocks at level 8 in the game client
_PVP_MIN_LEVEL = 8 

# How long the PVP Shield will be enabled on the player you attack
# after finishing the attack. Set to 0 to disable, default is 12h (0.5 days)
_PVP_SHIELD_AFTER_ATTACK = int(0.5 * 86400)

# PVP pool data
__pvp_data = {}
__pvp_pool = []
__pvp_search_result = {}
__pvp_active_data = {}

# PVP blacklist - arthur maps
_pvp_pool_blacklist = [ "100000030", "100000031", "100000032" ]
# -------------------------------------------------------------------------------

__initial_village = json.load(open(os.path.join(VILLAGES_DIR, "initial.json")))


SESSION_SAVE = 0		# player save
SESSION_VILLAGE = 1		# arthur
SESSION_ENEMY = 2		# enemy folder 
SESSION_FRIEND = 3		# friend folder

# Intially load saved villages
def load_saved_villages():
	global __villages
	global __saves
	global __friend_info

	global __pvp_data
	global __pvp_pool
	global __pvp_search_result
	global __pvp_active_data

	check_saves()
	load_saves(True)
	load_static_villages(True)
	copy_static_friends()
	load_friends(True)
	load_enemies(True)

	pvp_pool_size = len(__pvp_pool)
	print(f" [*] PVP pool size: {pvp_pool_size}")

def check_saves():
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

def reload_saves():
	__saves = {}

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

def copy_static_friends():
	# Copy from villages/friend_static to /friend if it's not there!
	if not os.path.exists(FRIENDS_DIR):
		os.mkdir(FRIENDS_DIR)

	path1 = VILLAGES_DIR + "/friend_static/"
	for file in os.listdir(path1):
		dest = os.path.join(FRIENDS_DIR, file)
		if os.path.exists(dest):
			continue

		shutil.copy(os.path.join(path1, file), dest)

def load_friends(add_to_pvp = False):
	# Friends in /friend
	print(" * Loading friends...")
	if not os.path.exists(FRIENDS_DIR):
		os.mkdir(FRIENDS_DIR)

	for file in os.listdir(FRIENDS_DIR):
		if file == "initial.json" or not file.endswith(".json"):
			continue
		# print(f" * Loading static enemy {file}... ", end='')
		try:
			village = json.load(open(os.path.join(FRIENDS_DIR, file)))
		except json.decoder.JSONDecodeError as e:
			print(f"Corrupt friends {file}")
			continue
		if not is_valid_village(village):
			print(f"Invalid friends {file}")
			continue
		USERID = village["playerInfo"]["pid"]
		if str(USERID) in __pvp_data:
			print(f"Ignored: duplicated friends PID '{USERID}'.")
		else:
			# migrate pvp save
			if "version" in village:
				print(f"migrating friends file for {USERID}...")
				migrate_loaded_save(village)
				with open(os.path.join(FRIENDS_DIR, file), 'w') as f:
					json.dump(village, f, indent='\t')

			__friend_info[USERID] = neighbor_data(village)
			if add_to_pvp:
				pvp_pool_add(USERID, village, SESSION_FRIEND, 0)

def load_enemies(add_to_pvp = False):
	# Enemies in /enemy
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

def get_friend_save(userid):
	path = os.path.join(FRIENDS_DIR, userid)
	data = None
	if os.path.exists(path + ".save.json"):
		data = json.load(open(path + ".save.json"))
	if os.path.exists(path + ".json"):
		data = json.load(open(path + ".json"))
	if data:
		migrate_loaded_save(data)
	return data

def get_enemy_save(userid):
	path = os.path.join(ENEMIES_DIR, userid)
	data = None
	if os.path.exists(path + ".save.json"):
		data = json.load(open(path + ".save.json"))
	if os.path.exists(path + ".json"):
		data = json.load(open(path + ".json"))
	if data:
		migrate_loaded_save(data)
	return data

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

# modifies stored PVP data for player
def pvp_pool_modify(player, town_id = 0):
	userid = player["playerInfo"]["pid"]
	if not pvp_pool_allowed(userid, player, town_id):
		return

	pvp_data_update(userid, player, town_id)

def pvp_pool_allowed(userid, village, town_id = 0):
	# pvp not allowed for these saves
	if userid in _pvp_pool_blacklist:
		return False

	return True

# set pvp attack begin/end state
def pvp_begin_attack(request, is_revenge = False):
	userid = request["user_id"]
	__pvp_active_data[userid] ={
		"revenge": is_revenge,
		"target": request["attacked_id"]
	}

def pvp_end_attack(userid):
	if userid not in __pvp_active_data:
		return None

	data = __pvp_active_data[userid]
	del __pvp_active_data[userid]
	return data

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

	range_min = max(_PVP_MIN_LEVEL, level - _PVP_SEARCH_LEVEL_RANGE)
	range_max = level + _PVP_SEARCH_LEVEL_RANGE
	retries = 0
	retries_level = 0
	while retries < _PVP_SEARCH_MAX_RETRIES:
		if retries_level >= _PVP_SEARCH_RETRIES_BEFORE_EXPAND:
			retries_level = 0
			range_min = max(8, range_min - _PVP_SEARCH_LEVEL_RANGE)
			range_max += _PVP_SEARCH_LEVEL_RANGE

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

		# print(json.dumps(data, indent="\t"))

		print(f"PVP enemy found after {retries} retries: {user}")
		return user

	print("No enemy found! :(")
	return None

def pvp_simulate_resources(save, userid, town_id = 0):
	pool_data = get_pvp_data(userid)
	if pool_data:
		session_type = pool_data["type"]

	# if in friend/ or enemy/, simulate resources being lost and gained over time
	if session_type == SESSION_FRIEND or session_type == SESSION_ENEMY:
		hours = int((timestamp_now() - save["privateState"]["shieldEndTime"]) / 3600)
		#print(f"hours since last shield: {hours}")
		res_multiplier = min(1.0, max(0.125, float(hours) / (24 * 2)))	# 2 days to recharge
		#print(f"res_multiplier = {res_multiplier}")
		_map = save["maps"][town_id]

		# this does not modify the save, it's just client side
		_map["coins"] = max(0, int(_map["coins"] * res_multiplier))
		_map["food"] = max(0, int(_map["food"] * res_multiplier))
		_map["wood"] = max(0, int(_map["wood"] * res_multiplier))
		_map["stone"] = max(0, int(_map["stone"] * res_multiplier))

def pvp_data(player, session_type, town_id = 0):
	data = {
		"level": player["maps"][town_id]["level"],
		"shield": player["privateState"]["shieldEndTime"],
		"type": session_type,
	}
	return data

def get_pvp_data(userid):
	if userid in __pvp_pool:
		return __pvp_data[userid]
	return None

def pvp_data_update(userid, player, town_id = 0):
	data = __pvp_data[userid]
	data["level"] = player["maps"][town_id]["level"]
	data["shield"] = player["privateState"]["shieldEndTime"]

def pvp_modify_victim(request, town_id = 0):
	userid = request["attacked_id"]
	resources = request["resources"]

	if userid not in __pvp_data:
		return
	data = __pvp_data[userid]
	session_type = data["type"]

	save = get_target_session(userid)
	if not save:
		return

	stealing_allowed = False

	if session_type == SESSION_VILLAGE:		# not allowed for static!
		return
	if session_type == SESSION_SAVE:
		stealing_allowed = True

	ts_now = timestamp_now()

	# grab some extra data
	extra = pvp_end_attack(request["user_id"])

	# give PVP shield to victim
	save["privateState"]["shieldEndTime"] = int(ts_now + _PVP_SHIELD_AFTER_ATTACK)

	# steal resources if allowed (saves only)
	if stealing_allowed:
		pvp_steal_resources(save, town_id, resources)

	# update pool data
	pvp_pool_modify(save, town_id)

	# update attack log
	pvp_push_attack_log(save, request, extra, get_target_session(request["user_id"]))

	save_target_session(userid, save, session_type)

def get_pvp_session(userid):
	if userid in __pvp_data:
		data = __pvp_data[userid]
		session_type = data["type"]
		if session_type == SESSION_ENEMY:
			return get_enemy_save(userid)
		elif session_type == SESSION_FRIEND:
			return get_friend_save(userid)
		elif session_type == SESSION_VILLAGE:
			return __villages[userid]
		else:
			return __saves[userid]

	return None

def get_target_session(userid):
	result = get_pvp_session(userid)
	if not result:
		if userid in __villages:
			result = __villages[userid]
		elif userid in __saves:
			result = __saves[userid]
	return result

def get_target_path(session_type):
	if session_type == SESSION_SAVE:
		return SAVES_DIR
	if session_type == SESSION_ENEMY:
		return ENEMIES_DIR
	if session_type == SESSION_FRIEND:
		return FRIENDS_DIR

	# not allowed for static!
	return None	

def save_target_session(userid, save, session_type):
	path = get_target_path(session_type)
	if not path:
		return

	save_session_path(userid, save, path)

def all_saves_userid():
	"Returns a list of the USERID of every saved village."
	return list(__saves.keys())

def all_userid():
	"Returns a list of the USERID of every village."
	return list(__villages.keys()) + list(__saves.keys())

def save_info(USERID: str):
	save = __saves[USERID]
	migrate_loaded_save(save)
	default_map = int(save["playerInfo"]["default_map"])
	empire_name = str(save["playerInfo"]["map_names"][default_map])
	xp = save["maps"][default_map]["xp"]
	level = save["maps"][default_map]["level"]
	return{"userid": USERID, "name": empire_name, "xp": xp, "level": level}

def all_saves_info():
	saves_info = []
	for userid in __saves:
		saves_info.append(save_info(userid))
	return list(saves_info)

def session(USERID: str):
	assert(isinstance(USERID, str))
	return __saves[USERID] if USERID in __saves else None

def neighbor_session(USERID: str):
	assert(isinstance(USERID, str))
	if USERID in __pvp_data:
		return __pvp_data[USERID]
	if USERID in __saves:
		return __saves[USERID]
	if USERID in __villages:
		return __villages[USERID]

def fb_friends_str(USERID: str):
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
		frie["first_name"] = vill["playerInfo"]["name"]
		frie["name"] = vill["playerInfo"]["name"]
		frie["pic_square"] = vill["playerInfo"]["pic"]
		if not frie["pic_square"]: frie["pic_square"] = "/img/profile/1025.png"
		friends += [frie]
	# Friends
	for key in __friend_info:
		f = __friend_info[key]
		friends += [{
			"uid": f["pid"],
			"pic_square": f["pic"],	# not gonna work in SI, it loads from graph.facebook.com!
			"name": f["name"],
			"first_name": f["first_name"],
		}]
	# other players
	for key in __saves:
		vill = __saves[key]
		if vill["playerInfo"]["pid"] == USERID:
			continue
		frie = {}
		frie["uid"] = vill["playerInfo"]["pid"]
		frie["first_name"] = vill["playerInfo"]["name"]
		frie["pic_square"] = vill["playerInfo"]["pic"]
		frie["name"] = vill["playerInfo"]["name"]
		if not frie["pic_square"]: frie["pic_square"] = "/img/profile/1025.png"
		friends += [frie]

	return friends

def neighbors(USERID):
	neighbors = []
	# static villages
	for key in __villages:
		vill = __villages[key]
		# Avoid Arthur being loaded as multiple neigtbors.
		if vill["playerInfo"]["pid"] == Constant.NEIGHBOUR_ARTHUR_GUINEVERE_1 \
		or vill["playerInfo"]["pid"] == Constant.NEIGHBOUR_ARTHUR_GUINEVERE_2 \
		or vill["playerInfo"]["pid"] == Constant.NEIGHBOUR_ARTHUR_GUINEVERE_3:
			continue
		
		neighbors += [neighbor_data(vill, 0)]
	# friends
	for key in __friend_info:
		neighbors += [__friend_info[key]]
	# other players
	for key in __saves:
		vill = __saves[key]
		if vill["playerInfo"]["pid"] == USERID:
			continue
		neighbors += [neighbor_data(vill, 0)]
	return neighbors

def neighbor_data(player, town_id = 0):
	_map = player["maps"][town_id]

	info = copy.deepcopy(player["playerInfo"])
	info["coins"] = _map["coins"]
	info["xp"] = _map["xp"]
	info["level"] = _map["level"]
	info["stone"] = _map["stone"]
	info["wood"] = _map["wood"]
	info["food"] = _map["food"]
	info["stone"] = _map["stone"]
	info["uid"] = info["pid"]
	info["pic_square"] = info["pic"]
	info["first_name"] = info["name"]
	info["name"] = info["name"]
	
	return info 

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

def save_session_path(USERID: str, save: dict, path: str):
	# TODO 
	file = f"{USERID}.save.json"
	with open(os.path.join(path, file), 'w') as f:
		json.dump(save, f, indent='\t')