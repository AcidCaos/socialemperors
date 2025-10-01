import os
import json
import copy
import jsonpatch
import math

# CONFIG
patch_filename = "../config/patch/2-unit_patch.json"
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

print("Patch phase 1 ----------------------------------------------------------")

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
	ITEM_TRAIN_TIME = col[19]

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
	item["training_time"] = str(ITEM_TRAIN_TIME).strip()

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

def load_config(filename):
	print(f"loading config {filename}...")
	return json.load(open(filename, 'r', encoding='utf-8'))

def load_patches(config, patches):
	for p in patches:
		apply_patch(config, p)

def apply_patch(config, filename):
	print(f"applying patch {filename}...")
	_apply_patch(config, json.load(open(filename, 'r', encoding='utf-8')))

def _apply_patch(data, p):
	jsonpatch.apply_patch(data, p, in_place = True)

def remove_duplicate_items(config):
	indexes = {}
	items = config["items"]
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
		break

	print(f"removed {num_duplicate} duplicate items")

def set_training_time(life):
	amount = int(life)
	if amount < 1000:
		return math.ceil(amount / 100) * 5
	return math.ceil(amount / 100) * 30

def get_item(items, item_id):
	item_id = str(item_id)
	for item in items:
		if item["id"] == item_id:
			return item
	return None

def make_final(config, patch, sm_patch):
	print(f"applying phase 1 patch...")
	jsonpatch.apply_patch(config, patch, in_place = True)

	# apply soul mixer patch
	apply_patch(config, sm_patch)

	# remove duplicates
	remove_duplicate_items(config)

	# now define training time for units
	items = config["items"]
	num = 0
	for item in items:
		if item["type"] == "u":
			if "training_time" not in item:
				life = item["life"]
				item["training_time"] = set_training_time(life)
				num += 1
	print(f"set training times for {num} units")

	# fix sky tower 2 incorrect size
	item = get_item(items, 1360)
	if item:
		item["width"] = 2
		item["height"] = 2
		name = item["name"]
		print(f"applied size fix to {name}")

	# build final patch
	final = []
	final.append({
		"op": "replace",
		"path": "/items",
		"value": items
	})
	return final

print("Patch phase 2 ----------------------------------------------------------")
patches = [ "../config/patch/0-language_en.json", "../config/patch/1-mega_patch.json" ]
sm_patch = "fusion_output.json"
config = load_config("../config/main.json")
load_patches(config, patches)
patch_final = make_final(config, patch, sm_patch)

if len(patch) > 0:
	with open(patch_filename, 'w') as f:
		json.dump(patch_final, f)
		print(f"Created final patch to {patch_filename}!")
else:
	print("Patch creation failed!")