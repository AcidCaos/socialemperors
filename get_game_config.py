import json
import os
import jsonpatch
import random
import time
import datetime
from bundle import MODS_DIR, CONFIG_DIR, CONFIG_PATCH_DIR
from constants import Constant

__game_config = json.load(open(os.path.join(CONFIG_DIR, "main.json"), 'r', encoding='utf-8'))
__rotation = json.load(open(os.path.join(CONFIG_DIR, "shop_rotation.json"), 'r', encoding='utf-8'))
__animals = {}

# Since we use mega patches now, better to make sure any old patches don't load as they will load after and will mess things up!
patch_ignore = [ 
	"dragon_boss_fix",
	"graveyard",
	"level_up_tips",
	"mission_goals",
	"missions_0_1",
	"new_daily_bonus",
	"soulmixer_temp",
	"unit_patch",
	"viral_offers",
	"viral_icons",
	"unit_collections",
	"soulmixer_powerup_incremented_modified",
	"soulmixer_items_data",
	"soulmixer_item",
	"3-unit_fusion",
	"fusion_output"
]

def ts_to_date(ts):
	return datetime.datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d')

def remove_duplicate_items():
	indexes = {}
	items = __game_config["items"]
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
        
		if num_duplicate:
			print(f" * Removed {num_duplicate} duplicate items from config patches")
		break

def apply_config_patch(filename):
	fname = os.path.basename(filename).split(".")[0]
	if fname.lower() not in patch_ignore:
		patch = json.load(open(filename, 'r', encoding='utf-8'))
		jsonpatch.apply_patch(__game_config, patch, in_place=True)
		print(f" * Patch applied:", fname)

# because the way this is done sucks we have to do redefine this here
def get_item(item_id):
	item_id = str(item_id)
	for item in __game_config["items"]:
		if item_id == item["id"]:
			return item
	return None

def apply_shop_rotation(ts):
	print (" [+] Setting up shop rotation...")

	_rng = random.getstate()

	seconds_interval = int(__rotation["rotation_hours"] * 3600)
	seed = ts // seconds_interval
	next_expiration_ts = (seed + 1) * seconds_interval 
	next_expiration_date = ts_to_date(next_expiration_ts)
	__game_config["globals"]["LIMITED_EDITION_EXPIRATION"] = next_expiration_date
	random.seed(seed)
	print(f" * Shop: RNG seed = {seed}\n * Shop: Limited Items will expire on {next_expiration_date}")

	# halloween settings
	spooktober = __rotation["spooktober"]
	now = datetime.datetime.today()
	is_spooktober = now.month == 10 and now.day == 31

	factions = __rotation["factions"]

	if __rotation["full_random"]:
		max_items = __rotation["max_items_full_random"]

		all_items = []
		for name in factions:
			if spooktober and name == "Halloween":
				print("skipped halloween")
				continue
			for item in factions[name]:
				
				all_items.append(item)

		random.shuffle(all_items)
		max_items = min(len(all_items), max_items)
		idx = 0
		while idx < max_items:
			item = get_item(all_items[idx])
			idx += 1
			if not item:
				continue

			item["in_store"] = "1"

		if spooktober and is_spooktober:
			for item_id in factions["Halloween"]:
				item = get_item(item_id)
				if not item:
					continue

				item["in_store"] = "1"
			print(" * Shop: Faction Halloween is now available!")

		print(f" * Shop: Enabled {max_items} random things in shop!")
	else:
		faction_names = list(factions.keys())
		random.shuffle(faction_names)
		if spooktober:
			# Remove halloween from rotation, it's always picked for halloween anyway
			faction_names.remove("Halloween")
		
		max_factions = min(__rotation["max_factions"], len(faction_names))
		chosen = []

		if spooktober and is_spooktober:
			# Always enable halloween on halloween
			max_factions -= 1
			chosen.append("Halloween")

		while max_factions > 0:
			chosen.append(faction_names[0])
			del faction_names[0]
			max_factions -= 1

		for f in chosen:
			print(f" * Shop: Faction {f} is now available!")
			for item_id in factions[f]:
				item = get_item(item_id)
				if not item:
					continue

				item["in_store"] = "1"
				
	if "always_enabled" in __rotation:
		force_enable = __rotation["always_enabled"]
		for name in force_enable:
			if name in factions:
				print(f" * Shop: FORCE-ENABLED Faction {name}!")
				for item_id in factions[name]:
					item = get_item(item_id)
					if not item:
						continue

					item["in_store"] = "1"

	random.setstate(_rng)

