import random

from engine import timestamp_now

version_name = "alpha 0.02"
version_code = "0.02a"

def migrate_loaded_save(save: dict) -> bool:
    # fix 0.01a saves
    if "version" not in save:
        save["version"] = "0.01a"
    
    if save["version"] == version_code: # save is from the current version
        return False
    
    # 0.01a -> 0.02a
    if save["version"] == "0.01a":
        save["maps"][0]["timestamp"] = timestamp_now()
        save["privateState"]["dartsRandomSeed"] = abs(int((2**16 - 1) * random.random()))
        save["version"] = "0.02a"

        print("   > migrated to 0.02a")
    
    # # 0.02a -> 0.03a
    # if save["version"] == "0.02a":
    #     save["version"] = "0.03a"
    #     save["privateState"]["arrayAnimals"] = {} # fix no animal spawning
    #     save["privateState"]["strategy"] = 8 # fix crash when attacking a player
    #     save["maps"][0]["universAttackWin"] = [] # pvp current island progress
    #     print("   > migrated to 0.03a")

    return True