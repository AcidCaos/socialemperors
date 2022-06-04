import json

game_config = json.load(open("./config/get_game_config.php_no_hash.txt", 'r'))

old_game_config = {
    # - core.Base
    "result": "ok", # "error"
    "honor_levels": [
        {
            "id": 1,
            "points": 0,
            "rank": "Peasant with Spear"
        },
        {
            "id": 2,
            "points": 50,
            "rank": "Count's Squire"
        }
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
            # - Base.processMap (_loc22_ = [...])
            "activation": 3.14,
            "collect": 1,
            "collect_type": "",
            "collect_xp": 0,
            "category_id": 1, #  CAT_BUILDING_TOWN:uint = 1; CAT_BUILDING_WAR:uint = 2; CAT_BUILDING_TROOPS:uint = 3; .... 7.
            "type": 0,
            "img_name": "Unknown_Image_name",
        },
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