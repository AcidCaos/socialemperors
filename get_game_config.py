import json
import os
import jsonpatch
from bundle import MODS_DIR, CONFIG_DIR, CONFIG_PATCH_DIR

__game_config = json.load(open(os.path.join(CONFIG_DIR, "game_config_20120826.json"), 'r', encoding='utf-8'))

def remove_duplicate_items():
    indexes = {}
    items = __game_config["items"]
    num_duplicate = 0

    while True:
        index = 0
        duplicate = False
        for item in items:
            if item["id"] in indexes:
                del items[indexes[item["id"]]]
                indexes.clear()
                duplicate = True
                num_duplicate += 1
                break

            indexes[item["id"]] = index
            index += 1

        if duplicate:
            continue
        
        if num_duplicate:
            print(f" * Removed {num_duplicate} duplicate items from config patches")
        break

def apply_config_patch(filename):
    patch = json.load(open(filename, 'r'))
    jsonpatch.apply_patch(__game_config, patch, in_place=True)

def patch_game_config():

    # Apply patches

    for patch_file in os.listdir(CONFIG_PATCH_DIR):
        if patch_file.endswith(".json"):
            f = os.path.join(CONFIG_PATCH_DIR, patch_file)
            apply_config_patch(f)
            patch = patch_file.replace(".json", "")
            print(" * Patch applied:", patch)

    # Apply mods

    if os.path.exists(MODS_DIR + "/mods.txt"):
        with open(MODS_DIR + "/mods.txt", "r") as f:
            lines = f.readlines()
            f.close()

        for line in lines:
            mod = line.strip()
            if mod.startswith("#"):
                continue
            if mod != "":
                mod.replace(".json", "")
                mod_path = f"{MODS_DIR}/{mod}.json"
                if os.path.exists(mod_path):
                    apply_config_patch(mod_path)
                    print(" * Mod applied:", mod)

    remove_duplicate_items()

print (" [+] Applying config patches and mods...")
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

# ID

items_dict_id_to_items_index = {int(item["id"]): i for i, item in enumerate(__game_config["items"])}

def get_item_from_id(id: int) -> dict:
    items_index = items_dict_id_to_items_index[int(id)] if int(id) in items_dict_id_to_items_index else None
    return __game_config["items"][items_index] if items_index is not None else None

def get_attribute_from_item_id(id: int, attribute_name: str) -> str:
    item = get_item_from_id(id)
    return item[attribute_name] if item and attribute_name in item else None

def get_name_from_item_id(id: int) -> str:
    return get_attribute_from_item_id(id, "name")

# subcat_functional

items_dict_subcat_functional_to_items_index = {int(item["subcat_functional"]): i for i, item in enumerate(__game_config["items"])}

def get_item_from_subcat_functional(subcat_functional: int) -> dict:
    items_index = items_dict_subcat_functional_to_items_index[int(subcat_functional)] if int(subcat_functional) in items_dict_subcat_functional_to_items_index else None
    return __game_config["items"][items_index] if items_index is not None else None

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