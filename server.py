print (" [+] Loading basics...")
import os
import json
import urllib
if os.name == 'nt':
    os.system("color")
    os.system("title Social Empires Server")
else:
    import sys
    sys.stdout.write("\x1b]2;Social Empires Server\x07")

print (" [+] Loading game config...")
from get_game_config import get_game_config, patch_game_config

print (" [+] Loading players...")
from get_player_info import get_player_info, get_neighbor_info
from sessions import load_saved_villages, all_saves_userid, all_saves_info, save_info, new_village, fb_friends_str
load_saved_villages()

print (" [+] Loading server...")
from flask import Flask, render_template, send_from_directory, request, redirect, session
from flask.debughelpers import attach_enctype_error_multidict
from command import command
from engine import timestamp_now
from version import version_name
from constants import Constant
from quests import get_quest_map
from bundle import ASSETS_DIR, STUB_DIR, TEMPLATES_DIR, BASE_DIR

host = '127.0.0.1'
port = 5050

app = Flask(__name__, template_folder=TEMPLATES_DIR)

print (" [+] Configuring server routes...")

##########
# ROUTES #
##########

## PAGES AND RESOURCES

@app.route("/", methods=['GET', 'POST'])
def login():
    # Log out previous session
    session.pop('USERID', default=None)
    session.pop('GAMEVERSION', default=None)
    # Reload saves. Allows saves modification without server reset
    load_saved_villages()
    # If logging in, set session USERID, and go to play
    if request.method == 'POST':
        session['USERID'] = request.form['USERID']
        session['GAMEVERSION'] = request.form['GAMEVERSION']
        print("[LOGIN] USERID:", request.form['USERID'])
        print("[LOGIN] GAMEVERSION:", request.form['GAMEVERSION'])
        return redirect("/play.html")
    # Login page
    if request.method == 'GET':
        saves_info = all_saves_info()
        return render_template("login.html", saves_info=saves_info, version=version_name)

@app.route("/play.html")
def play():
    print(session)

    if 'USERID' not in session:
        return redirect("/")
    if 'GAMEVERSION' not in session:
        return redirect("/")

    if session['USERID'] not in all_saves_userid():
        return redirect("/")
    
    USERID = session['USERID']
    GAMEVERSION = session['GAMEVERSION']
    print("[PLAY] USERID:", USERID)
    print("[PLAY] GAMEVERSION:", GAMEVERSION)
    return render_template("play.html", save_info=save_info(USERID), serverTime=timestamp_now(), friendsInfo=fb_friends_str(USERID), version=version_name, GAMEVERSION=GAMEVERSION, SERVERIP=host)

@app.route("/ruffle.html")
def ruffle():
    return redirect("/play.html?mode=ruffle")


@app.route("/new.html")
def new():
    session['USERID'] = new_village()
    session['GAMEVERSION'] = "SocialEmpires0926bsec.swf"
    return redirect("play.html")

@app.route("/crossdomain.xml")
def crossdomain():
    return send_from_directory(STUB_DIR, "crossdomain.xml")

@app.route("/img/<path:path>")
def images(path):
    return send_from_directory(TEMPLATES_DIR + "/img", path)

@app.route("/css/<path:path>")
def css(path):
    return send_from_directory(TEMPLATES_DIR + "/css", path)

## GAME STATIC


@app.route("/default01.static.socialpointgames.com/static/socialempires/swf/05122012_projectiles.swf")
def similar_05122012_projectiles():
    return send_from_directory(ASSETS_DIR + "/swf", "20130417_projectiles.swf")

@app.route("/default01.static.socialpointgames.com/static/socialempires/swf/05122012_magicParticles.swf")
def similar_05122012_magicParticles():
    return send_from_directory(ASSETS_DIR + "/swf", "20131010_magicParticles.swf")

@app.route("/default01.static.socialpointgames.com/static/socialempires/swf/05122012_dynamic.swf")
def similar_05122012_dynamic():
    return send_from_directory(ASSETS_DIR + "/swf", "120608_dynamic.swf")

@app.route("/default01.static.socialpointgames.com/static/socialempires/<path:path>")
def static_assets_loader(path):
    # return send_from_directory(ASSETS_DIR, path)
    if not os.path.exists(ASSETS_DIR + "/"+ path):
        # File does not exists in provided assets
        if not os.path.exists(f"{BASE_DIR}/download_assets/assets/{path}"):
            # Download file from SP's CDN if it doesn't exist

            # Make directory
            directory = os.path.dirname(f"{BASE_DIR}/download_assets/assets/{path}")
            if not os.path.exists(directory):
                os.makedirs(directory)

            # Download File
            URL = f"https://static.socialpointgames.com/static/socialempires/assets/{path}"
            try:
                response = urllib.request.urlretrieve(URL, f"{BASE_DIR}/download_assets/assets/{path}")
            except urllib.error.HTTPError:
                return ("", 404)

            print(f"====== DOWNLOADED ASSET: {URL}")
            return send_from_directory(f"{BASE_DIR}/download_assets/assets", path)
        else:
            # Use downloaded CDN asset
            print(f"====== USING EXTERNAL: download_assets/assets/{path}")
            return send_from_directory(f"{BASE_DIR}/download_assets/assets", path)
    else:
        # Use provided asset
        return send_from_directory(ASSETS_DIR, path)

## GAME DYNAMIC

