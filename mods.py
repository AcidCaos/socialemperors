import json
import os
import jsonpatch
import logging

log = logging.getLogger('__main__')

_supported_mod_versions = "rewrite"
_required_fields = {
	"name": "",
	"author": "",
	"description": "",
	"game": "",
	"supports": [],
	"data": []
}

def apply_user_mod(path, mod_name, config):
	mod = json.load(open(path, "r", encoding='utf-8'))

	if type(mod) != dict:
		log.info(f" * [{mod_name}] Wrong mod format!")
		return False

	if not check_fields(mod, mod_name):
		log.info(f" * [{mod_name}] Incorrect mod structure!")
		return False

	if mod["game"] != "Social Empires":
		log.info(f" * [{mod_name}] Mod does not support this game!")
		return False

	if _supported_mod_versions not in mod["supports"]:
		log.info(f" * [{mod_name}] Mod does not support this version!")
		return False

	status = try_apply_mod(mod["data"], mod_name, config)
	if status:
		_apply(config, mod, mod_name)
	else:
		name = mod["name"]
		author = mod["author"]
		log.info(f" * [{mod_name}] {name} by {author} -> FAILED!")
		return False

def try_apply_mod(data, mod_name, config):
	# check changes

	errors = 0
	for p in data:
		if p["op"] == "replace":
			if p["path"].lower().startswith("/items"):
				log.info(f" * [{mod_name}] Replace operation on items is not allowed!")
				errors += 1

		elif p["op"] == "add":
			if p["path"].lower() == "/items/-":
				# check if item changes are valid
				item = p["value"]
				if item["type"] == "u":
					if not check_item_mod(item, config, mod_name):
						name = item["name"]
						item_id = item["id"]
						log.info(f" * [{mod_name}] Invalid item modification: [{item_id}] {name}!")
						errors += 1

		elif p["op"] == "remove":
			log.info(f" * [{mod_name}] Remove operation is not allowed!")
			errors += 1

	return errors == 0

def check_fields(mod, mod_name):
	errors = 0
	for key in _required_fields:
		if key not in mod:
			log.info(f" * [{mod_name}] Field \"{key}\" is missing!")
			errors += 1
			continue
		if type(mod[key]) != type(_required_fields[key]):
			log.info(f" * [{mod_name}] Field \"{key}\" is wrong type!")
			errors += 1
			continue

	return errors == 0

def check_item_mod(item, config, mod_name):
	og = get_item(config, int(item["id"]))
	if not og:
		# new item - some data must exist
		if "pack_num" not in item:
			return False
		if "pack_category" not in item:
			return False
		if "pack_chance" not in item:
			return False
		if "training_time" not in item:
			return False
		# SM data not necessary here

	else:
		# existing item - data must not be removed
		if "pack_num" not in item and "pack_num" in og:
			return False
		if "pack_category" not in item and "pack_category" in og:
			return False
		if "pack_chance" not in item and "pack_chance" in og:
			return False
		if "training_time" not in item and "training_time" in og:
			return False
		if "sm_training_time" not in item and "sm_training_time" in og:
			return False
		if "breeding_order" not in item and "breeding_order" in og:
			return False

	return True

def get_item(config, item_id):
	for item in config["items"]:
		if int(item["id"]) == item_id:
			return item
	return None

def _apply(config, mod, mod_name):
	jsonpatch.apply_patch(config, mod["data"], in_place=True)
	name = mod["name"]
	author = mod["author"]
	log.info(f" * [{mod_name}] {name} by {author} -> MOD ACTIVE!")
	return True