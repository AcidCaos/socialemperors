import os
import json
import copy
import jsonpatch
import math

from fusion_builder import fusion_build

# CONFIG
patch_filename = "../config/patch/2-unit_patch.json"
# patch_filename = "unit_patch.json"
input_csv = "se_unit_patch.csv"

# DO THE THING
templates = json.load(open("unit_templates.json", 'r', encoding='utf-8'))

num_units = 0
lines = []
patch = []
riderpatch = []
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

def dump_category_csv(cats, main_csv, sub_csv):
	_cat = []
	_sub = []
	for CAT in cats:
		cat = cats[CAT]
		if "id" in cat:
			_cat.append([
				str(cat["id"]),
				str(cat["name"])
			])
			for sub in cat["sub"]:
				_sub.append([
					str(sub["id"]),
					str(cat["id"]),
					str(sub["name"])
				])
	write_csv(_cat, main_csv)
	write_csv(_sub, sub_csv)

def get_subcat(subcat):
	cats = config["categories"]
	for CAT in cats:
		cat = cats[CAT]
		for sub in cat["sub"]:
			if sub["id"] == subcat:
				return sub["name"]
	return ""

def dump_unit_category(items, output_csv):
	csv = []
	for item in items:
		instore = ""
		isbuilding = ""
		ishuman = ""
		doestrain = ""
		if item["in_store"] != "0":
			instore = item["in_store"]
		if item["type"] == "b":
			isbuilding = "YES"
		if item["race"] == "h":
			ishuman = "YES"
		if item["trains"] != "0":
			doestrain = get_item(items, int(item["trains"]))["name"]

		csv.append([
			str(item["id"]),
			instore,
			isbuilding,
			ishuman,
			doestrain,
			"",
			get_subcat(int(item["subcategory_id"])),
			str(item["name"]),
		])

	write_csv(csv, output_csv)

def read_csv(filename, separator='\t'):
	csv = []
	with open(filename, 'r') as f:
		for line in f:
			csv.append(line.strip().split(separator))
	return csv

def write_csv(csv, filename, separator='\t'):
	with open(filename, 'w') as f:
		for item in csv:
			data = separator.join(item)
			f.write(f"{data}\n")
	print(f"wrote csv {filename}")

def shop_modify(items, csv_filename):
	print("applying new shop configuration...")
	csv = read_csv(csv_filename)

	for entry in csv:
		item_id = entry[0]
		in_store = entry[1]
		item = get_item(items, int(item_id))
		if item:
			if in_store != "":
				item["in_store"] = str(in_store)
			else:
				item["in_store"] = "0"

	
	make_shop_rotation(items, csv, "../config/shop_rotation.json")

def make_shop_rotation(items, csv, filename):
	print(f"exporting shop rotation to {filename}...")
	factions = {}
	for entry in csv:
		if len(entry) < 8:
			continue
		
		faction = entry[7]
		if faction == "CollectionReward" or faction == "Always":
			continue

		item = get_item(items, int(entry[0]))
		if not item:
			continue
		if faction not in factions:
			factions[faction] = []

		factions[faction].append(int(int(entry[0])))

	rotation = {
		"rotation_hours": 48,
		"max_factions": 2,
		"max_items_full_random": 80,
		"full_random": False,
		"spooktober": True,
		"factions": factions,
		"always_enabled": []
	}

	with open(filename, 'w') as f:
		json.dump(rotation, f)



def makeriderpatch(item_id, rider_tier, tamed_id):
	# Create patch
	p = {}
	p["op"] = "add"
	p["path"] = f"/globals/DRAGONS/{item_id}"

	value = {}
	value["rider"] = rider_tier
	value["tamedId"] = tamed_id

	p["value"] = value

	# Append to rider patch list
	print(f"Created rider patch for {ITEM_NAME}")
	riderpatch.append(p)

def apply_riderpatch(config, patch):
	print("applying rider patch")
	jsonpatch.apply_patch(config, patch, in_place = True)

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

def set_pack_chance(life, item_type):
	return int(1000 / math.ceil(int(life) / 50))

def set_pack_category(life, item_type):
	return 2

def set_pack_num(life, item_type):
	return 1

def set_unit_pack_data(item):
	if item["type"] == "b":
		return
	life = item["life"]
	item["pack_num"] = set_pack_num(life, item["type"])
	item["pack_category"] = set_pack_category(life, item["type"])
	item["pack_chance"] = str(set_pack_chance(life, item["type"]))

	name = item["name"]
	num = item["pack_num"]
	cat = item["pack_category"]
	chance = item["pack_chance"]
	print(f"applied unit pack data to {name} -> num={num}, category={cat}, chance={chance}")

