# Darts manager reused from SW codebase
# Altered to work for SE

import json
import logging
import time
import datetime

log = logging.getLogger('__main__')

def refresh_darts(config, ts):
	# darts
	if "darts_items" in config:
		# 0 no debug
		# 1 debug wrap dates
		# 2 debug all start dates and prizes
		# 3 debug everything
		debug = 0

		# grab start date of last item as it is used as the wrap point
		darts_items = config["darts_items"]
		last_game = darts_items[-1]
		ts_last = time.mktime(datetime.datetime.strptime(last_game["start_date"], "%Y-%m-%d %H:%M:%S").timetuple())
		ts_now = ts

		# this has to be a loop because working with dates is stupid, and this ensures correct wrapping
		last_ts = ts_last
		wraps = 0
		while ts_now >= last_ts:
			last_ts = _update_darts(config, darts_items, last_ts, 0, ts_now, debug - 1)
			wraps += 1
			if debug > 0:
				next_wrap = datetime.datetime.fromtimestamp(last_ts).strftime("%Y-%m-%d %H:%M:%S")
				log.info(f"[DEBUG] Next darts date wrap is on {next_wrap}")

		log.info(f" * Darts: Minigame dates up to date -> {wraps} wraps!")

# updates darts start dates
def _update_darts(config, darts_items, ts_first, seconds, ts_now, debug = 0):
	week_length = 604800
	shift = seconds
	last_ts = 0
	for game in darts_items:
		# we ignore the date in config and just rebuild dates based on first date in config starting on monday
		ts = time.mktime(datetime.datetime.strptime(game["start_date"], "%Y-%m-%d %H:%M:%S").timetuple())
		new_date = datetime.datetime.fromtimestamp(ts_first + shift)

		# account for daylight savings
		if new_date.hour == 23:
			shift += 3600
			new_date = datetime.datetime.fromtimestamp(ts_first + shift)
		elif new_date.hour == 1:
			shift -= 3600
			new_date = datetime.datetime.fromtimestamp(ts_first + shift)
			
		# fix to nearest monday
		weekday = new_date.isoweekday()
		if weekday == 2:
			shift -= 86400
			new_date = datetime.datetime.fromtimestamp(ts_first + shift)
		elif weekday == 3:
			shift -= 86400 * 2
			new_date = datetime.datetime.fromtimestamp(ts_first + shift)
		elif weekday == 4:
			shift -= 86400 * 3
			new_date = datetime.datetime.fromtimestamp(ts_first + shift)
		elif weekday == 5:
			shift += 86400 * 3
			new_date = datetime.datetime.fromtimestamp(ts_first + shift)
		elif weekday == 6:
			shift += 86400 * 2
			new_date = datetime.datetime.fromtimestamp(ts_first + shift)
		elif weekday == 7:
			shift += 86400
			new_date = datetime.datetime.fromtimestamp(ts_first + shift)

		weekday = new_date.isoweekday()
		new_date = new_date.strftime("%Y-%m-%d %H:%M:%S")
		if debug >= 1:
			test = game["start_date"]
			
			# output minor prizes
			if debug >= 2:
				game_id = game["id"]
				log.info(f"Darts minigame ID: {game_id}")

				idx = 1
				for unit in game["items"]:
					item_id = int(unit)
					item = get_item(config, item_id)
					if item:
						item_name = item["name"]
					else:
						item_name = "INVALID UNIT"

					log.info(f"[DEBUG] Minor Prize {idx} = ({item_id}) {item_name}")
					idx += 1

			# output major prize and date change
			major_prize = int(game["extra_item"])
			item = get_item(config, major_prize)
			item_name = "INVALID MAJOR PRIZE"
			if item:
				item_name = item["name"]

			log.info(f"[DEBUG] {test} -> {new_date} (weekday = {weekday}) -> ({major_prize}) {item_name}")

		game["start_date"] = new_date

		# make sure each one lasts exactly 7 days from first one
		last_ts = ts_first + shift
		shift += week_length

	return last_ts

def get_item(config, item_id):
	id_str = str(item_id)
	for item in config["items"]:
		if item["id"] == id_str:
			return item
	return None