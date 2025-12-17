import logging

from get_game_config import get_daily_bonus
from engine import timestamp_now, give_resource_type, DAILY_BONUS_REPEATABLE
log = logging.getLogger('__main__')

log.info(f" * Daily login bonus repeatable: {DAILY_BONUS_REPEATABLE}")

def daily_bonus_process(player, ts_now):
	privateState = player["privateState"]

	days_passed = _check_login_ts(privateState["_tsNewDailyBonus"], ts_now)
	#log.info(f"{days_passed} days passed since last daily login")

	if not DAILY_BONUS_REPEATABLE:
		if days_passed > 0:
			days_passed = 1

	if days_passed > 0:
		advance_daily_bonus(privateState, days_passed)
	else:
		#log.info("Daily login bonus already given")
		return

	#log.info("Daily login bonus should be shown soon")
	return

def advance_daily_bonus(privateState, days_passed):
	if days_passed == 1:
		#log.info("Consecutive login!")
		privateState["numDayLogged"] = privateState["lastDayRewarded"] + 1
		privateState["showDailyBonus"] = 1
	if DAILY_BONUS_REPEATABLE:
		if days_passed >= 2 or privateState["numDayLogged"] >= 6:
			privateState["numDayLogged"] = 1
			privateState["lastDayRewarded"] = 0
			privateState["nextDayReward"] = 1
			privateState["showDailyBonus"] = 1
			privateState["_tsNewDailyBonus"] = 0
			#log.info("Reset daily login bonus as the streak was broken or all rewards were claimed")
	elif privateState["numDayLogged"] >= 6:
		privateState["showDailyBonus"] = 0
		#log.info("Turned off daily login bonus as all days were claimed")

def claim_daily_bonus(player, ts_now):
	privateState = player["privateState"]
	if not privateState["showDailyBonus"]:
		#log.info("Daily login bonus already given")
		return True
	if privateState["numDayLogged"] == privateState["lastDayRewarded"]:
		#log.info("Daily login bonus already given")
		return True

	day = privateState["numDayLogged"]
	reward = get_daily_bonus(day)
	if not reward:
		log.info("Invalid daily login bonus day {day}")
		return False

	#log.info(f"Giving reward for daily login bonus day {day}")
	_give_daily_reward(player, ts_now, reward["reward"])
	_advance_next_day(player, ts_now)
	return True

def _check_login_ts(last, now):
	day_last = last // 86400
	day_now = now // 86400

	return day_now - day_last

def _advance_next_day(player, ts_now):
	privateState = player["privateState"]
	privateState["lastDayRewarded"] = privateState["numDayLogged"]
	privateState["nextDayReward"] = privateState["lastDayRewarded"] + 1
	privateState["_tsNewDailyBonus"] = ts_now
	if privateState["nextDayReward"] >= 6:
		privateState["nextDayReward"] = 5
		privateState["showDailyBonus"] = 0

def _give_daily_reward(player, ts_now, reward):
	# no other town_ids are allowed
	town_id = 0
	_map = player["maps"][town_id]

	for res in reward:
		if res != "u": # game calls a command for units
			give_resource_type(player, _map, res, reward[res])

	return True