import json
import logging
import os
import random
from bundle import TEMPLATES_DIR, CONFIG_DIR
from server_config import get_server_config

log = logging.getLogger('__main__')

__user_avatars = []

def load_avatars():
	global __user_avatars

	try:
		avatars = json.load(open(os.path.join(CONFIG_DIR, "avatars.json")))

		__user_avatars = [{
			"url": "",
			"name": "Default Avatar"
		}]

		host = get_server_config()["server"]["ip"]
		port = get_server_config()["server"]["port"]
		base_url = f"http://{host}:{port}/"

		for a in avatars:
			__user_avatars.append({
				"url": f"{base_url}{a}",
				"name": avatars[a]
			})

		log.info(" [+] Avatars initialized!")
	except:
		log.info(" [!] Failed to load avatars.json")
		__user_avatars = [{
			"url": "",
			"name": "Default"
		}]

def _create_avatar_json():
	path = os.path.join(TEMPLATES_DIR, "img/profile/user")

	avatars = {}

	for file in os.listdir(path):
		avatars[f"img/profile/user/{file}"] = file 

	with open(os.path.join(CONFIG_DIR, "avatars.json"), 'w') as f:
		json.dump(avatars, f, indent='\t')

# random excluding default avatar, returns default avatar if none are defined
def get_random_avatar():
	num = len(__user_avatars)
	if num <= 1:
		return __user_avatars[0]

	return __user_avatars[random.randint(1, num - 1)]

def assign_random_avatar(save):
	playerInfo = save["playerInfo"]
	if not "pic" in playerInfo:
		playerInfo["pic"] = get_random_avatar()["url"]
		return
	if playerInfo["pic"] == "":
		playerInfo["pic"] = get_random_avatar()["url"]
		return

def get_avatars():
	return __user_avatars

load_avatars()