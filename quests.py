import json
import os

from bundle import QUESTS_DIR

def get_quest_map(questid):
    file = os.path.join(QUESTS_DIR, str(questid) + ".save.json")
    if not os.path.exists(file):
        return("", 404)
    d = json.load(open(file, 'r'))
    return d
