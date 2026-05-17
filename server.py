import os
import json
import urllib
import logging
import asyncio

from flask import Flask, render_template, send_from_directory, request, redirect
from flask import session as flasksession
from flask.debughelpers import attach_enctype_error_multidict
from bundle import ASSETS_DIR, STUB_DIR, TEMPLATES_DIR, BASE_DIR, CACHE_DIR, LOGS_DIR

app = Flask(__name__, template_folder=TEMPLATES_DIR)

# SILENCE FLASK BUT NOT SERVER LOGGER
logging.getLogger('werkzeug').disabled = True        # False enables flask logging

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
log.propagate = False

def _logging_filename():
	if not os.path.exists(LOGS_DIR):
		os.mkdir(LOGS_DIR)

	from datetime import datetime
	ts = datetime.utcnow().strftime("%Y-%m-%d %H %M %S")
	return f"{LOGS_DIR}/{ts}.log"

def _logging_setup(handle):
	handle.setLevel(logging.INFO)
	handle.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s %(message)s', "%Y-%m-%d %H:%M:%S"))
	log.addHandler(handle)

_logging_setup(logging.StreamHandler())

log.info(" [+] Loading basics...")

if os.name == 'nt':
	os.system("color")
	os.system("title Social Empires Server")
else:
	import sys
	sys.stdout.write("\x1b]2;Social Empires Server\x07")

# load server config -------------------------------------------------------------------------------------------
from server_config import get_server_config

host = get_server_config()["server"]["ip"]
port = get_server_config()["server"]["port"]
if get_server_config()["server"]["write_logs"]:
	_logging_setup(logging.FileHandler(_logging_filename(), mode='a'))

# --------------------------------------------------------------------------------------------------------------

log.info(" [+] Loading game config...")
from get_game_config import get_game_config, config_refresh

log.info(" [+] Loading players...")
from get_player_info import *
from sessions import *
load_saved_villages()

log.info(" [+] Loading server...")

from command import command
from engine import timestamp_now, get_default_town_id
from version import version_name, quest_ids, survival_arenas
from constants import Constant
from server_hmac import construct_hash_and_payload, check_hmac
from avatars import get_avatars

log.info(" [+] Configuring server routes...")

##########
# ROUTES #
##########

## PAGES AND RESOURCES

def do_logout():
	# Log out previous session
	flasksession.pop('USERID', default=None)
	flasksession.pop('GAMEVERSION', default=None)
	flasksession.pop('RUNNER', default=None)

@app.route("/", methods=['GET', 'POST'])
async def login():
	do_logout()

	# Reload saves. Allows saves modification without server reset
	if get_server_config()["server"]["allow_save_reloading"]:
		reload_saves()
	# If logging in, set session USERID, and go to play
	if request.method == 'POST':
		flasksession['USERID'] = request.form['USERID']
		flasksession['GAMEVERSION'] = request.form['GAMEVERSION']
		flasksession['RUNNER'] = request.form['RUNNER']

		uid = request.form['USERID']
		version = request.form['GAMEVERSION']
		runner = request.form['RUNNER']
		log.info(f"[LOGIN] USERID={uid}, GAMEVERSION={version}, RUNNER={runner}")

		if flasksession['RUNNER'] == "RUFFLE":
			return redirect("/play/ruffle")
		elif flasksession['RUNNER'] == "FLASH":
			return redirect("/play")
		else:
			return redirect("/play")
	# Login page
	if request.method == 'GET':
		saves_info = all_saves_info()
		return render_template("login.html", saves_info=saves_info, version=version_name)

@app.route("/reg", methods=['GET', 'POST'])
async def new_player():
	do_logout()
	return render_template("new_empire.html", version=version_name, avatars=get_avatars())

@app.route("/reg/new", methods=['POST'])
async def new_player_register():
	do_logout()

	#log.info("request: "+json.dumps(request.values, indent='\t'))

	result = check_player_name(request.values["playername"])
	if not result["ok"]:
		# TODO: show msg to user
		#log.info(result["msg"])
		return redirect("/reg")

	playername = request.values["playername"].strip()
	skiptutorial = 0
	if "skiptutorial" in request.values:
		skiptutorial = request.values["skiptutorial"] == "skiptutorial"
	starting_draggy = request.values["STARTING_DRAGGY"]
	avatar = request.values["AVATAR"]

	flasksession['GAMEVERSION'] = request.form['GAMEVERSION']
	flasksession['RUNNER'] = request.form['RUNNER']

	if "0926" not in flasksession['GAMEVERSION']:
		skiptutorial = 1

	flasksession['USERID'] = new_village(playername, skiptutorial, starting_draggy, avatar)

	if flasksession['RUNNER'] == "RUFFLE":
		return redirect("/play/ruffle")
	elif flasksession['RUNNER'] == "FLASH":
		return redirect("/play")

	return redirect("/play")

