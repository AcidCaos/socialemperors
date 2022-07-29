import json

__game_config = json.load(open("./config/get_game_config.php_26_Aug_2012_no_hash.txt", 'r'))

def patch_game_config():

    # Patch Graveyard undefined global values

    __game_config["globals"]["GRAVEYARD_POTIONS"] = {
        "price": {
            "c": 100
        },
        "amount": 1
    }

    # Patch Graveyard undefined locale strings

    __game_config["localization_strings"] += [{
        "id": 1564,
        "name": "BUY_POTIONS_LABEL",
        "text": "Buy #0# potions" # TODO
    }]
    __game_config["localization_strings"] += [{
        "id": 1566,
        "name": "GET_MORE_POTIONS",
        "text": "Get more" # TODO
    }]

patch_game_config()

def get_game_config() -> dict:
    return __game_config

def game_config() -> dict:
    return get_game_config()

##########
# PLAYER #
##########

def get_xp_from_level(level: int) -> int:
    return __game_config["levels"][int(level)]["exp_required"]

def get_level_from_xp(xp: int) -> int:
    i = 0
    for lvl in __game_config["levels"]:
        if lvl["exp_required"] > int(xp):
            return i
        i += 1
    return 0

#########
# ITEMS #
#########

items_dict_id_to_items_index = {int(item["id"]): i for i, item in enumerate(__game_config["items"])}

def get_item_from_id(id: int) -> dict:
    items_index = items_dict_id_to_items_index[int(id)] if int(id) in items_dict_id_to_items_index else None
    return __game_config["items"][items_index] if items_index is not None else None

def get_attribute_from_item_id(id: int, attribute_name: str) -> str:
    item = get_item_from_id(id)
    return item[attribute_name] if item and attribute_name in item else None

def get_name_from_item_id(id: int) -> str:
    return get_attribute_from_item_id(id, "name")

############
# MISSIONS #
############

missions_dict_id_to_missions_index = {int(item["id"]): i for i, item in enumerate(__game_config["missions"])}

def get_mission_from_id(id: int) -> dict:
    items_index = missions_dict_id_to_missions_index[int(id)] if int(id) in missions_dict_id_to_missions_index else None
    return __game_config["missions"][items_index] if items_index is not None else None

def get_attribute_from_mission_id(id: int, attribute_name: str) -> str:
    mission = get_mission_from_id(id)
    return mission[attribute_name] if mission and attribute_name in mission else None