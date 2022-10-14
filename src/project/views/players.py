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

            # Pull player and check if existing
            _players = Players.get_by_player_id(str(item["player_id"]))
            # If player does not exist, create record and insert
            if not _players:

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

            else:
                _returnPlayer = upsert_player(item["player_id"], item)

        except Exception as e:
            print("ERROR: ", e, flush=True)
            raise e

    return jsonify(msg="Successfully inserted all players")


def upsert_player(player_id, data):

    # Pull player and check if existing
    _players = Players.get_by_player_id(str(player_id))
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

    return _players


@players.route("/roster/<roster_id>", methods=["GET"])
def get_players_by_roster_id(roster_id):
    players = Players.get_by_roster_id(roster_id)

    return create_response(status=200, data={"players": serialize_list(players)})


@players.route("/roster/<roster_id>", methods=["PUT"])
def update_players_by_roster_id(roster_id):
    # Get requested data
    data = request.get_json()

    if not data.get("players"):
        create_response(
            status=400, message="Requires JSON payload with 'players' key/value"
        )

    players_list = data.get("players")
    print("PLAYERS LIST: ", players_list, flush=True)

    for idx, player in enumerate(players_list):
        print(
            f"UPDATING PLAYER {idx+1}/{len(players_list)}: ",
            player["player_id"],
            flush=True,
        )
        player_id = player["player_id"]
        _player = upsert_player(player_id, player)

    return create_response(status=200, message="Successfully updated all players.")


@players.route("/<player_id>", methods=["PUT"])
def update_player_by_player_id(player_id):
    # Get requested data
    data = request.get_json()

    # Check for player_id
    if not player_id:
        return create_response(status=400, message="Must include player_id as a param")

    _players = upsert_player(player_id, data)

    msg = f"Successfully updated player settings for {_players.player}"
    player_dict = _players.to_dict()
    return create_response(status=200, message=msg, data=player_dict)


def drop_player(player_id):

    # Build drop dictionary for player
    data = {
        "roster_id": '999',
        "salary": 0,
        "injured_reserve": False
    }

    # Upsert player
    _player = upsert_player(player_id, data)

    return _player


def add_player(player_id, roster_id, salary=None):

    # Build add dictionary for player

    data = {
        "roster_id": str(roster_id)
    }

    if salary:
        data["salary"] = int(salary)

    # Upsert player
    _player = upsert_player(player_id, data)

    return _player


def trade_player(player_id, roster_id):

    # Build trade dictionary for player
    data = {
        "roster_id": str(roster_id)
    }

    # Upsert player
    _player = upsert_player(player_id, data)

    return _player