# old redirects
@app.route("/new.html")
async def new_redirect():
	return redirect("/new")

@app.route("/ruffle.html")
async def ruffle_redirect():
	return redirect("/play/ruffle")

@app.route("/play.html")
async def play_redirect():
	return redirect("/play")

@app.route("/play")
async def play():
	log.info(flasksession)

	if 'USERID' not in flasksession:
		return redirect("/")
	if 'GAMEVERSION' not in flasksession:
		return redirect("/")

	if flasksession['USERID'] not in all_saves_userid():
		return redirect("/")
    
	USERID = flasksession['USERID']
	GAMEVERSION = flasksession['GAMEVERSION']
	log.info(f"[PLAY] USERID={USERID}, GAMEVERSION={GAMEVERSION}")

	return render_template("play.html", save_info=save_info(USERID, True), serverTime=timestamp_now(), friendsInfo=fb_friends_str(USERID), version=version_name, GAMEVERSION=GAMEVERSION, SERVERIP=host, PORT=port, offers=get_version_settings(GAMEVERSION)["show_offers"])

@app.route("/play/ruffle")
async def ruffle():
	log.info(flasksession)

	if 'USERID' not in flasksession:
		return redirect("/")
	if 'GAMEVERSION' not in flasksession:
		return redirect("/")

	if flasksession['USERID'] not in all_saves_userid():
		return redirect("/")
    
	USERID = flasksession['USERID']
	GAMEVERSION = flasksession['GAMEVERSION']
	
	log.info(f"[RUFFLE] USERID={USERID}, GAMEVERSION={GAMEVERSION}")

	return render_template("ruffle.html", save_info=save_info(USERID, True), serverTime=timestamp_now(), friendsInfo=fb_friends_str(USERID), version=version_name, GAMEVERSION=GAMEVERSION, SERVERIP=host, PORT=port, offers=get_version_settings(GAMEVERSION)["show_offers"])


@app.route("/new")
async def new():
	return redirect("/")
	#flasksession['USERID'] = new_village()
	#flasksession['GAMEVERSION'] = "SocialEmpires0926bsec.swf"
	#flasksession['RUNNER'] = "FLASH"
	#return redirect("play")

@app.route("/crossdomain.xml")
async def crossdomain():
	return send_from_directory(STUB_DIR, "crossdomain.xml")

@app.route("/img/<path:path>")
async def images(path):
	return send_from_directory(TEMPLATES_DIR + "/img", path)

@app.route("/css/<path:path>")
async def css(path):
	return send_from_directory(TEMPLATES_DIR + "/css", path)

@app.route("/js/<path:path>")
async def js(path):
	return send_from_directory(TEMPLATES_DIR + "/js", path)

## GAME STATIC


@app.route("/default01.static.socialpointgames.com/static/socialempires/swf/05122012_projectiles.swf")
async def similar_05122012_projectiles():
	return send_from_directory(ASSETS_DIR + "/swf", "20130417_projectiles.swf")

@app.route("/default01.static.socialpointgames.com/static/socialempires/swf/05122012_magicParticles.swf")
async def similar_05122012_magicParticles():
	return send_from_directory(ASSETS_DIR + "/swf", "20131010_magicParticles.swf")

@app.route("/default01.static.socialpointgames.com/static/socialempires/swf/05122012_dynamic.swf")
async def similar_05122012_dynamic():
	return send_from_directory(ASSETS_DIR + "/swf", "120608_dynamic.swf")

