from core import Mixin
from utils import get_current_time
from models.base import db
from sqlalchemy_utils import UUIDType
from sqlalchemy import ForeignKey, orm
from sqlalchemy.orm import relationship
from flask import jsonify
import pandas as pd
import uuid


class Rosters(db.Model, Mixin):

    __tablename__ = "rosters"
    __table_args__ = {"extend_existing": True}

    roster_id = db.Column(db.String, primary_key=True)
    display_name = db.Column(db.String)
    player_ids = db.Column(db.String)
    salary_total = db.Column(db.Integer)
    players_total = db.Column(db.Integer)

    @classmethod
    def get_by_roster_id(cls, roster_id):
        return db.session.query(Rosters).filter(Rosters.roster_id == roster_id).first()

    @classmethod
    def upsert_roster(cls, roster):
        db.session.add(roster)
        db.session.commit()
        return

    @classmethod
    def delete_roster(cls, roster):
        db.session.delete(roster)
        db.session.commit()
        return roster

    @classmethod
    def get_all(cls):
        return Rosters.query.order_by(Rosters.roster_id.asc()).all()

    @classmethod
    def upsert_df(cls, df):
        print("UPSERTING: ", flush=True)
        # Post roster data to postgres
        df.to_sql(name="rosters", con=db.engine, index=False)
        return jsonify(msg=f"Successfully uploaded {len(df)} records")

    @classmethod
    def upsert_batch(cls, batch):
        db.session.add_all(batch)
        db.session.commit()
        return
