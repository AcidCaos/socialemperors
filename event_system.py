import logging
import traceback
import json

log = logging.getLogger('__main__')

# grab server settings
from server_config import get_server_config
def event_hellforge(config, event, ts_now):
	from get_game_config import get_event_data, ts_to_date, date_to_ts
	event_id = 1
	event_name = "Hell's Forge Island"
	
	event_data = get_event_data(event_id)
	
	if not event_data:
		log.info(f" * {event_name} could not be enabled -> Event data not found!")
		return
	
	if event["active"]:
		# activate event
		duration = event["days"] * 86400
	
		start_ts = date_to_ts(event["date"])
		start_date = ts_to_date(start_ts)
		end_ts = start_ts + duration
		end_date = ts_to_date(end_ts)
	
		event_data["starts_at"] = start_ts
		event_data["duration"] = duration
		
		log.info(f" * {event_name} is now active! -> {start_date} - {end_date}")
	else:
		# deactivate event
		if event_data["duration"] > 0:
			log.info(f" * {event_name} is no longer active!")
		event_data["starts_at"] = 0
		event_data["duration"] = 0

_events = {
	"HELL_FORGE_ISLAND":				event_hellforge
}

def apply_events(config, ts):
	
	if "events" not in get_server_config():
		return

	log.info(" [+] Applying events...")
	events = get_server_config()["events"]
	for event in events:
		try:
			event_type = event["event"]
			if event_type in _events:
				_events[event_type](config, event, ts)
			else:
				log.info(f" * Unknown event {event_type}")
				
		except:
			traceback.print_exc()
			pass