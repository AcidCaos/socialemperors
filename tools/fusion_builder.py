import json
import jsonpatch
import math
import os

# Paths
path_sprites = "..\\assets\\buildingsprites\\"
path_thumbs = "..\\assets\\buildingthumbs\\"
file_ext_sprite = ".swf"
file_ext_thumb = ".jpg"

# Error handling
fail_on_missing_sprite = True
fail_on_missing_thumb = False


def apply_patch(filename):
	patch = json.load(open(f"../config/patch/{filename}.json", 'r', encoding='utf-8'))
	jsonpatch.apply_patch(config, patch, in_place=True)

# Load config
config = json.load(open("../config/main.json"))
# Apply required patches
patches = [ "0-language_en", "1-mega_patch", "2-unit_patch" ]
for patch in patches:
	apply_patch(patch)

# Load list of excluded units from Atom Fusion
exclude_list = json.load(open("fusion_excluded_units.json", 'r'))
exclude_groups = [ "worker", "cow", "sheep", "cart", "siege", "horse", "boar", "kamikaze" ]
exclude_races = [ "t", "n", "e", "a" ]


def must_exclude(item):
	# exclude non-unit items

	item_id = int(item["id"])

	if item["type"] != "u" \
	  or "chained" in item["name"].lower() \
	  or item_id in exclude_list \
	  or item_id >= 2241 and item_id < 2400 \
	  or item["race"].lower().strip() in exclude_races:
		# print(f'Excluded [{item["id"]}]{item["name"]}')
		return True
	
	groups = item["groups"].lower().split(" ")
	for group in groups:
		if group.strip() in exclude_groups:
			return True
		if group.strip() == "dragon" and "rider" in item["name"].lower():
			return True	# exclude dragon rider combos

	return False

def asset_missing(item):
	img_names = item["img_name"].split(",")

	fail = False
	for img_name in img_names:
		sprite = f"{path_sprites}{img_name}{file_ext_sprite}"
		thumb = f"{path_thumbs}{img_name}{file_ext_thumb}"
		if not os.path.exists(sprite):
			print(f"MISSING SPRITE: {sprite}")
			if fail_on_missing_sprite:
				fail = True
		if not os.path.exists(thumb):
			print(f"MISSING THUMBNAIL: {thumb}")
			if fail_on_missing_thumb:
				fail = True

	return fail

# Breeding order formulas

def breeding_order_simple(a, ar, ai, d, l, v):
	return int( (10 * a * ar)/(ai + 1) + (10 * d) + (l/100) + v )

def breeding_order_tier_based(a, ar, ai, d, l, v):
	dps = a / (ai / 30)
	breeding_order = 1
	if l > 8000: # TIER 4
		breeding_order = int(max(220, min(2000, -510 + pow(l / 900, 3) + pow(dps * 1, 0.5))))
	elif l > 2500: # TIER 3
		breeding_order = int(max(150, min(219, 150 + pow(l / 1100, 2) + pow(dps * 1, 0.5))))
	elif l > 1600: # TIER 2
		breeding_order = int(max(75, min(149, 10 + pow(l / 225, 2) + pow(dps * 5, 0.5))))
	else: # TIER 1
		breeding_order = int(max(1, min(74, -4 + pow(l / 200, 2) + pow(dps * 5, 0.5))))
	sm_training_time = 1000 * breeding_order # in seconds
	return breeding_order

def breeding_order_health(a, ar, ai, d, l, v):
	return min(int(l/20), 240)

def breeding_order_simple2(a, ar, ai, d, l, v):
	print("attack", a, "range", ar, "interval", ai, "defense", d, "life", l, "vel", v)
	return int( (10 * a * ar)/(ai + 1) + (l/10) + v )

# def tests(items):
# 	types = []
# 	races = []
# 	groups = []
# 	for item in items:
# 		if item["type"] not in types:
# 			types.append(item["type"])
# 		if item["race"] not in races:
# 			races.append(item["race"])
# 		for group in item["groups"].split(" "):
# 			if group not in groups:
# 				groups.append(group)
# 
# 	for item in items:
# 		if must_exclude(item):
# 			print(f'EXCLUDED [{item["id"]}]{item["name"]}')
# 		else:
# 			print(f'OK       [{item["id"]}]{item["name"]}')
# 
# 	print(f"races: {races}")
# 	print(f"types: {types}")
# 	print(f"groups: {groups}")
# 
# tests(config["items"])

patch_str = ""
bool_first = True
for index, item in enumerate(config["items"]):

	if must_exclude(item):
		continue
	if asset_missing(item):
		print(f'EXCLUDED [{item["id"]}]{item["name"]}')
		continue

	# some config values for the formula
	a = int(item["attack"])
	ar = int(item["attack_range"])
	ai = int(item["attack_interval"])
	d = int(item["defense"])
	l = int(item["life"])
	v = int(item["velocity"])

	# some way to approximate power (aka breeding order)
	breeding_order = breeding_order_health(a, ar, ai, d, l, v)
	sm_training_time = 2000 * breeding_order # in seconds

	# make patch
	patch_breeding_order = {
		"op": "add",
		"path": f"/items/{index}/breeding_order",
		"value": f"{breeding_order}"
	}
	sm_training_time_order = {
		"op": "add",
		"path": f"/items/{index}/sm_training_time",
		"value": f"{sm_training_time}"
	}

	print(f'{breeding_order} = [{item["id"]}]{item["name"]}')

	patch_str += ("[" if bool_first else ",") + "\n\n" + json.dumps(patch_breeding_order) + ",\n" + json.dumps(sm_training_time_order)
	bool_first = False

patch_str += "\n\n]"

# write patch file
fd = open("../config/patch/4-fusion.json", 'w')
fd.write(patch_str)
fd.close()