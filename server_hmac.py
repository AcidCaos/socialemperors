import hmac
import hashlib
import json
from typing import Optional, Dict, Any

_SERVER_KEY = "3m0d3pwiupoetn7ysa02"

def string_to_bytes(s): # -> bytes:
	return s.encode("utf-8")

def compute_hmac_sha256(payload: str, key: str = _SERVER_KEY): # -> bytes:
	return hmac.new(
		string_to_bytes(key),
		string_to_bytes(payload),
		hashlib.sha256,
	).digest()

def hash_(payload: str, key: str = _SERVER_KEY): # -> bytes:
	return compute_hmac_sha256(payload, key)

def construct_hash_and_payload(payload, key: str = _SERVER_KEY): # -> str:
	payload = json.dumps(payload)
	return f"{hash_(payload, key).hex()};{payload}"

def get_hash_and_payload(s: str): # -> Dict[str, Any]:
	i_semicolon = s.find(";")
	i_quote = s.find('"')
	i_brace = s.find("{")
	i_bracket = s.find("[")

	if (i_semicolon < 0	or i_quote < i_semicolon or i_brace < i_semicolon or (i_bracket < i_semicolon and i_bracket != -1)):
		return {"hash": None, "payload": s}

	hash_hex = s[:i_semicolon]
	payload = s[i_semicolon + 1 :]

	try:
		hash_bytes = bytes.fromhex(hash_hex)
	except ValueError:
		return {"hash": None, "payload": s}

	return {"hash": hash_bytes, "payload": payload}

def check_hash_and_payload(obj: Dict[str, Any], key: str = _SERVER_KEY): # -> bool:
	given_hash: Optional[bytes] = obj.get("hash")
	if given_hash is None:
		return False

	calc = hash_(obj["payload"], key)

	return hmac.compare_digest(given_hash, calc)