def get_item(items, item_id):
	item_id = str(item_id)
	for item in items:
		if item["id"] == item_id:
			return item
	return None

def modify_item_price(items, item_id, price, price_type):
	item = get_item(items, item_id)
	if not item:
		return
	
	item["cost"] = str(price)
	item["cost_type"] = price_type
	name = item["name"]
	print(f"adjusted price of {name}")

def modify_item_xp(items, item_id, xp):
	item = get_item(items, item_id)
	if not item:
		return
	
	item["xp"] = str(xp)
	name = item["name"]
	print(f"adjusted xp of {name}")

def modify_item_upgrade(items, item_id, upgrade_item_id):
	item = get_item(items, item_id)
	if not item:
		return
	
	item["upgrades_to"] = str(upgrade_item_id)
	name = item["name"]
	print(f"set upgrade for {name}")
	
def modify_item_barrack(items, item_id, train_item_id):
	item = get_item(items, item_id)
	if not item:
		return
	
	item["trains"] = str(train_item_id)
	name = item["name"]
	print(f"set barracks training unit for {name}")

def modify_item_attack(items, item_id, attack):
	item = get_item(items, item_id)
	if not item:
		return
	
	item["attack"] = str(attack)
	name = item["name"]
	print(f"set attack power for {name}")

def modify_item_attack_range(items, item_id, attack_range):
	item = get_item(items, item_id)
	if not item:
		return
	
	item["attack_range"] = str(attack_range)
	name = item["name"]
	print(f"set attack range for {name}")

def make_final(config, patch, sm_patch):
	print(f"applying phase 1 patch...")
	jsonpatch.apply_patch(config, patch, in_place = True)

	# apply soul mixer patch
	print(f"applying fusion build patch...")
	jsonpatch.apply_patch(config, sm_patch, in_place = True)
	#apply_patch(config, sm_patch)

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
				if "pack_chance" not in item and "sm_training_time" in item:
					set_unit_pack_data(item)
					
	print(f"set training times for {num} units")

	# fix sky tower 2 incorrect size
	item = get_item(items, 1360)
	if item:
		item["width"] = 2
		item["height"] = 2
		name = item["name"]
		print(f"applied size fix to {name}")

	# modify shop items
	shop_modify(config["items"], "shop_data.csv")

	# adjust prices
	modify_item_price(items, 472, 15, "c")		# black castle
	modify_item_price(items, 414, 20, "c")		# golden castle
	modify_item_price(items, 100, 225, "g")		# yellow tree
	modify_item_price(items, 106, 225, "g")		# red tree
	modify_item_price(items, 102, 390, "g")		# happy tree	
	modify_item_price(items, 125, 700, "g")		# unused soldier statues
	modify_item_price(items, 127, 700, "g")		# unused soldier statues
	modify_item_price(items, 1233, 0, "g")		# dragon breeding nest

	# adjust item xp
	modify_item_xp(items, 106, 23)				# red tree
	modify_item_xp(items, 100, 23)				# yellow tree
	modify_item_xp(items, 125, 70)				# unused soldier statues
	modify_item_xp(items, 127, 70)				# unused soldier statues
	modify_item_xp(items, 1233, 0)				# dragon breeding nest

	# enable golden hall upgrade
	modify_item_upgrade(items, 141, 412)			# town hall 4
	modify_item_xp(items, 412, 3000)				# golden hall
	modify_item_price(items, 412, 150000, "all")	# golden hall
	modify_item_barrack(items, 412, 500)			# golden hall
	modify_item_attack(items, 412, 20)				# golden hall
	modify_item_attack_range(items, 412, 8)			# golden hall

	# build final patch
	final = []

	# items
	final.append({
		"op": "replace",
		"path": "/items",
		"value": items
	})
	# rider data
	final.append({
		"op": "replace",
		"path": "/globals/DRAGONS",
		"value": config["globals"]["DRAGONS"]
	})

	return final

print("Patch phase 2 ----------------------------------------------------------")
print("running fusion builder...")
sm_patch = fusion_build()
patches = [ "../config/patch/0-language_en.json", "../config/patch/1-mega_patch.json" ]
config = load_config("../config/main.json")
load_patches(config, patches)
apply_riderpatch(config, riderpatch)
patch_final = make_final(config, patch, sm_patch)

#dump_category_csv(config["categories"], "categories.csv", "subcategories.csv")
#dump_unit_category(config["items"], "unit_store.csv")

if len(patch) > 0:
	with open(patch_filename, 'w') as f:
		json.dump(patch_final, f)
		print(f"Created final patch to {patch_filename}!")
else:
	print("Patch creation failed!")