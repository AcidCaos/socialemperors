import json

game_config = json.load(open("./config/get_game_config.php_26_Aug_2012_no_hash.txt", 'r'))

##########
# PLAYER #
##########

def get_xp_from_level(level: int) -> int:
    return game_config["levels"][int(level)]["exp_required"]

def get_level_from_xp(xp: int) -> int:
    i = 0
    for lvl in game_config["levels"]:
        if lvl["exp_required"] > int(xp):
            return i
        i += 1
    return 0

#########
# ITEMS #
#########

items_dict_id_to_items_index = {int(item["id"]): i for i, item in enumerate(game_config["items"])}

def get_item_from_id(id: int) -> dict:
    items_index = items_dict_id_to_items_index[int(id)] if int(id) in items_dict_id_to_items_index else None
    return game_config["items"][items_index] if items_index is not None else None

def get_attribute_from_item_id(id: int, attribute_name: str) -> str:
    item = get_item_from_id(id)
    return item[attribute_name] if item and attribute_name in item else None

def get_name_from_item_id(id: int) -> str:
    return get_attribute_from_item_id(id, "name")
