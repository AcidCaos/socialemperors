from quests import get_quest_map
from sessions import session, neighbor_session, neighbors, pvp_enemy
from engine import timestamp_now

def get_player_info(USERID, town_id = 0):
	save = session(USERID)
	friends = neighbors(USERID)

	# Update last logged in
	ts_now = timestamp_now()
	save["playerInfo"]["last_logged_in"] = ts_now

	# player
	response = {
		"result": "ok",
		"processed_errors": 0,
		"timestamp": ts_now,
		"playerInfo": save["playerInfo"],
		"map": save["maps"][town_id],
		"privateState": save["privateState"],
		"neighbors": friends
	}
	return response

def get_neighbor_info(userid, town_id = 0):
	save = neighbor_session(userid)
	friends = neighbors(userid)

	response = {
		"result": "ok",
		"processed_errors": 0,
		"timestamp": timestamp_now(),
		"playerInfo": save["playerInfo"],
		"map": save["maps"][town_id],
		"privateState": save["privateState"],
		"neighbors": friends
	}
	return response

def get_enemy_info(userid):
	response = {
		"id": userid,
		"result": "ok",
		"data": {}
	}
	return response

def get_random_enemy(userid, town_id):
	enemy_id = pvp_enemy(userid, town_id)
	if not enemy_id:
		return None

	save = neighbor_session(enemy_id)

	response = {
		"result": "ok",
		"processed_errors": 0,
		"timestamp": timestamp_now(),
		"playerInfo": save["playerInfo"],
		"map": save["maps"][town_id],
		"privateState": save["privateState"],
		"neighbors": []
	}
	return response

def get_quest_info(quest_id, town_id = 0):
	quest = get_quest_map(quest_id)
	response = {
		"result": "ok",
		"processed_errors": 0,
		"timestamp": timestamp_now(),
		"playerInfo": quest["playerInfo"],
		"map": quest["maps"][town_id],
		"privateState": quest["privateState"],
		"neighbors": []
	}
	return response
