import json
import os

__quests_dir = "./villages/quests"

def get_quest_map(questid):
    file = os.path.join(__quests_dir, str(questid) + ".json")
    if not os.path.exists(file):
        return("", 404)
    d = json.load(open(file, 'r'))
    return(d, 200)
