from flask import Flask, render_template, send_from_directory, request

host = '127.0.0.1'
port = 5050

app = Flask(__name__)

##########
# ROUTES #
##########

## PAGES AND RESOURCES

@app.route("/")
def index():
    return render_template("play.html")

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

@app.route("/default01.static.socialpointgames.com/static/socialempires/<path:path>")
def static_assets_loader(path):
    return send_from_directory("assets", path)

## GAME DYNAMIC

@app.route("/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/track_game_status.php", methods=['POST'])
def track_game_status():
    print("track_game_status:", request.values)
    status = request.values['status']
    installId = request.values['installId']
    user_id = request.values['user_id']
    print(f" * status={status} installId={installId} user_id={user_id}")
    return ("", 200)

@app.route("/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/get_game_config.php")
def get_game_config():
    print("get_game_config:", request.values)
    USERID = request.values['USERID']
    user_key = request.values['user_key']
    spdebug = request.values['spdebug']
    language = request.values['language']
    config = {
        # - core.Base
        "result": "ok", # "error"
        "honor_levels": [
            {"rank": "UnknownRankI", "points": 10}, 
            {"rank": "UnknownRankII", "points": 100}
        ],
        # - managers.GameDataManager
        "kompu_offers": [{
            "id": 000,
            "starts_at": 111,
            "duration": 300,
            "rewards": None,
            "hurry_up_cost": 4,
            "timer_between": None,
            "viral_icon": None,
            "game_type": None,
        }],
        "items": [], # "items": [{"id": 1}],
        "findable_items": [],
        "levels": [],
        "neighbor_assists": [],
        "map_prices": [],
        "missions": [], # "missions": [{"id": 1}],
        "magics": [], # "magics": [{"id": 1}],
        "social_items" : [], # "items": [{"id": 1}],
        "globals": {},
        "offer_packs": {},
        "level_ranking_reward": [],
        "units_collections_categories": {},
        "darts_items": [],
        "images": {},
        "tournament_type": {},
        "expansion_prices": [],
        "localization_strings": {},
    }
    return (config, 200)

@app.route("/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/get_player_info.php", methods=['POST'])
def get_player_info():
    print("get_player_info:", request.values)
    USERID = request.values['USERID']
    user_key = request.values['user_key']
    spdebug = request.values['spdebug']
    language = request.values['language']

    resp = {}

    return (resp, 200)

########
# MAIN #
########

if __name__ == '__main__':
    app.run(host=host, port=port, debug=True)