@app.route("/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/track_game_status.php", methods=['GET', 'POST'])
def track_game_status_response():
    status = request.values.get('status', 'unknown')
    installId = request.values.get('installId', 'unknown')
    user_id = request.values.get('user_id', 'unknown')

    print(f"track_game_status: status={status}, installId={installId}, user_id={user_id}. --", request.values)
    return ("", 200)
@app.route("/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/get_game_config.php", methods=['GET','POST'])
def get_game_config_response():
    spdebug = request.values.get('spdebug')
    USERID = request.values.get('USERID')
    user_key = request.values.get('user_key')
    language = request.values.get('language', 'en')

    print(f"get_game_config: USERID: {USERID}. --", request.values)
    return get_game_config()

@app.route("/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/get_player_info.php", methods=['GET', 'POST'])
def get_player_info_response():
    USERID = request.values.get('USERID')
    user_key = request.values.get('user_key')
    spdebug = request.values.get('spdebug')
    language = request.values.get('language', 'en')
    neighbors = request.values.get('neighbors')
    client_id = request.values.get('client_id')
    user = request.values.get('user')
    map = int(request.values['map']) if 'map' in request.values else None

    print(f"get_player_info: USERID: {USERID}. user: {user} --", request.values)

    # Current Player
    if user is None:
        return (get_player_info(USERID), 200)
    # Arthur
    elif user == Constant.NEIGHBOUR_ARTHUR_GUINEVERE_1 \
    or user == Constant.NEIGHBOUR_ARTHUR_GUINEVERE_2 \
    or user == Constant.NEIGHBOUR_ARTHUR_GUINEVERE_3:
        return (get_neighbor_info(user, map), 200)
    # Quest
    elif user.startswith("100000"): # Dirty but quick
        return get_quest_map(user)
    # Neighbor
    else:
        return (get_neighbor_info(user, map), 200)

@app.route("/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/sync_error_track.php", methods=['GET', 'POST'])
def sync_error_track_response():
    USERID = request.values.get('USERID')
    user_key = request.values.get('user_key')
    spdebug = request.values.get('spdebug')
    language = request.values.get('language', 'en')
    error = request.values.get('error', 'unknown')
    current_failed = request.values.get('current_failed', '0')
    tries = request.values.get('tries')
    survival = request.values.get('survival', '0')
    previous_failed = request.values.get('previous_failed', '0')
    description = request.values.get('description', '')
    user_id = request.values.get('user_id', '')

    print(f"sync_error_track: USERID: {USERID}. [Error: {error}] tries: {tries}. --", request.values)
    return ("", 200)
@app.route("/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/", methods=['GET', 'POST'])
@app.route("/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires", methods=['GET', 'POST'])
def srvempires_base_response():
    print(f"[BASE ROUTE CALLED] method={request.method} -- values={request.values}")
    if 'data' in request.values:
        return command_response()
    return ("", 200)

@app.route("/null", methods=['GET', 'POST'])
def flash_sync_error_response():
    sp_ref_cat = request.values.get('sp_ref_cat', 'flash_sync_error')

    if sp_ref_cat == "flash_sync_error":
        reason = "reload On Sync Error"
    elif sp_ref_cat == "flash_reload_quest":
        reason = "reload On End Quest"
    elif sp_ref_cat == "flash_reload_attack":
        reason = "reload On End Attack"
    else:
        reason = sp_ref_cat

    print("flash_sync_error", reason, ". --", request.values)
    return redirect("/play.html")

@app.route("/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/command.php", methods=['GET', 'POST'])
def command_response():
    USERID = request.values.get('USERID')
    user_key = request.values.get('user_key')
    spdebug = request.values.get('spdebug')
    language = request.values.get('language', 'en')
    client_id = request.values.get('client_id')

    print(f"command: USERID: {USERID}. --", request.values)

    data_str = request.values.get('data')
    if not data_str:
        return ({"result": "success"}, 200)

    if len(data_str) > 65 and data_str[64] == ';':
        data_payload = data_str[65:]
    else:
        data_payload = data_str

    try:
        data = json.loads(data_payload)
    except Exception as e:
        print(f"[-] Failed parsing json data: {e}")
        return ({"result": "success"}, 200)

    command(USERID, data)
    
    return ({"result": "success"}, 200)

@app.route("/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/get_continent_ranking.php", methods=['GET', 'POST'])
def get_continent_ranking_response():
    USERID = request.values.get('USERID')
    worldChange = request.values.get('worldChange', '0')
    spdebug = request.values.get('spdebug')
    town_id = request.values.get('map', '0')
    user_key = request.values.get('user_key')

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
    return(response)


########
# MAIN #
########

print (" [+] Running server...")

@app.before_request
def log_request_info():
    try:
        ts = timestamp_now()
    except:
        import time
        ts = int(time.time())
    try:
        with open("request.log", "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {request.method} {request.url}\n")
            f.write(f"  Values: {dict(request.values)}\n\n")
    except Exception as ex:
        print("[-] Error writing request log:", ex)

import traceback

@app.errorhandler(Exception)
def handle_exception(e):
    try:
        ts = timestamp_now()
    except:
        import time
        ts = int(time.time())
    with open("error.log", "a", encoding="utf-8") as f:
        f.write(f"=== ERROR AT {ts} ===\n")
        traceback.print_exc(file=f)
        f.write("\n")
    traceback.print_exc()
    return ({"error": str(e)}, 500)

if __name__ == '__main__':
    app.secret_key = 'SECRET_KEY'
    app.run(host=host, port=port, debug=True, use_reloader=False)
