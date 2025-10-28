// PVP Ranking
function showLeaderboard(...param)
{
	if (param[0][0] === "list-pt")
	{
		window.open("/pvp/ranking", '_blank').focus();
	}
}
// Graveyard Ask for Potions
function showPopupSEHelpPotion(...param)
{
	if (param[0].length == 0)
	{
		window.open("/graveyard/potions", '_blank').focus();
	}
}
// ??
function sendFbMessage(...param)
{
	// player_uid
	_ei_debug("sendFbMessage", param);
}
// Share Lost Item
function showFeedItemFound(...param)
{
	// voluntary, tipo, id
	_ei_debug("showFeedItemFound", param);
}
// Events -> Hire Friends
function showPopupSEHelpOffer(...param)
{
	// event_id
	_ei_debug("showPopupSEHelpOffer", param);
}
// SI Building Hiring
function showPopupSEHelpSocialItem(...param)
{
	// bx, by, town_id, bitem_id, hired_si, bitem_name
	_ei_debug("showPopupSEHelpSocialItem", param);

	if (param.length == 6) 
	{
		_open_window_post_request("/friends/hire", param);
	}
}
// ??
function showFeed(...param)
{
	// Land Expansion
	// confirm:
	// true, "expansion", ownedGrid.length - 2, ownerGrid.length, ""
	// deny:
	// false, "expansion", ownedGrid.length - 2, ownerGrid.length, ""
	_ei_debug("showPopupSEHelpNest", param);
	
}
// Dragon Nest Help
function showPopupSEHelpNest(...param)
{
	// all_friends, nest_name
	// use privateState.dragonSocialHelp as SI
	// client sends Constants.CMD_CLEAR_DRAGON_HIRES command with SI data
	_ei_debug("showPopupSEHelpNest", param);
}

function _open_window_post_request(url, ...param) {
	var form = document.createElement("form");
	form.setAttribute("method", "post");
	form.setAttribute("action", url);
	form.setAttribute("target", "_blank");
	form.style.display = "none";
	
	var input = document.createElement("input");
	input.type = "hidden";
	input.name = "data";
	input.value = JSON.stringify(param[0], null, '');
	form.appendChild(input);

	document.body.appendChild(form);
	form.submit();
	document.body.removeChild(form);
}

// Debug
function _ei_debug(func_name, ...param)
{
	console.log("ExternalInterface: " + func_name + " -> " + JSON.stringify(param[0], null, '\t'));
}

console.log("ExternalInterface initialized!");