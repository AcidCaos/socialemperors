import json
import os
import copy
import uuid

from flask import session
# from flask_session import SqlAlchemySessionInterface, current_app

__villages_dir = "./villages"
__saves_dir = "./saves"

__villages = {}  # ALL saved villages + static neighbors
'''__villages = {
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
    # Saves
    for file in os.listdir(__saves_dir):
        print(f" * Loading SAVE: village at {file}... ", end='')
        village = json.load(open(os.path.join(__saves_dir, file)))
        USERID = village["playerInfo"]["pid"]
        print("USERID:", USERID)
        __villages[str(USERID)] = village

load_saved_villages()

# New village

def new_village() -> str:
    # Generate USERID
    USERID: str = str(uuid.uuid4())
    assert USERID not in all_userid()
    # Copy init
    village = copy.copy(__initial_village)
    village["playerInfo"]["pid"] = USERID
    __villages[USERID] = village
    # Generate save_file
    save_session(USERID)
    return USERID

# Access functions

def all_userid() -> list:
    "Returns a list of the USERID of every loaded village."
    return list(__villages.keys())

def session(USERID: str) -> dict:
    return __villages[str(USERID)] if str(USERID) in __villages else None

def neighbors(USERID: str):
    # TODO 
    return {}

# Persistency

def backup_session(USERID: str):
    # TODO 
    return

def save_session(USERID: str):
    # TODO 
    file = str(USERID) + ".save.json"
    print(f" * Saving village at {file}... ", end='')
    village = json.dump(session(USERID), open(os.path.join(__saves_dir, file), 'w'), indent=4)
    print("Done.")