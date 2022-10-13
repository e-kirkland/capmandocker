from flask import Blueprint, request, jsonify

from models.Players import Players
from core import create_response, serialize_list

players = Blueprint("players", __name__, url_prefix="/players")


def players_upsert_df(df):

    # Post player data to postgres
    df_json = df.to_dict(orient="records")

    # Create Player object and upsert
    for item in df_json:
        try:
            _player = Players(
                player_id=str(item["player_id"]),
                player=str(item["player"]),
                position=str(item["position"]),
                team=str(item["team"]),
                salary=str(item["salary"]),
                roster_id=int(item["roster_id"]),
                injured_reserve=bool(item["injured_reserve"]),
                war=float(item["war"]),
                value=float(item["value"]),
            )
            Players.upsert_player(_player)
        except Exception as e:
            print("ERROR: ", e, flush=True)
            raise e

    return jsonify(msg="Successfully inserted all players")


@players.route("/roster/<roster_id>", methods=["GET"])
def get_players_by_roster_id(roster_id):
    players = Players.get_by_roster_id(roster_id)

    return create_response(status=200, data={"players": serialize_list(players)})


@players.route("/<player_id>", methods=["PUT"])
def update_player_by_player_id(player_id):
    # Get requested data
    data = request.get_json()

    # Check for player_id
    if not player_id:
        return create_response(status=400, message="Must include player_id as a param")

    # Pull player and check if existing
    _players = Players.get_by_player_id(player_id)
    if not _players:
        return create_response(status=400, message="player_id not found")

    # Store new values
    if data.get("player"):
        _players.player = data["player"]
    if data.get("position"):
        _players.position = data["position"]
    if data.get("team"):
        _players.team = data["team"]
    if data.get("salary"):
        _players.salary = data["salary"]
    if data.get("roster_id"):
        _players.roster_id = data["roster_id"]
    if data.get("injured_reserve"):
        _players.injured_reserve = data["injured_reserve"]
    if data.get("war"):
        _players.war = data["war"]
    if data.get("value"):
        _players.value = data["value"]

    # Upsert player
    Players.upsert_player(_players)

    msg = f"Successfully updated player settings for {_players.player}"
    player_dict = _players.to_dict()
    return create_response(status=200, message=msg, data=player_dict)
