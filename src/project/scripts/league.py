from flask import jsonify
from models.base import db
from views.settings import settings_upsert
from .sleeper import get_league


def init_db():
    print("CREATING TABLES", flush=True)
    db.drop_all()
    db.create_all()
    db.session.commit()
    return db


def update_settings(leagueID, salaryCap, rosterMin, rosterMax, transaction_id):
    settings_dict = {
        "league_id": leagueID,
        "salary_cap": salaryCap,
        "roster_min": rosterMin,
        "roster_max": rosterMax,
        "transaction_id": transaction_id,
    }

    msg = settings_upsert(settings_dict)

    return msg


def populate_tables(leagueID, salaryCap, rosterMin, rosterMax):
    print("POPULATING TABLES", flush=True)
    transaction_id = get_league(leagueID)

    print("UPDATING SETTINGS", flush=True)
    msg = update_settings(leagueID, salaryCap, rosterMin, rosterMax, transaction_id)

    return jsonify(msg="All tables populated successfully")


def init_league(leagueID, salaryCap, rosterMin, rosterMax):

    # Set up postgres tables
    init_db()

    # Populate tables with league info
    msg = populate_tables(leagueID, salaryCap, rosterMin, rosterMax)

    return jsonify(msg="League initialized successfully")
