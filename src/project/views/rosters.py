from flask import Blueprint, request, jsonify
from sqlalchemy import create_engine

from models.Rosters import Rosters

rosters = Blueprint("rosters", __name__, url_prefix="/rosters")


def records_upsert_df(df):

    # Post team data to postgres
    df_json = df.to_dict(orient="records")

    # Create Roster object and upsert
    for idx, item in enumerate(df_json):
        try:
            _roster = Rosters(
                roster_id=str(item["roster_id"]),
                display_name=str(item["display_name"]),
                player_ids=str(item["player_ids"]),
                salary_total=int(item["salary_total"]),
                players_total=int(item["players_total"]),
            )
            Rosters.upsert_roster(_roster)
        except Exception as e:
            print("ERROR: ", e, flush=True)
            raise e

    return jsonify(msg="Successfully inserted all rosters")
