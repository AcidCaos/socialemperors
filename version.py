import random

from engine import timestamp_now

version_name = "alpha 0.04"
version_code = "0.04a"

_quest_ids = [
    "100000006",
    "100000007",
    "100000008",
    "100000012",
    "100000002",
    "100000021",
    "100000022",
    "100000003",
    "100000027",
    "100000028",
    "100000014",
    "100000013",
    "100000020",
    "100000015",
    "100000023",
    "100000019",
    "100000018",
    "100000011",
    "100000033",
    "100000041",
    "100000042",
    "100000043",
    "100000044",
    "100000045",
    "100000046",
    "100000047",
    "100000090",
    "100000091",
    "100000092"
]

_survival_arenas = [
    "100000035",
    "100000036",
    "100000037"
]

def fix_variable(dictionary, key, expected):
    if key not in dictionary:
        dictionary[key] = expected
    elif dictionary[key] == None:
        dictionary[key] = expected
    elif type(dictionary[key]) != type(expected):
        dictionary[key] = expected

def _fix_quest_ranks(ranks, quests):
    for quest in quests:
        if quest not in ranks:
            ranks[quest] = None

def _fix_survival_maps(maps, arenas):
    for arena in arenas:
        if arena not in maps:
            maps[arena] = { "ts": 0, "tp": 0 }

def migrate_loaded_save(save):
    # Migration always happens now, we check the data type this time and insert any new data if necessary
    # This should make sure the save file isn't "half fixed"

    playerInfo = save["playerInfo"]
    privateState = save["privateState"]
    maps = save["maps"]
    ts_now = timestamp_now()
    darts_seed = abs(int((2**16 - 1) * random.random()))

    # OLD fixes --------------------------------------------------------------------------------------------------------------------------------------------------
    # player avatar
    fix_variable(playerInfo, "pic", "")

    # timestamp fix in maps
    for _map in maps:
        fix_variable(_map, "timestamp", ts_now)

    # darts rng seed if missing
    fix_variable(privateState, "dartsRandomSeed", darts_seed)

    fix_variable(privateState, "arrayAnimals", {})					# fix no animal spawning
    fix_variable(privateState, "strategy", 8)						# fix crash when attacking player
    fix_variable(privateState, "universAttackWin", [])				# pvp current island progress (old game builds)
    fix_variable(privateState, "questTimes", [])					# quests
    fix_variable(privateState, "lastQuestTimes", [])				# 1.1.5 quests

    # survival arena
    fix_variable(privateState, "survivalVidaTimeStamp", [])
    fix_variable(privateState, "survivalVidasExtra", 0)
    fix_variable(privateState, "survivalMaps", {})
    _fix_survival_maps(privateState["survivalMaps"], _survival_arenas)

    # NEW fixes --------------------------------------------------------------------------------------------------------------------------------------------------
    # questsRank fix
    fix_variable(privateState, "questsRank", {})
    _fix_quest_ranks(privateState["questsRank"], _quest_ids)

    # team selection window formations
    fix_variable(privateState, "tournamentFormation", 0)

    # pvp shields
    fix_variable(privateState, "shieldEndTime", 0)
    fix_variable(privateState, "shieldCooldown", 0)
    fix_variable(privateState, "purchasedShields", [])

    # remove version tag as it's useless now
    if "version" in save:
        save.pop("version")

    return True