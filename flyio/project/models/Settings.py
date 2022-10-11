from ..core import Mixin
from ..utils import get_current_time
from .base import db
from sqlalchemy_utils import UUIDType
from sqlalchemy import ForeignKey, orm
from sqlalchemy.orm import relationship
import uuid


class Settings(db.Model, Mixin):

    __tablename__ = "settings"
    __table_args__ = {"extend_existing": True}

    id = db.Column(
        UUIDType(binary=False), primary_key=True, default=uuid.uuid4, unique=True
    )
    league_id = db.Column(db.Integer, nullable=False)
    salary_cap = db.Column(db.Integer, nullable=False)
    roster_min = db.Column(db.Integer, nullable=False)
    roster_max = db.Column(db.Integer, nullable=False)
    transaction_id = db.Column(db.String)

    @classmethod
    def get_by_id(cls, id):
        return cls.query.filter_by(id=id).first()

    @classmethod
    def get_by_league_id(cls, league_id):
        return (
            db.session.query(Settings).filter(Settings.league_id == league_id).first()
        )

    @classmethod
    def upsert_settings(cls, settings):
        db.session.add(settings)
        db.session.commit()
        return settings

    @classmethod
    def delete_settings(cls, settings):
        db.session.delete(settings)
        db.session.commit()
        return settings

    @classmethod
    def get_all(cls):
        return Settings.query.order_by(Settings.league_id.asc()).all()
