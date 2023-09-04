import os
import json
import copy

# CONFIG
patch_filename = "../config/patch/unit_patch.json"
# patch_filename = "unit_patch.json"
input_csv = "se_unit_patch.csv"

# DO THE THING
templates = json.load(open("unit_templates.json", 'r', encoding='utf-8'))

num_units = 0
lines = []
patch = []
storage = {}
if os.path.exists(input_csv):
	with open(input_csv, "r", encoding='utf-8') as f:
		lines = f.readlines()
		f.close()

def trimquotes(inputstr: str):
	new = inputstr
	while not new.startswith("{"):
		new = inputstr[1:]
	while not new.endswith("}"):
		new = new [:-1]
	return new

def makeriderpatch(item_id, rider_tier, tamed_id):
	# Create patch
	p = {}
	p["op"] = "add"
	p["path"] = f"/globals/DRAGONS/{item_id}"

	value = {}
	value["rider"] = rider_tier
	value["tamed_id"] = tamed_id

	p["value"] = value

	# Append to rider patch list
	print(f"Created rider patch for {ITEM_NAME}")
	patch.append(p)

for line in lines:
	col = line.split("\t")

	ITEM_ID = col[0]
	ITEM_ASSET = col[1]
	ITEM_NAME = col[2]
	ITEM_HEALTH = col[3]
	ITEM_ATTACK = col[4]
	ITEM_RANGE = col[5]
	ITEM_INTERVAL = col[6]
	ITEM_SPEED = col[7]
	ITEM_POPULATION = col[8]
	ITEM_POTIONS = col[9]
	ITEM_XP = col[10]
	ITEM_CASH_COST = col[11]
	ITEM_COST_VALUE = col[12]
	ITEM_COST_TYPE = col[13]
	ITEM_FLYING = col[14]
	ITEM_GROUPS = col[15]
	ITEM_STORE_GROUPS = col[16]
	ITEM_RIDER_TIER = col[17]
	ITEM_TAMED_ID = col[18]

	if ITEM_ASSET == "":
		print(f"FAILED: {ITEM_NAME} - Asset missing")
		continue

	if ITEM_GROUPS not in templates:
		print(f"FAILED: {ITEM_NAME} - Template {ITEM_GROUPS} not found")
		continue

	# Fetch from template
	template = templates[ITEM_GROUPS]
	item = copy.deepcopy(template)

	# Update data
	item["id"] = str(ITEM_ID)
	item["img_name"] = str(ITEM_ASSET)
	item["name"] = str(ITEM_NAME)
	item["life"] = str(ITEM_HEALTH)
	item["attack"] = str(ITEM_ATTACK)
	item["attack_range"] = str(ITEM_RANGE)
	item["velocity"] = str(ITEM_SPEED)
	item["attack_interval"] = str(ITEM_INTERVAL)
	item["population"] = str(ITEM_POPULATION)
	item["potions"] = str(ITEM_POTIONS)
	item["xp"] = str(ITEM_XP)
	item["flying"] = str(ITEM_FLYING)
	item["cost_unit_cash"] = ITEM_CASH_COST.replace("\\","")
	item["cost"] = str(ITEM_COST_VALUE)
	item["cost_type"] = str(ITEM_COST_TYPE)
	item["groups"] = str(ITEM_GROUPS)
	item["store_groups"] = str(ITEM_STORE_GROUPS)

	# Create patch
	p = {}
	p["op"] = "add"
	p["path"] = "/items/-"
	p["value"] = item

	# Append to patch
	patch.append(p)
	num_units += 1
	# Append to storage
	storage[str(ITEM_ID)] = 1

	# If there's a rider unit make a patch
	if ITEM_RIDER_TIER != "" and ITEM_TAMED_ID != "":
		makeriderpatch(str(ITEM_ID), str(ITEM_RIDER_TIER), str(ITEM_TAMED_ID.replace('\n','')))

	print(f"Made unit patch for {ITEM_NAME}")

if len(patch) > 0:
	with open(patch_filename, 'w') as f:
		json.dump(patch, f)
	# with open(output_storage, 'w') as f:
	# 	json.dump(storage, f)
		print(f"Created patch for {num_units} items to {patch_filename}!")
else:
	print("Patch creation failed!")