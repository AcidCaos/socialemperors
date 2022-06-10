print (" [+] Loading basics...")
import os
import json
if os.name == 'nt':
    os.system("color")

print (" [+] Loading game config...")
from get_game_config import get_game_config

print (" [+] Loading players...")
from get_player_info import get_player_info
from sessions import all_saves_userid, new_village

print (" [+] Loading server...")
from flask import Flask, render_template, send_from_directory, request, redirect, session
from flask.debughelpers import attach_enctype_error_multidict
from command import command

version = "pre-alpha 0.01"

host = '127.0.0.1'
port = 5050

app = Flask(__name__)

print (" [+] Configuring server routes...")

##########
# ROUTES #
##########

## PAGES AND RESOURCES

@app.route("/", methods=['GET', 'POST'])
def login():
    # Log out previous session
    session.pop('USERID', default=None)
    # If logging in, set session USERID, and go to play
    if request.method == 'POST':
        session['USERID'] = request.form['USERID']
        print("[LOGIN] USERID:", request.form['USERID'])
        return redirect("/play.html")
    # Login page
    if request.method == 'GET':
        return render_template("login.html", all_saves_userid=all_saves_userid())

@app.route("/play.html")
def play():
    if 'USERID' not in session:
        return redirect("/")
    print("[PLAY] USERID:", session['USERID'])
    return render_template("play.html", USERID=session['USERID'])

@app.route("/new.html")
def new():
    session['USERID'] = new_village()
    return redirect("play.html")

@app.route("/crossdomain.xml")
def crossdomain():
    return send_from_directory("stub", "crossdomain.xml")

@app.route("/img/<path:path>")
def images(path):
    return send_from_directory("templates/img", path)

## GAME STATIC

@app.route("/default01.static.socialpointgames.com/static/socialempires/fonts/en_ErasBold.swf")
def fake_fonts():
    return send_from_directory("stub", "en_ErasBold.swf")

@app.route("/default01.static.socialpointgames.com/static/socialempires/flash/SocialEmpires0910csec.swf")
def game_swf():
    return send_from_directory("flash", "SocialEmpires0926bsec_fonts.swf")

@app.route("/default01.static.socialpointgames.com/static/socialempires/flash/<path:path>")
def flash_files(path):
    return send_from_directory("flash", path)

@app.route("/default01.static.socialpointgames.com/static/socialempires/swf/05122012_projectiles.swf")
def similar_05122012_projectiles():
    return send_from_directory("assets/swf", "120615__projectiles.swf")

@app.route("/default01.static.socialpointgames.com/static/socialempires/swf/05122012_magicParticles.swf")
def similar_05122012_magicParticles():
    return send_from_directory("assets/swf", "121009_magicParticles.swf")

@app.route("/default01.static.socialpointgames.com/static/socialempires/swf/05122012_dynamic.swf")
def similar_05122012_dynamic():
    return send_from_directory("assets/swf", "120608_dynamic.swf")

@app.route("/default01.static.socialpointgames.com/static/socialempires/<path:path>")
def static_assets_loader(path):
    return send_from_directory("assets", path)

## GAME DYNAMIC

@app.route("/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/track_game_status.php", methods=['POST'])
def track_game_status_response():
    status = request.values['status']
    installId = request.values['installId']
    user_id = request.values['user_id']

    print(f"track_game_status: status={status}, installId={installId}, user_id={user_id}. --", request.values)
    return ("", 200)

@app.route("/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/get_game_config.php")
def get_game_config_response():
    USERID = request.values['USERID']
    user_key = request.values['user_key']
    spdebug = request.values['spdebug']
    language = request.values['language']

    print(f"get_game_config: USERID: {USERID}. --", request.values)
    return get_game_config()

@app.route("/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/get_player_info.php", methods=['POST'])
def get_player_info_response():
    USERID = request.values['USERID']
    user_key = request.values['user_key']
    spdebug = request.values['spdebug']
    language = request.values['language']
    neighbors = request.values['neighbors']
    client_id = request.values['client_id']

    print(f"get_player_info: USERID: {USERID}. --", request.values)
    return (get_player_info(USERID), 200)

@app.route("/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/sync_error_track.php", methods=['POST'])
def sync_error_track_response():
    USERID = request.values['USERID']
    user_key = request.values['user_key']
    spdebug = request.values['spdebug']
    language = request.values['language']
    error = request.values['error']
    current_failed = request.values['current_failed']
    tries = request.values['tries'] if 'tries' in request.values else None
    survival = request.values['survival']
    previous_failed = request.values['previous_failed']
    description = request.values['description']
    user_id = request.values['user_id']

    print(f"sync_error_track: USERID: {USERID}. [Error: {error}] tries: {tries}. --", request.values)
    return ("", 200)

@app.route("/null")
def flash_sync_error_response():
    sp_ref_cat = request.values['sp_ref_cat']

    if sp_ref_cat == "flash_sync_error":
        reason = "reload On Sync Error"
    elif sp_ref_cat == "flash_reload_quest":
        reason = "reload On End Quest"
    elif sp_ref_cat == "flash_reload_attack":
        reason = "reload On End Attack"

    print("flash_sync_error", reason, ". --", request.values)
    return redirect("/play.html")

@app.route("/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/command.php", methods=['POST'])
def command_response():
    USERID = request.values['USERID']
    user_key = request.values['user_key']
    spdebug = request.values['spdebug']
    language = request.values['language']
    client_id = request.values['client_id']

    print(f"command: USERID: {USERID}. --", request.values)

    data_str = request.values['data']
    data_hash = data_str[:64]
    assert data_str[64] == ';'
    data_payload = data_str[65:]
    data = json.loads(data_payload)

    command(USERID, data)
    
    return ({"result": "success"}, 200)


########
# MAIN #
########

print (" [+] Running server...")

if __name__ == '__main__':
    app.secret_key = 'SECRET_KEY'
    app.run(host=host, port=port, debug=False)
