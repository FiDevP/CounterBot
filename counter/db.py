# -*- coding: utf-8 -*-

import sqlite3


def ensure_connection(func):
    """ Декоратор для подключения к СУБД: открывает соединение,
        выполняет переданную функцию и закрывает за собой соединение.
        Потокобезопасно!
    """
    def inner(*args, **kwargs):
        with sqlite3.connect('server.db') as conn:
            kwargs['conn'] = conn
            res = func(*args, **kwargs)
        return res

    return inner


@ensure_connection
def init_db(conn, force: bool = False):
    sql = conn.cursor()

    if force:
        sql.execute('DROP TABLE IF EXISTS data_counter')

    sql.execute("""CREATE TABLE IF NOT EXISTS data_counter (
        id                 INTEGER PRIMARY KEY,
        user_id            INTEGER NOT NULL,
        water_cold         FLOAT NOT NULL,
        water_hot          FLOAT NOT NULL,
        el_day             FLOAT NOT NULL,
        el_night           FLOAT NOT NULL
     )
    """)
    conn.commit()


@ensure_connection
def add_to_db(
        conn,
        user_id,
        water_cold,
        water_hot,
        el_day,
        el_night
        ):
    sql = conn.cursor()
    sql.execute("INSERT INTO data_counter (user_id, water_cold, water_hot, el_day, el_night) VALUES ( ?, ?, ?, ?, ?)", (
                            user_id,
                            water_cold,
                            water_hot,
                            el_day,
                            el_night
    ))
    conn.commit()


@ensure_connection
def calculate_indicators(conn):
    sql = conn.cursor()
    sql.execute('SELECT COUNT(*) FROM data_counter')
    (q,) = sql.fetchone()

    sql.execute('SELECT water_cold, water_hot, el_day, el_night FROM data_counter WHERE id = ?', (q,))
    list1 = sql.fetchall()
    wa_co1 = list1[0][0]
    wa_ho1 = list1[0][1]
    el_da1 = list1[0][2]
    el_ni1 = list1[0][3]

    sql.execute('SELECT water_cold, water_hot, el_day, el_night FROM data_counter WHERE id = ?', (q-1,))
    list1 = sql.fetchall()
    wa_co2 = list1[0][0]
    wa_ho2 = list1[0][1]
    el_da2 = list1[0][2]
    el_ni2 = list1[0][3]

    wa_co = wa_co1 - wa_co2
    wa_ho = wa_ho1 - wa_ho2
    el_da = el_da1 - el_da2
    el_ni = el_ni1 - el_ni2
    wat = wa_co + wa_ho  # водоотведение

    result = (wa_co * 37.49) + (wa_ho * 37.49) + (wat * 35.06) + (el_da * 4.47) + (el_ni * 1.68)
    return result