@app.route("/default01.static.socialpointgames.com/static/socialempires/<path:path>")
async def static_assets_loader(path):
	# return send_from_directory(ASSETS_DIR, path)
	if not os.path.exists(ASSETS_DIR + "/"+ path):
		# File does not exists in provided assets
		if not os.path.exists(f"{ASSETS_DIR}/../download_assets/assets/{path}"):
			# Download file from SP's CDN if it doesn't exist

			# Make directory
			directory = os.path.dirname(f"{ASSETS_DIR}/../download_assets/assets/{path}")
			if not os.path.exists(directory):
				os.makedirs(directory)

			# Download File
			URL = f"https://static.socialpointgames.com/static/socialempires/assets/{path}"
			try:
				response = urllib.request.urlretrieve(URL, f"{ASSETS_DIR}/../download_assets/assets/{path}")
			except urllib.error.HTTPError:
				return ("", 404)

			log.info(f"====== DOWNLOADED ASSET: {URL}")
			return send_from_directory("{ASSETS_DIR}/../download_assets/assets", path)
		else:
			# Use downloaded CDN asset
			log.info(f"====== USING EXTERNAL: download_assets/assets/{path}")
			return send_from_directory("{ASSETS_DIR}/../download_assets/assets", path)
	else:
		# Use provided asset
		return send_from_directory(ASSETS_DIR, path)

## GAME DYNAMIC

@app.route("/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/get_up_data.php", methods=['POST'])
async def units_pack_get_data():
	USERID = request.values['USERID']
	user_key = request.values['user_key']
	if 'spdebug' in request.values:
		spdebug = request.values['spdebug']
	language = request.values['language']

	#log.info("request: "+json.dumps(request.values, indent='\t'))
	data, correct = check_hmac(request.values['data'])
	#log.info("data: "+json.dumps(data, indent='\t'))

	if not correct: # Invalid HMAC
		return (construct_hash_and_payload({
			"result": "error"
		}), 403)

	state = pop_unit_pack_state(USERID)
	retries = 100
	while not state:
		if retries < 0:
			return (construct_hash_and_payload({
				"result": "error"
			}), 403)

		retries -= 1
		await asyncio.sleep(0.1)
		state = pop_unit_pack_state(USERID)

	if state["n"] != int(data["n"]):
		return (construct_hash_and_payload({
			"result": "error"
		}), 403)

	randoms = state["r"]
	return (construct_hash_and_payload({
		"result": "success",
		"data": state["r"]
	}), 200)

@app.route("/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/pvp/web/app.php/pvp/enemy", methods=['POST'])
async def pvp_lookup():
	USERID = request.values['USERID']
	user_key = request.values['user_key']
	if 'spdebug' in request.values:
		spdebug = request.values['spdebug']
	language = request.values['language']

	data, correct = check_hmac(request.values['data'])
	if not correct: # Invalid HMAC
		return ("", 403)

	return (construct_hash_and_payload(get_enemy_info(USERID, 0)), 200)

@app.route("/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/pvp/web/app.php/pvp/attack/begin", methods=['POST'])
async def pvp_begin():
	USERID = request.values['USERID']
	user_key = request.values['user_key']
	if 'spdebug' in request.values:
		spdebug = request.values['spdebug']
	language = request.values['language']

	#log.info("request: "+json.dumps(request.values, indent='\t'))
	data, correct = check_hmac(request.values['data'])
	#log.info("data: "+json.dumps(data, indent='\t'))

	# data -> dict
	#    attacked_id -> enemy_id
	#    rival_name -> enemy name
	#    level -> attacker level
	#    name -> attacker name
	#    user_id -> user_id
	#    attacked_level_id -> enemy level
	#    [reply] -> 0 if attack is revenge

	if not correct:
		return ("", 403)

	is_revenge = False
	if "reply" in data:
		is_revenge = data["reply"] == 0

	pvp_begin_attack(data, is_revenge)

	return ("", 200)

@app.route("/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/pvp/web/app.php/pvp/attack/end", methods=['POST'])
async def pvp_end():
	USERID = request.values['USERID']
	user_key = request.values['user_key']
	if 'spdebug' in request.values:
		spdebug = request.values['spdebug']
	language = request.values['language']

	#log.info("request: "+json.dumps(request.values, indent='\t'))
	data, correct = check_hmac(request.values['data'])
	#log.info("data: "+json.dumps(data, indent='\t'))

	# data -> dict
	#    user_id -> user_id
	#    percentage -> damage% (0-1)
	#    level -> attacker level
	#    winnerId -> winner_id
	#    attacked_id -> enemy_id
	#    name -> attacker name
	#    resources -> stolen resources { s, f, g, w }

	if not correct:
		return ("", 403)

	pvp_modify_victim(data, 0)

	return ("", 200)

@app.route("/pvp/ranking", methods=['GET'])
async def pvp_ranking():
	if 'USERID' not in flasksession:
		return redirect("/")
	if 'GAMEVERSION' not in flasksession:
		return redirect("/")

	return render_template("pvp_ranking.html", version=version_name, player_rank=pvp_get_ranks())

