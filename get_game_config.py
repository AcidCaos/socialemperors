import json
import os
import jsonpatch
import random
import time
import datetime
import logging

from mods import *
from bundle import MODS_DIR, CONFIG_DIR, CONFIG_PATCH_DIR
from constants import Constant
from event_system import apply_events

log = logging.getLogger('__main__')

__game_config = json.load(open(os.path.join(CONFIG_DIR, "main.json"), 'r', encoding='utf-8'))
__rotation = json.load(open(os.path.join(CONFIG_DIR, "shop_rotation.json"), 'r', encoding='utf-8'))
__shop_rotation_refresh = None
__animals = {}

# grab server settings
from server_config import get_server_config

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

def get_event_data(event_id):
	events = __game_config["collect_game"]
	for ev in events:
		event = events[ev]
		if event["id"] == event_id:
			return event
	return None

def get_event_offer(event_id):
	events = __game_config["viral_offers"]
	for ev in events:
		event = events[ev]
		if event["id"] == event_id:
			return event
	return None

def ts_to_date(ts):
	return datetime.datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d')

def date_to_ts(date_str):
	return int(datetime.datetime.strptime(date_str, "%m-%d-%Y").replace(tzinfo=datetime.timezone.utc).timestamp())

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
			log.info(f" * Removed {num_duplicate} duplicate items from config patches")
		break

def apply_config_patch(filename):
	fname = os.path.basename(filename).split(".")[0]
	if fname.lower() not in patch_ignore:
		patch = json.load(open(filename, 'r', encoding='utf-8'))
		jsonpatch.apply_patch(__game_config, patch, in_place=True)
		log.info(f" * Patch applied: {fname}")

# because the way this is done sucks we have to do redefine this here
def get_item(item_id):
	item_id = str(item_id)
	for item in __game_config["items"]:
		if item_id == item["id"]:
			return item
	return None

def check_shop_rotation(ts):
	if ts >= __shop_rotation_refresh:
		apply_shop_rotation(ts, True)
		apply_events(ts)

def _cost_str(t):
	types = {
		"c": "cash",
		"g": "gold",
		"w": "wood",
		"f": "food",
		"s": "stone",
		"x": "xp",
		"p": "potion(s)"
	}
	if t in types:
		return types[t]
	return ""

def _output_shop_factions():
	factions = __rotation["factions"]
	for faction in factions:
		log.info(f"**{faction}**")
		for item_id in factions[faction]:
			item = get_item(item_id)
			if not item:
				continue

			name = item["name"]
			cost = item["cost"]
			cost_type = _cost_str(item["cost_type"])
			log.info(f"{name} [{cost} {cost_type}]")
		log.info("")

def clear_shop_rotation():
	factions = __rotation["factions"]
	for faction in factions:
		for item_id in factions[faction]:
			item = get_item(item_id)
			if not item:
				continue

			item["in_store"] = "0"

def apply_shop_rotation(ts, refresh = False):
	if refresh:
		log.info(" [+] Refreshing shop rotation...")
	else:
		log.info(" [+] Setting up shop rotation...")

	clear_shop_rotation()

	_rng = random.getstate()

	__settings = get_server_config()["shop"]

	seconds_interval = int(__settings["rotation_hours"] * 3600)
	seed = ts // seconds_interval
	next_expiration_ts = (seed + 1) * seconds_interval
	next_expiration_date = ts_to_date(next_expiration_ts)
	global __shop_rotation_refresh
	__shop_rotation_refresh = next_expiration_ts
	__game_config["globals"]["LIMITED_EDITION_EXPIRATION"] = next_expiration_date
	random.seed(seed)
	log.info(f" * Shop: RNG seed = {seed}")
	log.info(f" * Shop: Limited Items will expire on {next_expiration_date}")

	# halloween settings
	spooktober = __settings["spooktober"]
	now = datetime.datetime.today()
	is_spooktober = now.month == 10 and now.day == 31

	factions = __rotation["factions"]

	if __settings["full_random"]:
		max_items = __settings["max_items_full_random"]

		all_items = []
		for name in factions:
			if spooktober and name == "Halloween":
				log.info("skipped halloween")
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
			log.info(" * Shop: Faction Halloween is now available!")

		log.info(f" * Shop: Enabled {max_items} random things in shop!")
	else:
		faction_names = list(factions.keys())
		random.shuffle(faction_names)
		if spooktober:
			# Remove halloween from rotation, it's always picked for halloween anyway
			faction_names.remove("Halloween")
		
		max_factions = min(__settings["max_factions"], len(faction_names))
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
			log.info(f" * Shop: Faction {f} is now available!")
			for item_id in factions[f]:
				item = get_item(item_id)
				if not item:
					continue

				item["in_store"] = "1"
				
	if "always_enabled" in __settings:
		force_enable = __settings["always_enabled"]
		for name in force_enable:
			if name in factions:
				log.info(f" * Shop: FORCE-ENABLED Faction {name}!")
				for item_id in factions[name]:
					item = get_item(item_id)
					if not item:
						continue

					item["in_store"] = "1"

	random.setstate(_rng)

def apply_server_config():
	__game_config["globals"]["PVP_TIMER_SECONDS"] = int(get_server_config()["pvp"]["time_limit_minutes"] * 60)

def apply_patches():
	log.info(" [+] Applying config patches...")
	for patch_file in os.listdir(CONFIG_PATCH_DIR):
		if patch_file.endswith(".json"):
			f = os.path.join(CONFIG_PATCH_DIR, patch_file)
			apply_config_patch(f)

def apply_mods():
	log.info(" [+] Applying mods...")
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
					apply_user_mod(mod_path, mod, __game_config)

	remove_duplicate_items()

def check_unit_packs():
	log.info(" [+] Checking Unit Packs...")
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
					log.info(f" * Duplicate found: id={uid} in pack id={pack_id}")
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
_ts = int(time.time())
apply_patches()
apply_mods()
check_unit_packs()
apply_shop_rotation(_ts)
apply_events(_ts)
apply_server_config()
grab_animals()

# access functions
items_dict_id_to_items_index = {int(item["id"]): i for i, item in enumerate(__game_config["items"])}

def get_game_config():
	return __game_config

def get_animals():
	return __animals

def game_config():
	return get_game_config()

def get_item_from_id(id: int):
	items_index = items_dict_id_to_items_index[int(id)] if int(id) in items_dict_id_to_items_index else None
	return __game_config["items"][items_index] if items_index is not None else None

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

def get_spell(spell_id):
	spells = __game_config["magics"]
	for spell in spells:
		if spell["id"] == spell_id:
			return spell
	return None

def get_mission(goal_id):
	missions = __game_config["missions"]
	for m in missions:
		if m["id"] == goal_id:
			return m
	return None

def get_hellforge_item(item_id):
	items = __game_config["collect_game_items"]
	for it in items:
		item = items[it]
		if item["id"] == item_id:
			return item
	return None