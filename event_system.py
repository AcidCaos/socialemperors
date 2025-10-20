import logging
import traceback
import json

log = logging.getLogger('__main__')

# grab server settings
from server_config import get_server_config
def event_basic(mapping, event, ts_now, num_active):
	from get_game_config import get_event_data, get_event_offer, ts_to_date, date_to_ts
	event_id = mapping["event_id"]
	offer_id = mapping["offer_id"]
	event_name = mapping["name"]

	event_data = None
	offer_data = None
	if event_id:
		event_data = get_event_data(event_id)
	if offer_id:
		offer_data = get_event_offer(offer_id)

	if not offer_data:
		log.info(f" * [{event_name}] FAILED to activate event! -> Event data not found!")
		return

	should_be_active = num_active < _MAX_EVENTS
	is_active = event["active"]

	if not should_be_active:
		if is_active:
			log.info(f" * [{event_name}] FAILED to activate event! -> Too many active events!")
		is_active = False

	if is_active:
		# activate event
		duration = event["days"] * 86400
	
		start_ts = date_to_ts(event["date"])
		start_date = ts_to_date(start_ts)
		end_ts = start_ts + duration
		end_date = ts_to_date(end_ts)
	
		offer_data["starts_at"] = start_ts
		offer_data["duration"] = duration

		if event_data:
			event_data["starts_at"] = start_ts
			event_data["duration"] = duration
		
		log.info(f" * [{event_name}] Event active! -> {start_date} - {end_date}")
		return 1
	else:
		# deactivate event
		if offer_data["duration"] > 0:
			log.info(f" * [{event_name}] Event longer active!")
		
		offer_data["starts_at"] = 0
		offer_data["duration"] = 0

		if event_data:
			event_data["starts_at"] = 0
			event_data["duration"] = 0
		return 0

# DO NOT TOUCH THESE
_events = {
	"EASTER_DRAGON": {
		"name":					"Easter Dragon Event",
		"event":				event_basic,
		"event_id":				None,
		"offer_id":				1,
	},
	"HELL_FORGE_ISLAND": {
		"name":					"Hell's Forge Island",
		"event":				event_basic,
		"event_id":				1,
		"offer_id":				2,
	},
	"IVORY_CHALLENGE": {
		"name":					"Ivory Challenge",
		"event":				event_basic,
		"event_id":				None,
		"offer_id":				3,
	},
	"IVORY_CHALLENGE_DUPLICATE": {
		"name":					"Ivory Challenge Duplicate",
		"event":				event_basic,
		"event_id":				None,
		"offer_id":				4,
	},
	"NIGHT_FORGE": {
		"name":					"Night Forge",
		"event":				event_basic,
		"event_id":				None,
		"offer_id":				5,
	},
}
# the game client cannot show more than 3
_MAX_EVENTS = 3

def apply_events(ts):
	if "events" not in get_server_config():
		return

	log.info(" [+] Applying events...")
	events = get_server_config()["events"]
	num_active = 0

	for event in events:
		try:
			event_type = event["event"]
			if event_type in _events:
				num_active += _events[event_type]["event"](_events[event_type], event, ts, num_active)
			else:
				log.info(f" * Unknown event {event_type}")
				
		except:
			traceback.print_exc()
			pass
		