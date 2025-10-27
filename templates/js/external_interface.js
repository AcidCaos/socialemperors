// PVP Ranking
function showLeaderboard(param)
{
	if (param[0] === "list-pt")
	{
		window.open("/pvp/ranking", '_blank').focus();
	}
}
// Graveyard Ask for Potions
function showPopupSEHelpPotion(param)
{
	if (param.length == 0)
	{
		window.open("/graveyard/potions", '_blank').focus();
	}
}