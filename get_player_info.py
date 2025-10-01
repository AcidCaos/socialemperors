from quests import get_quest_map
from sessions import session, neighbor_session, neighbors
from engine import timestamp_now

def get_player_info(USERID):
    # Update last logged in
    ts_now = timestamp_now()
    session(USERID)["playerInfo"]["last_logged_in"] = ts_now
    # player
    player_info = {
        "result": "ok",
        "processed_errors": 0,
        "timestamp": ts_now,
        "playerInfo": session(USERID)["playerInfo"],
        "map": session(USERID)["maps"][0],
        "privateState": session(USERID)["privateState"],
        "neighbors": neighbors(USERID)
    }
    return player_info

def get_neighbor_info(userid, map_number = 0):
    enemy = neighbor_session(userid)

    neighbor_info = {
        "result": "ok",
        "processed_errors": 0,
        "timestamp": timestamp_now(),
        "playerInfo": neighbor_session(userid)["playerInfo"],
        "map": neighbor_session(userid)["maps"][map_number],
        "privateState": neighbor_session(userid)["privateState"],
        "neighbors": neighbors(userid)
    }
    return neighbor_info

def get_enemy_info(userid):
	enemy_info = {
		"id": userid,
		"result": "ok",
		"data": {}
	}
	return enemy_info

def get_quest_info(quest_id, map_number = 0):
    quest_data = get_quest_map(quest_id)
    quest_info = {
        "result": "ok",
        "processed_errors": 0,
        "timestamp": timestamp_now(),
        "playerInfo": quest_data["playerInfo"],
        "map": quest_data["maps"][map_number],
        "privateState": quest_data["privateState"],
        "neighbors": []
    }
    return quest_info
