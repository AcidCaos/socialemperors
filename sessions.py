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


__villages_dir = "./villages"
__saves_dir = "./saves"

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

__initial_village = json.load(open(os.path.join(__villages_dir, "initial.json")))

# Load saved villages

def load_saved_villages():
    global __villages
    global __saves
    # Empty in memory
    __villages = {}
    __saves = {}
    # Saves dir check
    if not os.path.exists(__saves_dir):
        try:
            print(f"Creating '{__saves_dir}' folder...")
            os.mkdir(__saves_dir)
        except:
            print(f"Could not create '{__saves_dir}' folder.")
            exit(1)
    if not os.path.isdir(__saves_dir):
        print(f"'{__saves_dir}' is not a folder... Move the file somewhere else.")
        exit(1)
    # Static neighbors in /villages
    for file in os.listdir(__villages_dir):
        if file == "initial.json" or not file.endswith(".json"):
            continue
        print(f" * Loading STATIC neighbor: village at {file}... ", end='')
        village = json.load(open(os.path.join(__villages_dir, file)))
        USERID = village["playerInfo"]["pid"]
        print("USERID:", USERID)
        __villages[str(USERID)] = village
    # Saves in /saves
    for file in os.listdir(__saves_dir):
        print(f" * Loading SAVE: village at {file}... ", end='')
        try:
            save = json.load(open(os.path.join(__saves_dir, file)))
        except json.decoder.JSONDecodeError as e:
            print("Corrupted JSON.")
            continue
        USERID = save["playerInfo"]["pid"]
        print("USERID:", USERID)
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

def neighbors(USERID: str):
    neighbors = []
    # static villages
    for key in __villages:
        vill = __villages[key]
        neigh = vill["playerInfo"]
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
        if vill["playerInfo"]["pid"] != USERID:
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

# Persistency

def backup_session(USERID: str):
    # TODO 
    return

def save_session(USERID: str):
    # TODO 
    file = f"{USERID}.save.json"
    print(f" * Saving village at {file}... ", end='')
    village = session(USERID)
    with open(os.path.join(__saves_dir, file), 'w') as f:
        json.dump(village, f, indent=4)
    print("Done.")