@app.route("/graveyard/potions", methods=['GET'])
async def graveyard_potions():
	if 'USERID' not in flasksession:
		return redirect("/")
	if 'GAMEVERSION' not in flasksession:
		return redirect("/")

	player = session(flasksession['USERID'])
	can = player_can_receive_potions(player)

	return render_template("graveyard_potions.html", version=version_name, can_receive=can, num=POTIONS_PER_FRIEND)

@app.route("/graveyard/potions/request", methods=['GET'])
async def graveyard_potions_request():
	if 'USERID' not in flasksession:
		return redirect("/")
	if 'GAMEVERSION' not in flasksession:
		return redirect("/")

	player_ask_potions(flasksession['USERID'])

	return redirect("/graveyard/potions")

@app.route("/friends/hire", methods=['POST'])
async def external_friends_hire():
	if 'USERID' not in flasksession:
		return redirect("/")
	if 'GAMEVERSION' not in flasksession:
		return redirect("/")

	if "data" not in request.values:
		return redirect("/")
	data = json.loads(request.values["data"])
	# bx, by, town_id, bitem_id, hired_si, bitem_name

	item = get_item_from_id(data[3])
	si = get_si_info(data[3])
	
	if not item or not si:
		return redirect("/")

	hired = len(data[4].split(","))
	required = len(si["workers"].split(','))
	cost = si["worker_cost"]
	autohire = int(item["id"]) not in autohire_ignore_buildings

	return render_template("friends_hire.html", version=version_name, building=item, num=hired, required=required, cost=cost, autohire=autohire)


# graph.facebook.com reroute
@app.route("/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/graph.facebook.com/<path:path>", methods=['GET'])
async def graph_fb(path):
	_path = path.split("/")
	if len(_path) != 2:
		return ("", 404)
	if _path[1] != "picture":
		return ("", 404)
	if request.values["type"] != "square":
		return ("", 404)
	
	uid = str(_path[0])
	avatar = get_target_pic(uid)

	if not avatar:
		return send_from_directory(TEMPLATES_DIR, "img/profile/default.jpg")

	pic = image_cache(avatar, uid)
	if not pic:
		return send_from_directory(TEMPLATES_DIR, "img/profile/default.jpg")
	
	return send_from_directory(CACHE_DIR, pic)

# caches images from web to send under the graph.facebook.com reroute
__image_cache = []
__image_cache_filename = []

def image_cache_load():
	global __image_cache
	global __image_cache_filename
	if not os.path.exists(CACHE_DIR):
		os.mkdir(CACHE_DIR)
	cache_json_path = os.path.join(CACHE_DIR, "cache.json")
	if os.path.exists(cache_json_path):
		data = json.load(open(cache_json_path, 'r', encoding='utf-8'))
		__image_cache = data["uid"]
		__image_cache_filename = data["img"]

def image_cache_save():
	with open(os.path.join(CACHE_DIR, "cache.json"), 'w', encoding='utf-8') as f:
		data = {
			"uid": __image_cache,
			"img": __image_cache_filename
		}
		json.dump(data, f)

def image_cache(url, userid):
	# no bullshit!
	userid = userid.replace(".","")

	if url in __image_cache:
		idx = __image_cache.index(url)
		return __image_cache_filename[idx]
	else:
		if not os.path.exists(CACHE_DIR):
			os.mkdir(CACHE_DIR)

		dest = f"{userid}.png"
		try:
			response = urllib.request.urlretrieve(url, os.path.join(CACHE_DIR, dest))
		except urllib.error.HTTPError:
			return ("", 404)
		__image_cache.append(url)
		__image_cache_filename.append(dest)
		image_cache_save()
		return dest

image_cache_load()

@app.route("/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/track_game_status.php", methods=['POST'])
async def track_game_status_response():
	status = request.values['status']
	installId = request.values['installId']
	user_id = request.values['user_id']

	#log.info(f"track_game_status: status={status}, installId={installId}, user_id={user_id}. --", request.values)
	return ("", 200)

@app.route("/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/get_game_config.php", methods=['GET','POST'])
async def get_game_config_response():
	spdebug = None

	USERID = request.values['USERID']
	user_key = request.values['user_key']
	if 'spdebug' in request.values:
		spdebug = request.values['spdebug']
	language = request.values['language']

	#log.info(f"get_game_config: USERID: {USERID}. --", request.values)
	
	config_refresh(timestamp_now())

	return construct_hash_and_payload(get_game_config())

