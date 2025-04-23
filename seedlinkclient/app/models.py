from datetime import datetime

from sqlalchemy import PrimaryKeyConstraint, Sequence

from app import db


class Seismic(db.Model):
    __tablename__ = 'seismic'

    id = db.Column(
        db.BigInteger,
        Sequence('seismic_id_seq'),  # explicit sequence for composite PK
        primary_key=True,
        autoincrement=True
    )
    start_time = db.Column(
        db.DateTime(timezone=True),
        primary_key=True,
        nullable=False,
        default=datetime(1970, 1, 1)
    )
    station_code = db.Column(db.String(50), nullable=False)
    network = db.Column(db.String(50), nullable=False)
    channel = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(50), nullable=True)
    end_time = db.Column(db.DateTime(timezone=True),
                         nullable=False,
                         default=datetime(1970, 1, 1))
    delta = db.Column(db.Float, nullable=False)
    sample_rate = db.Column(db.Float, nullable=False)
    calib = db.Column(db.Float, nullable=False)
    data = db.Column(db.ARRAY(db.Integer), nullable=False)
    arrival_time = db.Column(db.DateTime(timezone=True),
                             nullable=False,
                             default=datetime(1970, 1, 1))
    length = db.Column(db.Integer, nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('id', 'start_time'),
    )

    def __repr__(self):
        return f"<Seismic {self.station_code}>"

