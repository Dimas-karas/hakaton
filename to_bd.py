import pandas as pd
import psycopg2
from database import *
from models import *
import random

conn = psycopg2.connect(database='rosatom', user='postgres', host='localhost', password='1712')



def to_bd_graph():
    df = pd.read_csv('points.csv', sep=';')
    cur = conn.cursor()

    cur.execute("delete from graph_data;")

    conn.commit()
    cur.close()


    # Вставляем данные из датафрейма в таблицу базы данных
    for index, row in df.iterrows():
        db = SessionLocal()

        new_data = {
            "point_id" : row["point_id"],
            "latitude" : row["latitude"],
            "longitude": row["longitude"],
            "point_name": row["point_name"]
        }

        station_to_add = GraphData(**new_data)
        db.add(station_to_add)
        db.commit()
        db.close()

def to_bd_shedule():
    df = pd.read_excel('Расписание движения судов.xlsx').dropna()
    df1 = pd.read_csv('timesheet_time.csv')
    cur = conn.cursor()

    cur.execute("delete from schedule;")

    conn.commit()
    cur.close()


    # Вставляем данные из датафрейма в таблицу базы данных
    for index, row in df.iterrows():
        db = SessionLocal()
        try:
            time = df1.iloc[0][row["Название судна"]]
        except:
            time = '2022-03-04 14:00:00'

        # Данные для вставки
        data = {
            "ship_name": row["Название судна"],
            "id_karavan": 123,
            "id_provodki": 456,
            "ice_class": row["Ледовый класс"],
            "speed": row["Скорость, узлы\n(по чистой воде)"],
            "start_point": row["Пункт начала плавания"],
            "end_point": row["Пункт окончания плавания"],
            "start_date": row["Дата начала плавания"],
            "karavan_point": "Karavan Point",
            "ledokol": "Таймыр",
            "finish_time_plan": time,
            "finish_time_actual": time,
        }


        to_add = Schedule(**data)
        db.add(to_add)
        db.commit()
        db.close()

def to_bd_algos_real():
    df = pd.read_csv('timesheet_real.csv')
    cur = conn.cursor()

    cur.execute("delete from provodki_algos_real;")

    conn.commit()
    cur.close()

    # Вставляем данные из датафрейма в таблицу базы данных
    for index, row in df.iterrows():
        db = SessionLocal()

        # Данные для вставки
        data = {
            "name": row["name"],
            "id_provodki": 12345,
            "dot1": row["dot1"],
            "dot2": row["dot2"],
            "speed": row["speed"],
            "dot1_time": row["on_dot1_time"],
            "dot2_time": row["dot2_time"],
            "travel_hours": row["travel_hours"],
            "wait_hours": row["wait_hours"],
            "with_data": row["with"]
        }

        to_add = ProvodkiAlgosReal(**data)
        db.add(to_add)
        db.commit()
        db.close()

def to_bd_algos_ideal():
    df = pd.read_csv('ideal_timesheet.csv')
    cur = conn.cursor()

    cur.execute("delete from provodki_algos_ideal;")

    conn.commit()
    cur.close()

    # Вставляем данные из датафрейма в таблицу базы данных
    for index, row in df.iterrows():
        db = SessionLocal()

        # Данные для вставки
        data = {
            "name": row["name"],
            "id_provodki": 12345,
            "dot1": row["dot1"],
            "dot2": row["dot2"],
            "speed": row["speed"],
            "dot1_time": row["dot1_time"],
            "dot2_time": row["dot2_time"],
            "travel_hours": row["travel_hours"],
            "wiring": row["wiring"]
        }

        to_add = ProvodkiAlgosIdeal(**data)
        db.add(to_add)
        db.commit()
        db.close()



