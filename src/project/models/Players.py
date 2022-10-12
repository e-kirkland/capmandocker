from core import Mixin
from utils import get_current_time
from models.base import db
from sqlalchemy_utils import UUIDType
from sqlalchemy import ForeignKey, orm
from sqlalchemy.orm import relationship
import uuid


class Players(db.Model, Mixin):

    __tablename__ = "players"
    __table_args__ = {"extend_existing": True}

    player_id = db.Column(db.String, nullable=False, primary_key=True)
    player = db.Column(db.String)
    position = db.Column(db.String)
    team = db.Column(db.String)
    salary = db.Column(db.String)
    roster_id = db.Column(db.Integer)
    injured_reserve = db.Column(db.Boolean)
    war = db.Column(db.Numeric)
    value = db.Column(db.Numeric)

    @classmethod
    def get_by_player_id(cls, player_id):
        return cls.query.filter_by(player_id=player_id).first()

    @classmethod
    def get_by_roster_id(cls, roster_id):
        return db.session.query(Players).filter(Players.roster_id == roster_id).all()

    @classmethod
    def upsert_player(cls, player):
        db.session.add(player)
        db.session.commit()
        return player

    @classmethod
    def delete_player(cls, player):
        db.session.delete(player)
        db.session.commit()

    @classmethod
    def get_all(cls):
        return Players.query.order_by(Players.roster_id.asc()).all()
