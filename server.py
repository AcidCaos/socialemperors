import os
from flask import Flask, render_template, send_from_directory, request
from flask.debughelpers import attach_enctype_error_multidict

host = '127.0.0.1'
port = 5050

app = Flask(__name__)

if os.name == 'nt':
    os.system("color")

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
        "items": [ # StaticData for items (buildings...)
            {
                "id": 0, # (used in StaticDataLib.getItem(0)) this is the list index, not building/item id. Must start at 0, then 1, and so on.
            }
        ],
        "findable_items": [],
        "levels": [ # must have playerInfo.map.level entries.  See the very end of PlayerStatus.Init()
            {"exp_required": 1},
            {"exp_required": 10},
            {"exp_required": 50},
            {"exp_required": 100},
        ],
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
    neighbors = request.values['neighbors']
    client_id = request.values['client_id']

    player = {
        # - core.Base
        "result": "ok", # "error"
        "processed_errors": 1,
        "timestamp": 12345,
        "playerInfo": {
            "cash": 888,
            "world_id": 35684,
            "default_map": 0,
            "map_names": ["map1", "map2"],
            "map_sizes": [0, 0],
        },
        # - managers.PlayerStatus
        "map": {
            "id": 0, # TODO compared with 0
            "expansions": [7,8,9,12,14,17,18,19], # [0]=13 ???
            "timestamp": 12345,
            "coins": 888,
            "xp": 100,
            "level": 3,
            "stone": 40,
            "wood": 41,
            "food": 42,
            "race": "h",
            "skin": 0,
            "idCurrentTreasure": 222,
            "timestampLastTreasure": 12345,
            "resourcesTraded": {},
            "receivedAssists": {},
            "increasedPopulation": 0,
            "expirableUnitsTime": {},
            "items": [
                # core.BuildingReference
                [
                    {
                        "id": 0, # this is the list index, not building/item id. Must start at 0, 1, and so on.
                        "tx": 2,
                        "ty": 2,
                        "x": 33,
                        "y": 22,
                        "zIndex": 0,
                        "frame": 0,
                        "sort": 0,
                        "otx": 0,
                        "oty": 0,
                        "mc": {}, # core.IsoEngine.IsoElement
                        "building": { # StaticData
                            "id": 0, # building/item id. Constants.ID_BUILDING_HOUSE_1
                            "name": "UnknownBuilding",
                            "img_name": "Unknown_Image_name",
                            "type": "b", # Constants.TYPE_BUILDING:String = "b"; Constants.TYPE_UNIT:String = "u";
                            "xp": 12,
                            "display_order": 0,
                            "category_id": 1,
                            "subcategory_id": 0,
                            "subcat_functional": 0,
                            "min_level": 1,
                            "width": 2,
                            "height": 2,
                            "in_store": 1,
                            "new_item": 1, # 0 or 1 (boolean, but Integer represented)
                            "giftable": 1, # 0 or 1 (boolean, but Integer represented)
                            "groups": "unknownFormatGroup:String",
                            "frame": 0,
                            "max_frame": 1,
                            "elevation": 0,
                            "attack": 2,
                            "defense": 2,
                            "life": 8,
                            "velocity": 15,
                            "attack_range": 7,
                            "attack_interval": 20,
                            "population": 3,
                            "race": "", #race represented by string (usually a single character)
                            "flying": 0, # 0 or 1 (boolean, but Integer represented)
                            "protect": 0, # 0 or 1 (boolean, but Integer represented)
                            "potion": 0,
                            "achievement": 0, # 0 or 1 (boolean, but Integer represented)
                            "upgrades_to": 0, # probably an item id
                            "units_limit": 0,
                            "size": 1,
                            "giftId": 0, # unknown type
                            "iphone_id": 0, # unknown type
                            "store_level": 1,
                            "cost": 13,
                            "cost_type": "",
                            "cost_unit_cash": 1,
                            "activation": 3.14,
                            "collect": 1,
                            "collect_type": "",
                            "collect_xp": 0,
                            "unit_capacity": 5,
                            "trains": 0,
                            "build_time": 300, # unknown type
                            "subcategory2_id": 0,
                            "only_mobile": 1,
                        },
                        "loaded_": { # DynamicData

                        },
                    #     setUpBuildings    [processMap() loadedMap array build]
                    #     **************    *********************************************
                    },  # "id"          --> _loc14_ = int(_loc7_[0]);
                    33, # "x"           --> _loc15_ = _loc7_[1];
                    22, # "y"           --> _loc16_ = _loc7_[2];
                    0,  # "orientation" --> _loc17_ = _loc7_[3];
                    0,  # "collected_at"--> _loc31_ = _loc7_[4];
                    0,  # "level"       --> _loc19_ = _loc7_[5] OR 0
                    [], # "units"       --> _loc20_ = _loc7_[6] OR []
                    {}, # "attrs"       --> _loc21_ = _loc7_[7] OR {}
                    #                                 ^
                    #                                 L "_loc7_" is THIS array! :: (from processMap): _loc7_ = ---.serverItem = item = player.map.items[x]
                ],
            ],
        },
        "privateState": {
            "unlockedEarlyBuildings": {
                # "ItemName": True,
            },
            "completedMissions": [
                # "MissionName",
            ],
            "rewardedMissions": [
                # "MissionName",
            ],
            "potion": 0,
            "neighborAssists": {
                # "u1111": 1231     # "u" + neighbor.pid
            },
            "kompuSpells": 0,
            "kompuLastTimeStamp": 1,
            "kompuSteps": [],
            "kompuCompleted": [],
            "lastUpgrades": [],

            "unlockedSkins": {},
            "unlockedQuestIndex": 0,
            "questsRank": {},
            "magics": {},
            "mana": 777,
            "boughtUnits": [],
            "unitCollectionsCompleted": [],
            "dragonNumber": 0,
            "stepNumber": 0,
            "timeStampTakeCare": 12345,
            "monsterNumber": 0,
            "stepMonsterNumber": 0,
            "timeStampTakeCareMonster": 12345,
            "riderNumber": 0,
            "riderStepNumber": 0,
            "riderTimeStamp": 12345,
            "timeStampHeavySiegePeriod": 0,
            "timeStampHeavySiegeAttack": 0,
            "timeStampDartsReset": 0,
            "timeStampDartsNewFree": 0,
            "dartsBalloonsShot": [],
            "dartsRandomSeed": 10000000000001,
            "dartsHasFree": True,
            "dartsGotExtra": True,
            "countTimePacket": [],
            "infoShowed": [],
            #"teams": None, # ReferenceError: Error #1069: Property tournament not found on String and there is no default value.
            "teams": { # if(!(this.privateState["teams"][Config.TEAM_TOURNAMENT] is Array))
                "tournament": None,
            },
            "timestampLastBonus": 0,
        },
        "neighbors": [
            {
                "pid": 1111,
                "name": "Neighbor1",
                "xp": 300,
                "level": 12,
                "world_id": 35643,
            }
        ]
    }

    return (player, 200)

########
# MAIN #
########

if __name__ == '__main__':
    app.run(host=host, port=port, debug=True)
