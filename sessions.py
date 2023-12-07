import json
import os
import copy
import uuid
import random
from flask import session
# from flask_session import SqlAlchemySessionInterface, current_app

from version import version_code
from engine import timestamp_now
from version import migrate_loaded_save
from constants import Constant

from bundle import VILLAGES_DIR, SAVES_DIR

__villages = {}  # ALL static neighbors
'''__villages = {
    "USERID_1": {
        "playerInfo": {...},
        "maps": [{...},{...}]
        "privateState": {...}
    },
    "USERID_2": {...}
}'''

__saves = {}  # ALL saved villages
'''__saves = {
    "USERID_1": {
        "playerInfo": {...},
        "maps": [{...},{...}]
        "privateState": {...}
    },
    "USERID_2": {...}
}'''

__initial_village = json.load(open(os.path.join(VILLAGES_DIR, "initial.json")))

# Load saved villages

def load_saved_villages():
    global __villages
    global __saves
    # Empty in memory
    __villages = {}
    __saves = {}
    # Saves dir check
    if not os.path.exists(SAVES_DIR):
        try:
            print(f"Creating '{SAVES_DIR}' folder...")
            os.mkdir(SAVES_DIR)
        except:
            print(f"Could not create '{SAVES_DIR}' folder.")
            exit(1)
    if not os.path.isdir(SAVES_DIR):
        print(f"'{SAVES_DIR}' is not a folder... Move the file somewhere else.")
        exit(1)
    # Static neighbors in /villages
    for file in os.listdir(VILLAGES_DIR):
        if file == "initial.json" or not file.endswith(".json"):
            continue
        print(f" * Loading static neighbour {file}... ", end='')
        village = json.load(open(os.path.join(VILLAGES_DIR, file)))
        if not is_valid_village(village):
            print("Invalid neighbour")
            continue
        USERID = village["playerInfo"]["pid"]
        if str(USERID) in __villages:
            print(f"Ignored: duplicated PID '{USERID}'.")
        else:
            __villages[str(USERID)] = village
            print("Ok.")
    # Saves in /saves
    for file in os.listdir(SAVES_DIR):
        print(f" * Loading save at {file}... ", end='')
        try:
            save = json.load(open(os.path.join(SAVES_DIR, file)))
        except json.decoder.JSONDecodeError as e:
            print("Corrupted JSON.")
            continue
        if not is_valid_village(save):
            print("Invalid Save.")
            continue
        USERID = save["playerInfo"]["pid"]
        try:
            map_name = save["playerInfo"]["map_names"][ save["playerInfo"]["default_map"] ]
        except:
            map_name = '?'
        print(f"({map_name}) Ok.")
        __saves[str(USERID)] = save
        modified = migrate_loaded_save(save) # check save version for migration
        if modified:
            save_session(USERID)

# New village

def new_village() -> str:
    # Generate USERID
    USERID: str = str(uuid.uuid4())
    assert USERID not in all_userid()
    # Copy init
    village = copy.deepcopy(__initial_village)
    # Custom values
    village["version"] = version_code
    village["playerInfo"]["pid"] = USERID
    village["maps"][0]["timestamp"] = timestamp_now()
    village["privateState"]["dartsRandomSeed"] = abs(int((2**16 - 1) * random.random()))
    # Memory saves
    __saves[USERID] = village
    # Generate save file
    save_session(USERID)
    print("Done.")
    return USERID

# Access functions

def all_saves_userid() -> list:
    "Returns a list of the USERID of every saved village."
    return list(__saves.keys())

def all_userid() -> list:
    "Returns a list of the USERID of every village."
    return list(__villages.keys()) + list(__saves.keys())

def save_info(USERID: str) -> dict:
    save = __saves[USERID]
    default_map = save["playerInfo"]["default_map"]
    empire_name = str(save["playerInfo"]["map_names"][default_map])
    xp = save["maps"][default_map]["xp"]
    level = save["maps"][default_map]["level"]
    return{"userid": USERID, "name": empire_name, "xp": xp, "level": level}

def all_saves_info() -> list:
    saves_info = []
    for userid in __saves:
        saves_info.append(save_info(userid))
    return list(saves_info)

def session(USERID: str) -> dict:
    assert(isinstance(USERID, str))
    return __saves[USERID] if USERID in __saves else None

def neighbor_session(USERID: str) -> dict:
    assert(isinstance(USERID, str))
    if USERID in __saves:
        return __saves[USERID]
    if USERID in __villages:
        return __villages[USERID]

def neighbors(USERID: str):
    neighbors = []
    # static villages
    for key in __villages:
        vill = __villages[key]
        # Avoid Arthur being loaded as multiple neigtbors.
        if vill["playerInfo"]["pid"] == Constant.NEIGHBOUR_ARTHUR_GUINEVERE_1 \
        or vill["playerInfo"]["pid"] == Constant.NEIGHBOUR_ARTHUR_GUINEVERE_2 \
        or vill["playerInfo"]["pid"] == Constant.NEIGHBOUR_ARTHUR_GUINEVERE_3:
            continue
        neigh = vill["playerInfo"]
        neigh["pic"] = vill["maps"][0]["pic"] if "pic" in vill["maps"][0] else None
        neigh["coins"] = vill["maps"][0]["coins"]
        neigh["xp"] = vill["maps"][0]["xp"]
        neigh["level"] = vill["maps"][0]["level"]
        neigh["stone"] = vill["maps"][0]["stone"]
        neigh["wood"] = vill["maps"][0]["wood"]
        neigh["food"] = vill["maps"][0]["food"]
        neigh["stone"] = vill["maps"][0]["stone"]
        neighbors += [neigh]
    # other players
    for key in __saves:
        vill = __saves[key]
        if vill["playerInfo"]["pid"] == USERID:
            continue
        neigh = vill["playerInfo"]
        neigh["coins"] = vill["maps"][0]["coins"]
        neigh["xp"] = vill["maps"][0]["xp"]
        neigh["level"] = vill["maps"][0]["level"]
        neigh["stone"] = vill["maps"][0]["stone"]
        neigh["wood"] = vill["maps"][0]["wood"]
        neigh["food"] = vill["maps"][0]["food"]
        neigh["stone"] = vill["maps"][0]["stone"]
        neighbors += [neigh]
    return neighbors

# Check for valid village
# The reason why this was implemented is to warn the user if a save game from Social Wars was used by accident

def is_valid_village(save: dict):
    if "playerInfo" not in save or "maps" not in save or "privateState" not in save:
        # These are obvious
        return False
    for map in save["maps"]:
        if "oil" in map or "steel" in map:
            return False
        if "stone" not in map or "food" not in map:
            return False
        if "items" not in map:
            return False
        if type(map["items"]) != list:
            return False

    return True

# Persistency

def backup_session(USERID: str):
    # TODO 
    return

def save_session(USERID: str):
    # TODO 
    file = f"{USERID}.save.json"
    print(f" * Saving village at {file}... ", end='')
    village = session(USERID)
    with open(os.path.join(SAVES_DIR, file), 'w') as f:
        json.dump(village, f, indent=4)
    print("Done.")