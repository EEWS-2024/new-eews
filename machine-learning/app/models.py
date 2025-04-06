from datetime import datetime

from app import db


class StationTime(db.Model):
    __tablename__ = 'station_times'

    id = db.Column(db.Integer, primary_key=True)
    station_code = db.Column(db.String(50), nullable=False)
    time = db.Column(db.DateTime, nullable=False, default=datetime(1970, 1, 1))

    def __repr__(self):
        return f"<StationTime {self.station_code}>"

class StationWave(db.Model):
    __tablename__ = 'station_waves'

    id = db.Column(db.Integer, primary_key=True)
    station_code = db.Column(db.String(50), nullable=False)
    time = db.Column(db.DateTime, nullable=False, default=datetime(1970, 1, 1))
    count = db.Column(db.Integer, nullable=False, default=0)
    type = db.Column(db.String(50), nullable=False)
    is_reset = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<StationPrimaryWave {self.station_code}>"