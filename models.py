from sqlalchemy import Integer, String, Float, BigInteger, Text, Boolean
from sqlalchemy.sql.schema import Column
from database import Base

class GraphData(Base):
    __tablename__ = 'graph_data'
    point_id = Column(BigInteger, primary_key=True, autoincrement=True)
    latitude = Column(String(255), nullable=False)
    longitude = Column(String(255), nullable=False)
    point_name = Column(Text, nullable=False)


class Schedule(Base):
    __tablename__ = "schedule"

    ship_name = Column(Text, primary_key=True)
    id_karavan = Column(BigInteger)
    id_provodki = Column(BigInteger)
    ice_class = Column(BigInteger)
    speed = Column(BigInteger)
    start_point = Column(Text)
    end_point = Column(Text)
    start_date = Column(Text)
    karavan_point = Column(Text)
    ledokol = Column(Text)
    finish_time_plan = Column(Text)
    finish_time_actual = Column(Text)

class ProvodkiAlgosReal(Base):
    __tablename__ = "provodki_algos_real"

    name = Column(Text)
    id_provodki = Column(BigInteger, primary_key=True)
    dot1 = Column(Text)
    dot2 = Column(Text)
    speed = Column(Text)
    dot1_time = Column(Text)
    dot2_time = Column(Text)
    travel_hours = Column(BigInteger)
    wait_hours = Column(BigInteger)
    with_data = Column(Text, name="with")

class ProvodkiAlgosIdeal(Base):
    __tablename__ = "provodki_algos_ideal"

    name = Column(Text)
    id_provodki = Column(BigInteger, primary_key=True)
    dot1 = Column(Text)
    dot2 = Column(Text)
    speed = Column(Text)
    dot1_time = Column(Text)
    dot2_time = Column(Text)
    travel_hours = Column(BigInteger)
    wiring = Column(Boolean)

