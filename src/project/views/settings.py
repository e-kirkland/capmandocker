from flask import Blueprint, request, jsonify

from models.Settings import Settings
from core import create_response, serialize_list

settings = Blueprint("settings", __name__, url_prefix="/settings")


def settings_upsert(settings_dict):

    try:

        # Create Roster object and upsert
        _settings = Settings(
            league_id=str(settings_dict["league_id"]),
            salary_cap=int(settings_dict["salary_cap"]),
            roster_min=int(settings_dict["roster_min"]),
            roster_max=int(settings_dict["roster_max"]),
            transaction_id=str(settings_dict["transaction_id"]),
        )
        Settings.upsert_settings(_settings)

    except Exception as e:
        print("ERROR: ", e, flush=True)
        raise e

    return jsonify(msg="Successfully inserted settings")


@settings.route("/<league_id>", methods=["GET"])
def get_settings_by_league_id(league_id):
    settings = Settings.get_by_league_id(league_id)

    return create_response(data={"settings": settings.to_dict()})


@settings.route("/<league_id>", methods=["PUT"])
def update_settings_by_league_id(league_id):
    # Get requested data
    data = request.get_json()

    # Check for league_id
    if not league_id:
        return create_response(status=400, message="Must include league_id as a param")

    # Pull setting and check if existing
    _settings = Settings.get_by_league_id(league_id)
    if not _settings:
        return create_response(
            status=400, message="league_id not found in settings table"
        )

    # Store new values
    if data.get("salary_cap") is not None:
        _settings.salary_cap = data["salary_cap"]
    if data.get("roster_min") is not None:
        _settings.roster_min = data["roster_min"]
    if data.get("roster_max") is not None:
        _settings.roster_max = data["roster_max"]
    if data.get("transaction_id") is not None:
        _settings.transaction_id = data["transaction_id"]

    # Upsert settings
    Settings.upsert_settings(_settings)

    msg = f"Successfully updated settings with league_id: {_settings.league_id}"
    settings_dict = _settings.to_dict()
    return create_response(status=200, message=msg, data=settings_dict)

def update_settings_internal(league_id, data):

    # Pull setting and check if existing
    _settings = Settings.get_by_league_id(league_id)
    if not _settings:
        return f"NO SETTINGS FOUND FOR LEAGUE ID: {league_id}"

    # Store new values
    if data.get("salary_cap") is not None:
        _settings.salary_cap = data["salary_cap"]
    if data.get("roster_min") is not None:
        _settings.roster_min = data["roster_min"]
    if data.get("roster_max") is not None:
        _settings.roster_max = data["roster_max"]
    if data.get("transaction_id") is not None:
        _settings.transaction_id = data["transaction_id"]

    # Upsert settings
    Settings.upsert_settings(_settings)

    msg = f"Successfully updated settings with league_id: {_settings.league_id}"
    
    return msg