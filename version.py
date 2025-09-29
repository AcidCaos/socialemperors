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

def _safe_migrate_save(save):
    privateState = save["privateState"]

    # questsRank fix
    fix_variable(privateState, "questsRank", {})
    _fix_quest_ranks(privateState["questsRank"], _quest_ids)

    # team selection window formations
    fix_variable(privateState, "tournamentFormation", 0)

    # pvp shields
    fix_variable(privateState, "shieldEndTime", 0)
    fix_variable(privateState, "shieldCooldown", 0)
    fix_variable(privateState, "purchasedShields", [])

def migrate_loaded_save(save: dict) -> bool:

    # Let's really make sure this migration happens or the save will never migrate correctly, way better than checking just one value which may be incorrectly set
    # while the rest of the data may remain unmigrated and outdated making the game crash
    _safe_migrate_save(save)

    # discard current version saves
    if save["version"] == version_code:
        return False
    
    # fix 0.01a saves
    if "version" not in save or save["version"] is None:
        save["version"] = "0.01a"
    
    # 0.01a -> 0.02a
    if save["version"] == "0.01a":
        save["maps"][0]["timestamp"] = timestamp_now()
        save["privateState"]["dartsRandomSeed"] = abs(int((2**16 - 1) * random.random()))
        save["version"] = "0.02a"
        print("   > migrated to 0.02a")
    
    # 0.02a -> 0.03a
    if save["version"] == "0.02a":
        if "arrayAnimals" not in save["privateState"]:
            save["privateState"]["arrayAnimals"] = {} # fix no animal spawning
        if "strategy" not in save["privateState"]:
            save["privateState"]["strategy"] = 8 # fix crash when attacking a player
        if "universAttackWin" not in save["maps"][0]:
            save["maps"][0]["universAttackWin"] = [] # pvp current island progress
        if "questTimes" not in save["maps"][0]:
            save["maps"][0]["questTimes"] = [] # quests
        if "lastQuestTimes" not in save["maps"][0]:
            save["maps"][0]["lastQuestTimes"] = [] # 1.1.5 quests
        save["version"] = "0.03a"
        print("   > migrated to 0.03a")
    
    # 0.03a -> 0.04a
    if save["version"] == "0.03a":
        if "pic" not in save["playerInfo"].keys():
            save["playerInfo"]["pic"] = ""
        if("survivalVidaTimeStamp" not in save["privateState"]):
            save["privateState"]["survivalVidaTimeStamp"] = []
        if("survivalVidasExtra" not in save["privateState"]):
            save["privateState"]["survivalVidasExtra"] = 0
        if("survivalMaps" not in save["privateState"]):
            save["privateState"]["survivalMaps"] = {
                "100000035": {
                    "ts": 0,
                    "tp": 0
                },
                "100000036": {
                    "ts": 0,
                    "tp": 0
                },
                "100000037": {
                    "ts": 0,
                    "tp": 0
                }
            }
        save["version"] = "0.04a"
        print("   > migrated to 0.04a")

    # 0.04a -> 0.05a
    #if save["version"] == "0.04a":
    #    save["version"] = "0.05a"
    #    print("   > migrated to 0.05a")

    return True