@app.route("/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/get_player_info.php", methods=['POST'])
async def get_player_info_response():
	player_user = flasksession['USERID']

	USERID = request.values['USERID']
	user_key = request.values['user_key']
	spdebug = request.values['spdebug'] if 'spdebug' in request.values else None
	language = request.values['language']
	neighbors = request.values['neighbors'] if 'neighbors' in request.values else None
	client_id = request.values['client_id']
	user = request.values['user'] if 'user' in request.values else None
	map = int(request.values['map']) if 'map' in request.values else 0

	log.info(f"get_player_info: USERID: {USERID}. user: {user} --", request.values)

	# Current Player
	if user is None:
		flasksession["TOWNID"] = map
		#log.info(f"SET LAST TOWN ID TO {map}")
		return (construct_hash_and_payload(get_player_info(USERID, flasksession['USERID'], flasksession["TOWNID"])), 200)
	elif user == USERID:
		flasksession["TOWNID"] = map
		#log.info(f"SET LAST TOWN ID TO {map}")
		return (construct_hash_and_payload(get_player_info(USERID, flasksession['USERID'], flasksession["TOWNID"])), 200)
	# PVP RANDOM
	if user == "undefined":
		enemy = get_pvp_search_result(USERID, 0)
		if not enemy:
			# TODO: handle no players found
			return ("", 404)
		return (construct_hash_and_payload(enemy), 200)
	# Arthur
	elif user == Constant.NEIGHBOUR_ARTHUR_GUINEVERE_1 \
	or user == Constant.NEIGHBOUR_ARTHUR_GUINEVERE_2 \
	or user == Constant.NEIGHBOUR_ARTHUR_GUINEVERE_3:
		return (construct_hash_and_payload(get_target_info(user, map)), 200)
	# Quest
	elif user in quest_ids or user in survival_arenas: # Dirty but quick
		return construct_hash_and_payload(get_quest_info(user))
	# Neighbor
	else:
		return (construct_hash_and_payload(get_target_info(user, map)), 200)

@app.route("/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/get_public_player_info.php", methods=['GET'])
async def get_public_player_info_response():
	USERID = request.values['USERID']
	user_key = request.values['user_key']
	language = request.values['language']

	player = get_target_session(USERID)
	if not player:
		return ("", 404)

	town_id = get_default_town_id(player, flasksession["GAMEVERSION"])
	playerInfo = player["playerInfo"]
	_map = player["maps"][town_id]
	privateState = player["privateState"]
	
	response = {
		"name": playerInfo["name"],
		"level": _map["level"],
		"map_names": playerInfo["map_names"],
		"honor_points": playerInfo["honor_points"],
		"country": playerInfo["country"],
		"last_logged_in": playerInfo["last_logged_in"],
		"attacks_won": playerInfo["attacks_won"],
		"attacks_lost": playerInfo["attacks_lost"],
		"pid": playerInfo["pid"],
		"teams": privateState["teams"]
	}

	return (response, 200)


@app.route("/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/sync_error_track.php", methods=['POST'])
async def sync_error_track_response():
	spdebug = None

	USERID = request.values['USERID']
	user_key = request.values['user_key']
	if 'spdebug' in request.values:
		spdebug = request.values['spdebug']
	language = request.values['language']
	error = request.values['error']
	current_failed = request.values['current_failed']
	tries = request.values['tries'] if 'tries' in request.values else None
	survival = request.values['survival']
	previous_failed = request.values['previous_failed']
	description = request.values['description']
	user_id = request.values['user_id']

	#log.info(f"sync_error_track: USERID: {USERID}. [Error: {error}] tries: {tries}. --", request.values)
	return ("", 200)

@app.route("/null")
async def flash_sync_error_response():
	sp_ref_cat = request.values['sp_ref_cat']

	if sp_ref_cat == "flash_sync_error":
		reason = "reload On Sync Error"
	elif sp_ref_cat == "flash_reload_quest":
		reason = "reload On End Quest"
	elif sp_ref_cat == "flash_reload_attack":
		reason = "reload On End Attack"

	#log.info("flash_sync_error", reason, ". --", request.values)
	return redirect("/play.html")

