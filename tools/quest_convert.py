import os
import json
import copy
import jsonpatch
import math
from version import migrate_loaded_save

# CONFIG
quest_sources = "villages/quests/"
output_dir = "saves/"
base_map = "villages/initial.json"


def convert(filename, base):
	print(f"processing {filename}...")
	quest = json.load(open(filename, 'r', encoding='utf-8'))

	Q = copy.deepcopy(base)
	Q["playerInfo"] = quest["playerInfo"]
	Q["privateState"] = quest["privateState"]
	Q["maps"] = []
	Q["maps"].append(quest["map"])

	migrate_loaded_save(Q)

	new_path = filename.replace(".json", ".save.json")
	with open(new_path, 'w') as f:
		json.dump(Q, f, indent='\t')

for quest in os.listdir(quest_sources):
	base = json.load(open(base_map, 'r', encoding='utf-8'))
	if quest.endswith(".json"):
		f = os.path.join(quest_sources, quest)
		convert(f, base)