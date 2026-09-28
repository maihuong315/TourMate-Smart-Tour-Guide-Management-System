import streamlit as st
import pymysql
import pandas as pd

from pymysql.cursors import DictCursor
from datetime import datetime, date


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="TourMate - Smart Tour Guide",
    page_icon="🧭",
    layout="wide"
)


# ============================================================
# MYSQL CONFIG
# ============================================================

MYSQL_CONFIG = {
    "host": "mysql-19728385-npmaihuong-927f.b.aivencloud.com",
    "port": 27942,
    "user": "avnadmin",

    # DÁN PASSWORD AIVEN CỦA EM VÀO ĐÂY
    "password": "AVNS_zBDlzsF9I5fC-EdWcl0",

    "database": "defaultdb",
    "charset": "utf8mb4",
    "cursorclass": DictCursor,
    "autocommit": True,

    "connect_timeout": 20,
    "read_timeout": 30,
    "write_timeout": 30,
}


# ============================================================
# TEST MYSQL NGAY KHI APP CHẠY
# ============================================================

def test_mysql():

    conn = None

    try:

        conn = pymysql.connect(
            **MYSQL_CONFIG
        )

        with conn.cursor() as cursor:

            cursor.execute(
                "SELECT 1 AS connection_ok"
            )

            result = cursor.fetchone()

            cursor.execute(
                "SELECT DATABASE() AS db_name"
            )

            database = cursor.fetchone()

        return True, result, database

    except pymysql.MySQLError as e:

        code = e.args[0] if e.args else "UNKNOWN"

        message = (
            e.args[1]
            if len(e.args) > 1
            else str(e)
        )

        return (
            False,
            None,
            f"MySQL Error {code}: {message}"
        )

    except Exception as e:

        return (
            False,
            None,
            str(e)
        )

    finally:

        if conn:

            conn.close()


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_conn():

    try:

        return pymysql.connect(
            **MYSQL_CONFIG
        )

    except pymysql.MySQLError as e:

        code = e.args[0] if e.args else "UNKNOWN"

        message = (
            e.args[1]
            if len(e.args) > 1
            else str(e)
        )

        raise RuntimeError(
            f"MySQL Error {code}: {message}"
        )


# ============================================================
# EXECUTE
# ============================================================

def execute(sql, params=()):

    conn = None

    try:

        conn = get_conn()

        with conn.cursor() as cursor:

            cursor.execute(
                sql,
                params
            )

            return cursor.lastrowid

    except pymysql.MySQLError as e:

        code = e.args[0] if e.args else "UNKNOWN"

        message = (
            e.args[1]
            if len(e.args) > 1
            else str(e)
        )

        raise RuntimeError(
            f"MySQL Error {code}: {message}"
        )

    finally:

        if conn:

            conn.close()


# ============================================================
# QUERY
# ============================================================

def query(sql, params=()):

    conn = None

    try:

        conn = get_conn()

        with conn.cursor() as cursor:

            cursor.execute(
                sql,
                params
            )

            return cursor.fetchall()

    except pymysql.MySQLError as e:

        code = e.args[0] if e.args else "UNKNOWN"

        message = (
            e.args[1]
            if len(e.args) > 1
            else str(e)
        )

        raise RuntimeError(
            f"MySQL Error {code}: {message}"
        )

    finally:

        if conn:

            conn.close()


# ============================================================
# QUERY ONE
# ============================================================

def query_one(sql, params=()):

    rows = query(
        sql,
        params
    )

    if rows:

        return rows[0]

    return None


# ============================================================
# QUERY DATAFRAME
# ============================================================

def query_df(sql, params=()):

    rows = query(
        sql,
        params
    )

    if not rows:

        return pd.DataFrame()

    return pd.DataFrame(rows)


# ============================================================
# STARTUP TEST
# ============================================================

mysql_ok, mysql_result, mysql_database = test_mysql()


if not mysql_ok:

    st.title("🧭 TourMate")

    st.error(
        "❌ Không thể kết nối Aiven MySQL"
    )

    st.code(
        str(mysql_database)
    )

    st.warning(
        """
        Kiểm tra lại:

        • Host
        • Port
        • User
        • Password
        • Database

        Host:
        mysql-19728385-npmaihuong-927f.b.aivencloud.com

        Port:
        27942

        Database:
        defaultdb

        User:
        avnadmin
        """
    )

    st.stop()


# ============================================================
# CONNECTION SUCCESS
# ============================================================

st.sidebar.success(
    "🟢 MySQL Connected"
)
