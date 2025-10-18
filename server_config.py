import json
import logging

log = logging.getLogger('__main__')

__SERVER_CONFIG = {}
def initialize(config_path):
	try:
		global __SERVER_CONFIG
		__SERVER_CONFIG = json.load(open(config_path, 'r', encoding='utf-8'))
		log.info(f" * Server configured successfully")
	except:
		log.info(" * Server configuration file is corrupted\n   the server cannot start!")
		log.info("   the server cannot start!")
		exit(0)

def get_server_config():
	return __SERVER_CONFIG

log.info(" [+] Loading Server configuration")
initialize("server_config.json")