def apply_patches():
	print (" [+] Applying config patches...")
	for patch_file in os.listdir(CONFIG_PATCH_DIR):
		if patch_file.endswith(".json"):
			f = os.path.join(CONFIG_PATCH_DIR, patch_file)
			apply_config_patch(f)

def apply_mods():
	print (" [+] Applying mods...")
	if os.path.exists(MODS_DIR + "/mods.txt"):
		with open(MODS_DIR + "/mods.txt", "r", encoding='utf-8') as f:
			lines = f.readlines()
			f.close()

		for line in lines:
			mod = line.strip()
			if mod.startswith("#"):
				continue
			if mod != "":
				mod.replace(".json", "")
				mod_path = f"{MODS_DIR}/{mod}.json"
				if os.path.exists(mod_path):
					apply_config_patch(mod_path)
					print(" * Mod applied:", mod)

	remove_duplicate_items()

def check_unit_packs():
	print(" [+] Checking Unit Packs...")
	unit_packs = __game_config["unit_packs"]
	for pack in unit_packs:
		if "custom" in pack:
			duplicates = []
			custom = pack["custom"]
			num = len(custom)
			idx = 0
			while idx < num:
				if custom[idx]["id"] in duplicates:
					uid = custom[idx]["id"]
					pack_id = pack["id"]
					print(f" * Duplicate found: id={uid} in pack id={pack_id}")
					del custom[idx]
					num -= 1
					continue
				
				duplicates.append(custom[idx]["id"])
				idx += 1

def grab_animals():
	animal_subcats = [ 74, 75, 88 ]
	for item in __game_config["items"]:
		subcat = item["subcat_functional"]
		if int(subcat) in animal_subcats:
			if subcat not in __animals:
				__animals[str(subcat)] = []
			__animals[str(subcat)].append(int(item["id"]))

# do it
apply_patches()
apply_shop_rotation(int(time.time()))
apply_mods()
check_unit_packs()
grab_animals()

items_dict_id_to_items_index = {int(item["id"]): i for i, item in enumerate(__game_config["items"])}
items_dict_subcat_functional_to_items_index = {int(item["subcat_functional"]): i for i, item in enumerate(__game_config["items"])}
missions_dict_id_to_missions_index = {int(item["id"]): i for i, item in enumerate(__game_config["missions"])}

def get_game_config():
	return __game_config

def get_animals():
	return __animals

def game_config():
	return get_game_config()

##########
# PLAYER #
##########

def get_xp_from_level(level: int):
	return __game_config["levels"][int(level)]["exp_required"]

def get_level_from_xp(xp: int):
	i = 0
	for lvl in __game_config["levels"]:
		if lvl["exp_required"] > int(xp):
			return i
		i += 1
	return 0

def get_item_from_id(id: int):
	items_index = items_dict_id_to_items_index[int(id)] if int(id) in items_dict_id_to_items_index else None
	return __game_config["items"][items_index] if items_index is not None else None

def get_attribute_from_item_id(id: int, attribute_name: str):
	item = get_item_from_id(id)
	return item[attribute_name] if item and attribute_name in item else None

def get_name_from_item_id(id: int):
	return get_attribute_from_item_id(id, "name")

def get_item_from_subcat_functional(subcat_functional: int):
	items_index = items_dict_subcat_functional_to_items_index[int(subcat_functional)] if int(subcat_functional) in items_dict_subcat_functional_to_items_index else None
	return __game_config["items"][items_index] if items_index is not None else None

def get_mission_from_id(id: int):
	items_index = missions_dict_id_to_missions_index[int(id)] if int(id) in missions_dict_id_to_missions_index else None
	return __game_config["missions"][items_index] if items_index is not None else None

def get_attribute_from_mission_id(id: int, attribute_name: str):
	mission = get_mission_from_id(id)
	return mission[attribute_name] if mission and attribute_name in mission else None

def get_si_info(item_id):
	for si in __game_config["social_items"]:
		if si["id"] == item_id:
			return si
	return None

def get_time_machine_packet(idx):
	packets = __game_config["globals"]["TIME_MACHINE"]
	if idx >= 0 and idx < len(packets):
		return packets[idx]

	return None

def get_offer_pack_id(pack_id):
	offers = __game_config["offer_packs"]
	for pack in offers:
		if pack["id"] == pack_id:
			return pack
	return None

def get_unit_pack(pack_id):
	packs = __game_config["unit_packs"]
	for pack in packs:
		if pack["id"] == pack_id:
			return pack
	return None

def get_collection_reward(collection_id):
	rewards = __game_config["globals"]["COLLECTION_REWARDS"]
	if collection_id <= 0 or collection_id >= len(rewards):
		return None
	return rewards[collection_id]