@app.route("/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/command.php", methods=['POST'])
async def command_response():
	spdebug = None

	USERID = request.values['USERID']
	user_key = request.values['user_key']
	if 'spdebug' in request.values:
		spdebug = request.values['spdebug']
	language = request.values['language']
	client_id = request.values['client_id']
	last_town_id = 0
	if "TOWNID" in flasksession:
		last_townid = flasksession["TOWNID"]

	# log.info(f"command: USERID: {USERID}. --", request.values)

	data_str = request.values['data']
	data_hash = data_str[:64]
	assert data_str[64] == ';'
	data_payload = data_str[65:]
	data = json.loads(data_payload)

	command(USERID, data, flasksession["GAMEVERSION"], last_townid)
    
	return ({"result": "success"}, 200)

@app.route("/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/get_continent_ranking.php")
async def get_continent_ranking_response():

	USERID = request.values['USERID']
	worldChange = request.values['worldChange']
	if 'spdebug' in request.values:
		spdebug = request.values['spdebug']
	town_id = request.values['map']
	user_key = request.values['user_key']

	# TODO - stub
	response = {
		"world_id": 0,
		"continent": [
			{"posicion": 0, "nivel": 1, "user_id": 1111}, # villages/AcidCaos
			{"posicion": 1, "nivel": 0},
			{"posicion": 2, "nivel": 0},
			{"posicion": 3, "nivel": 0},
			{"posicion": 4, "nivel": 0},
			{"posicion": 5, "nivel": 0},
			{"posicion": 6, "nivel": 0},
			{"posicion": 7, "nivel": 0}
		]
	}
	return(construct_hash_and_payload(response))

# UNIMPLEMENTED APIS

async def _api_not_implemented(request, api_call):
	log.info(f"API NOT IMPLEMENTED: {api_call}")
	log.info("request: "+json.dumps(request.values, indent='\t'))
	data, correct = check_hmac(request.values['data'])
	log.info("data: "+json.dumps(data, indent='\t'))

	if not correct:
		return ("", 403)

	return ("", 404)

@app.route("/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/register_found_item.php", methods=['POST'])
async def register_found_item():
	return await _api_not_implemented(request, "register_found_item.php")

@app.route("/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/get_continent.php", methods=['POST'])
async def get_continent():
	return await _api_not_implemented(request, "get_continent.php")

@app.route("/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/get_user_world.php", methods=['POST'])
async def get_user_world():
	return await _api_not_implemented(request, "get_user_world.php")

@app.route("/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/report_error.php", methods=['POST'])
async def report_error():
	return await _api_not_implemented(request, "report_error.php")

@app.route("/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/tournaments/cancel_tournament.php", methods=['POST'])
async def tournaments_cancel_tournament():
	return await _api_not_implemented(request, "tournaments/cancel_tournament.php")

@app.route("/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/tournaments/create_tournament.php", methods=['POST'])
async def tournaments_create_tournament():
	return await _api_not_implemented(request, "tournaments/create_tournament.php")

@app.route("/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/tournaments/join_tournament.php", methods=['POST'])
async def tournaments_join_tournament():
	return await _api_not_implemented(request, "tournaments/join_tournament.php")

@app.route("/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/tournaments/start_tournament_match.php", methods=['POST'])
async def tournaments_start_tournament_match():
	return await _api_not_implemented(request, "tournaments/start_tournament_match.php")

@app.route("/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/tournaments/finish_tournament_match.php", methods=['POST'])
async def tournaments_finish_tournament_match():
	return await _api_not_implemented(request, "tournaments/finish_tournament_match.php")

@app.route("/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/tournaments/clean_tournament.php", methods=['POST'])
async def tournaments_clean_tournament():
	return await _api_not_implemented(request, "tournaments/clean_tournament.php")

@app.route("/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/tournaments/leave_tournament.php", methods=['POST'])
async def tournaments_leave_tournament():
	return await _api_not_implemented(request, "tournaments/leave_tournament.php")

@app.route("/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/tournaments/kompu_try.php", methods=['POST'])
async def kompu_try():
	return await _api_not_implemented(request, "tournaments/kompu_try.php")

@app.route("/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/tournaments/kompu_hurry_up.php", methods=['POST'])
async def kompu_hurry_up():
	return await _api_not_implemented(request, "tournaments/kompu_hurry_up.php")

@app.route("/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/tournaments/clean_assaults.php", methods=['POST'])
async def clean_assaults():
	return await _api_not_implemented(request, "tournaments/clean_assaults.php")


########
# MAIN #
########

log.info(" [+] Running server...")

if __name__ == '__main__':
	app.secret_key = 'SECRET_KEY'
	# TODO: post to console this after running the app
	if logging.getLogger('werkzeug').disabled:
		log.info(f" * Running on http://{host}:{port}")
	app.run(host=host, port=port, debug=False)
	