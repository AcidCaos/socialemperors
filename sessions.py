import json
import os

__villages_dir = "./villages"
__villages = []  # ALL villages

__initial_village = json.load(open(os.path.join(__villages_dir, "initial.json")))

__current_session = None # Current session

# Load saved villages

for file in os.listdir(__villages_dir):
    if file == "initial.json" or not file.endswith(".json"):
        continue
    print(" * Loading SAVE: village at", file)
    village = json.load(open(os.path.join(__villages_dir, file)))
    __villages.append(village)

# Set current session

# TODO 
__current_session = __initial_village

# Set current session neighbors

def session():
    # TODO 
    return __current_session

def neighbors():
    # TODO 
    return {}
