import streamlit as st
import pymysql
import pandas as pd

from pymysql.cursors import DictCursor
from datetime import date, datetime, time, timedelta


# ============================================================
# 1. PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="TourMate",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# 2. CSS
# ============================================================

st.markdown(
    """
    <style>

    .main {
        background: #f5f7fb;
    }

    .block-container {
        max-width: 1500px;
        padding-top: 1.2rem;
        padding-bottom: 3rem;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a, #172554);
    }

    [data-testid="stSidebar"] * {
        color: white !important;
    }

    .hero {
        background: linear-gradient(135deg, #0f766e, #2563eb);
        color: white;
        padding: 30px;
        border-radius: 22px;
        margin-bottom: 25px;
        box-shadow: 0 10px 30px rgba(0,0,0,.12);
    }

    .hero h1 {
        margin: 0;
        font-size: 38px;
    }

    .hero p {
        margin-top: 8px;
        opacity: .9;
        font-size: 16px;
    }

    .card {
        background: white;
        padding: 20px;
        border-radius: 16px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 5px 15px rgba(0,0,0,.04);
    }

    .section-title {
        font-size: 25px;
        font-weight: 700;
        margin-top: 20px;
        margin-bottom: 15px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 3. AIVEN MYSQL
# ============================================================

MYSQL_CONFIG = {
    "host": "mysql-19728385-npmaihuong-927f.b.aivencloud.com",
    "port": 27942,
    "user": "avnadmin",

    # ========================================================
    # DÁN MẬT KHẨU AIVEN CỦA EM VÀO ĐÂY
    # ========================================================

    "password": "AVNS_zBDlzsF9I5fC-EdWcl0",

    "database": "defaultdb",
    "charset": "utf8mb4",
    "cursorclass": DictCursor,
    "autocommit": True,
    "connect_timeout": 15,
    "read_timeout": 30,
    "write_timeout": 30,
}


# ============================================================
# 4. DATABASE FUNCTIONS
# ============================================================

def get_conn():

    if (
        not MYSQL_CONFIG["password"]
        or MYSQL_CONFIG["password"] == "YOUR_AIVEN_PASSWORD"
    ):
        raise RuntimeError(
            "Chưa nhập mật khẩu Aiven trong MYSQL_CONFIG."
        )

    return pymysql.connect(**MYSQL_CONFIG)


def execute(sql, params=()):

    conn = None

    try:

        conn = get_conn()

        with conn.cursor() as cursor:
            cursor.execute(sql, params)

        conn.commit()

    except pymysql.MySQLError as e:

        code = e.args[0] if e.args else "UNKNOWN"
        message = e.args[1] if len(e.args) > 1 else str(e)

        raise RuntimeError(
            f"MySQL Error {code}: {message}"
        )

    finally:

        if conn:
            conn.close()


def query(sql, params=()):

    conn = None

    try:

        conn = get_conn()

        with conn.cursor() as cursor:

            cursor.execute(sql, params)

            return cursor.fetchall()

    except pymysql.MySQLError as e:

        code = e.args[0] if e.args else "UNKNOWN"
        message = e.args[1] if len(e.args) > 1 else str(e)

        raise RuntimeError(
            f"MySQL Error {code}: {message}"
        )

    finally:

        if conn:
            conn.close()


def query_one(sql, params=()):

    rows = query(sql, params)

    if rows:
        return rows[0]

    return None


def query_df(sql, params=()):

    rows = query(sql, params)

    return pd.DataFrame(rows)


# ============================================================
# 5. DATABASE INFORMATION
# ============================================================

def table_exists(table_name):

    result = query_one(
        """
        SELECT COUNT(*) AS total
        FROM information_schema.tables
        WHERE table_schema = DATABASE()
          AND table_name = %s
        """,
        (table_name,),
    )

    return result["total"] > 0


def get_columns(table_name):

    rows = query(
        """
        SELECT
            COLUMN_NAME,
            IS_NULLABLE,
            COLUMN_DEFAULT,
            DATA_TYPE,
            COLUMN_TYPE
        FROM information_schema.columns
        WHERE table_schema = DATABASE()
          AND table_name = %s
        ORDER BY ORDINAL_POSITION
        """,
        (table_name,),
    )

    return rows


def column_names(table_name):

    return [
        row["COLUMN_NAME"]
        for row in get_columns(table_name)
    ]


# ============================================================
# 6. DATABASE CONNECTION TEST
# ============================================================

def database_test():

    conn = None

    try:

        conn = get_conn()

        with conn.cursor() as cursor:

            cursor.execute(
                "SELECT VERSION() AS version"
            )

            version = cursor.fetchone()

            cursor.execute(
                "SELECT DATABASE() AS db"
            )

            db = cursor.fetchone()

            cursor.execute(
                "SELECT CURRENT_USER() AS db_user"
            )

            user = cursor.fetchone()

        return {
            "version": version["version"],
            "database": db["db"],
            "user": user["db_user"],
        }

    finally:

        if conn:
            conn.close()


# ============================================================
# 7. SAFE ADD COLUMN
# ============================================================

def add_column_if_missing(
    table_name,
    column_name,
    definition
):

    cols = column_names(table_name)

    if column_name in cols:
        return

    try:

        execute(
            f"""
            ALTER TABLE `{table_name}`
            ADD COLUMN `{column_name}` {definition}
            """
        )

    except RuntimeError as e:

        # Nếu một instance khác vừa tạo column
        if "1060" in str(e):
            return

        raise


# ============================================================
# 8. CREATE TABLES
# ============================================================

def create_base_tables():

    execute(
        """
        CREATE TABLE IF NOT EXISTS guides (

            id INT AUTO_INCREMENT PRIMARY KEY,

            name VARCHAR(150) NOT NULL,

            phone VARCHAR(30),

            email VARCHAR(150),

            language VARCHAR(150),

            experience_years INT DEFAULT 0,

            status VARCHAR(30) DEFAULT 'Active',

            created_at TIMESTAMP
            DEFAULT CURRENT_TIMESTAMP

        )
        """
    )


    execute(
        """
        CREATE TABLE IF NOT EXISTS tours (

            id INT AUTO_INCREMENT PRIMARY KEY,

            code VARCHAR(50) UNIQUE NOT NULL,

            name VARCHAR(255) NOT NULL,

            guide_id INT,

            start_date DATE NOT NULL,

            end_date DATE NOT NULL,

            start_time TIME,

            pickup_location VARCHAR(255),

            hotel VARCHAR(255),

            vehicle VARCHAR(255),

            driver VARCHAR(150),

            total_guests INT DEFAULT 0,

            status VARCHAR(30)
            DEFAULT 'Scheduled',

            notes TEXT,

            created_at TIMESTAMP
            DEFAULT CURRENT_TIMESTAMP

        )
        """
    )


    execute(
        """
        CREATE TABLE IF NOT EXISTS itinerary (

            id INT AUTO_INCREMENT PRIMARY KEY,

            tour_id INT NOT NULL,

            tour_date DATE NOT NULL,

            time TIME,

            place VARCHAR(255) NOT NULL,

            activity TEXT,

            transport VARCHAR(100),

            notes TEXT,

            created_at TIMESTAMP
            DEFAULT CURRENT_TIMESTAMP

        )
        """
    )


    execute(
        """
        CREATE TABLE IF NOT EXISTS guests (

            id INT AUTO_INCREMENT PRIMARY KEY,

            tour_id INT NOT NULL,

            full_name VARCHAR(150) NOT NULL,

            gender VARCHAR(30),

            age INT,

            nationality VARCHAR(100),

            phone VARCHAR(50),

            room_number VARCHAR(50),

            special_request TEXT,

            attendance VARCHAR(30)
            DEFAULT 'Present',

            notes TEXT,

            created_at TIMESTAMP
            DEFAULT CURRENT_TIMESTAMP

        )
        """
    )


    execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (

            id INT AUTO_INCREMENT PRIMARY KEY,

            tour_id INT,

            task_name VARCHAR(255) NOT NULL,

            task_type VARCHAR(100),

            due_date DATE,

            due_time TIME,

            assigned_to VARCHAR(150),

            done BOOLEAN DEFAULT FALSE,

            notes TEXT,

            created_at TIMESTAMP
            DEFAULT CURRENT_TIMESTAMP

        )
        """
    )


    execute(
        """
        CREATE TABLE IF NOT EXISTS places (

            id INT AUTO_INCREMENT PRIMARY KEY,

            name VARCHAR(255) NOT NULL,

            location VARCHAR(255),

            category VARCHAR(100),

            introduction TEXT,

            history TEXT,

            highlights TEXT,

            tips TEXT,

            image_url TEXT,

            created_at TIMESTAMP
            DEFAULT CURRENT_TIMESTAMP

        )
        """
    )


    execute(
        """
        CREATE TABLE IF NOT EXISTS incidents (

            id INT AUTO_INCREMENT PRIMARY KEY,

            tour_id INT,

            incident_date DATE,

            incident_time TIME,

            type VARCHAR(100),

            title VARCHAR(255) NOT NULL,

            description TEXT,

            solution TEXT,

            status VARCHAR(30)
            DEFAULT 'Open',

            created_by VARCHAR(150),

            created_at TIMESTAMP
            DEFAULT CURRENT_TIMESTAMP

        )
        """
    )


# ============================================================
# 9. FIX DATABASE CŨ
# ============================================================

def repair_old_database():

    # ========================================================
    # FIX TOURS
    # ========================================================

    if table_exists("tours"):

        cols = column_names("tours")

        # ----------------------------------------------------
        # TRƯỜNG HỢP DATABASE CŨ CÓ tour_name
        # ----------------------------------------------------

        if "tour_name" in cols and "name" not in cols:

            try:

                execute(
                    """
                    ALTER TABLE tours
                    CHANGE COLUMN tour_name
                    name VARCHAR(255) NOT NULL
                    """
                )

            except RuntimeError:

                # Nếu rename không được,
                # tạo name mới và copy dữ liệu
                add_column_if_missing(
                    "tours",
                    "name",
                    "VARCHAR(255)"
                )

                execute(
                    """
                    UPDATE tours
                    SET name = tour_name
                    WHERE name IS NULL
                    """
                )

        elif "tour_name" in cols and "name" in cols:

            # Có cả hai cột.
            # Đồng bộ name từ tour_name nếu name trống.

            try:

                execute(
                    """
                    UPDATE tours
                    SET name = tour_name
                    WHERE
                        (name IS NULL OR name = '')
                        AND tour_name IS NOT NULL
                    """
                )

            except Exception:
                pass


        # ----------------------------------------------------
        # ĐẢM BẢO CÁC CỘT MỚI
        # ----------------------------------------------------

        add_column_if_missing(
            "tours",
            "name",
            "VARCHAR(255)"
        )

        add_column_if_missing(
            "tours",
            "guide_id",
            "INT"
        )

        add_column_if_missing(
            "tours",
            "start_date",
            "DATE"
        )

        add_column_if_missing(
            "tours",
            "end_date",
            "DATE"
        )

        add_column_if_missing(
            "tours",
            "start_time",
            "TIME"
        )

        add_column_if_missing(
            "tours",
            "pickup_location",
            "VARCHAR(255)"
        )

        add_column_if_missing(
            "tours",
            "hotel",
            "VARCHAR(255)"
        )

        add_column_if_missing(
            "tours",
            "vehicle",
            "VARCHAR(255)"
        )

        add_column_if_missing(
            "tours",
            "driver",
            "VARCHAR(150)"
        )

        add_column_if_missing(
            "tours",
            "total_guests",
            "INT DEFAULT 0"
        )

        add_column_if_missing(
            "tours",
            "status",
            "VARCHAR(30) DEFAULT 'Scheduled'"
        )

        add_column_if_missing(
            "tours",
            "notes",
            "TEXT"
        )

        add_column_if_missing(
            "tours",
            "created_at",
            "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        )


    # ========================================================
    # GUIDES
    # ========================================================

    if table_exists("guides"):

        add_column_if_missing(
            "guides",
            "phone",
            "VARCHAR(30)"
        )

        add_column_if_missing(
            "guides",
            "email",
            "VARCHAR(150)"
        )

        add_column_if_missing(
            "guides",
            "language",
            "VARCHAR(150)"
        )

        add_column_if_missing(
            "guides",
            "experience_years",
            "INT DEFAULT 0"
        )

        add_column_if_missing(
            "guides",
            "status",
            "VARCHAR(30) DEFAULT 'Active'"
        )


    # ========================================================
    # ITINERARY
    # ========================================================

    if table_exists("itinerary"):

        add_column_if_missing(
            "itinerary",
            "tour_id",
            "INT"
        )

        add_column_if_missing(
            "itinerary",
            "tour_date",
            "DATE"
        )

        add_column_if_missing(
            "itinerary",
            "time",
            "TIME"
        )

        add_column_if_missing(
            "itinerary",
            "place",
            "VARCHAR(255)"
        )

        add_column_if_missing(
            "itinerary",
            "activity",
            "TEXT"
        )

        add_column_if_missing(
            "itinerary",
            "transport",
            "VARCHAR(100)"
        )

        add_column_if_missing(
            "itinerary",
            "notes",
            "TEXT"
        )


    # ========================================================
    # GUESTS
    # ========================================================

    if table_exists("guests"):

        add_column_if_missing(
            "guests",
            "tour_id",
            "INT"
        )

        add_column_if_missing(
            "guests",
            "full_name",
            "VARCHAR(150)"
        )

        add_column_if_missing(
            "guests",
            "gender",
            "VARCHAR(30)"
        )

        add_column_if_missing(
            "guests",
            "age",
            "INT"
        )

        add_column_if_missing(
            "guests",
            "nationality",
            "VARCHAR(100)"
        )

        add_column_if_missing(
            "guests",
            "phone",
            "VARCHAR(50)"
        )

        add_column_if_missing(
            "guests",
            "room_number",
            "VARCHAR(50)"
        )

        add_column_if_missing(
            "guests",
            "special_request",
            "TEXT"
        )

        add_column_if_missing(
            "guests",
            "attendance",
            "VARCHAR(30) DEFAULT 'Present'"
        )

        add_column_if_missing(
            "guests",
            "notes",
            "TEXT"
        )


    # ========================================================
    # TASKS
    # ========================================================

    if table_exists("tasks"):

        add_column_if_missing(
            "tasks",
            "tour_id",
            "INT"
        )

        add_column_if_missing(
            "tasks",
            "task_name",
            "VARCHAR(255)"
        )

        add_column_if_missing(
            "tasks",
            "task_type",
            "VARCHAR(100)"
        )

        add_column_if_missing(
            "tasks",
            "due_date",
            "DATE"
        )

        add_column_if_missing(
            "tasks",
            "due_time",
            "TIME"
        )

        add_column_if_missing(
            "tasks",
            "assigned_to",
            "VARCHAR(150)"
        )

        add_column_if_missing(
            "tasks",
            "done",
            "BOOLEAN DEFAULT FALSE"
        )

        add_column_if_missing(
            "tasks",
            "notes",
            "TEXT"
        )


    # ========================================================
    # PLACES
    # ========================================================

    if table_exists("places"):

        add_column_if_missing(
            "places",
            "location",
            "VARCHAR(255)"
        )

        add_column_if_missing(
            "places",
            "category",
            "VARCHAR(100)"
        )

        add_column_if_missing(
            "places",
            "introduction",
            "TEXT"
        )

        add_column_if_missing(
            "places",
            "history",
            "TEXT"
        )

        add_column_if_missing(
            "places",
            "highlights",
            "TEXT"
        )

        add_column_if_missing(
            "places",
            "tips",
            "TEXT"
        )

        add_column_if_missing(
            "places",
            "image_url",
            "TEXT"
        )


    # ========================================================
    # INCIDENTS
    # ========================================================

    if table_exists("incidents"):

        add_column_if_missing(
            "incidents",
            "tour_id",
            "INT"
        )

        add_column_if_missing(
            "incidents",
            "incident_date",
            "DATE"
        )

        add_column_if_missing(
            "incidents",
            "incident_time",
            "TIME"
        )

        add_column_if_missing(
            "incidents",
            "type",
            "VARCHAR(100)"
        )

        add_column_if_missing(
            "incidents",
            "title",
            "VARCHAR(255)"
        )

        add_column_if_missing(
            "incidents",
            "description",
            "TEXT"
        )

        add_column_if_missing(
            "incidents",
            "solution",
            "TEXT"
        )

        add_column_if_missing(
            "incidents",
            "status",
            "VARCHAR(30) DEFAULT 'Open'"
        )

        add_column_if_missing(
            "incidents",
            "created_by",
            "VARCHAR(150)"
        )


# ============================================================
# 10. DEMO DATA
# ============================================================

def seed_demo_data():

    # ========================================================
    # GUIDE
    # ========================================================

    guide = query_one(
        """
        SELECT id
        FROM guides
        WHERE email = %s
        LIMIT 1
        """,
        ("demo@tourmate.vn",),
    )

    if not guide:

        execute(
            """
            INSERT INTO guides
            (
                name,
                phone,
                email,
                language,
                experience_years,
                status
            )
            VALUES
            (%s,%s,%s,%s,%s,%s)
            """,
            (
                "Nguyễn Minh Anh",
                "0901234567",
                "demo@tourmate.vn",
                "Vietnamese, English",
                4,
                "Active",
            ),
        )

        guide = query_one(
            """
            SELECT id
            FROM guides
            WHERE email = %s
            LIMIT 1
            """,
            ("demo@tourmate.vn",),
        )

    guide_id = guide["id"]


    # ========================================================
    # TOUR 1
    # ========================================================

    tour = query_one(
        """
        SELECT id
        FROM tours
        WHERE code = %s
        LIMIT 1
        """,
        ("TM-VT-001",),
    )

    if not tour:

        start = date.today()
        end = date.today() + timedelta(days=2)

        execute(
            """
            INSERT INTO tours
            (
                code,
                name,
                guide_id,
                start_date,
                end_date,
                start_time,
                pickup_location,
                hotel,
                vehicle,
                driver,
                total_guests,
                status,
                notes
            )
            VALUES
            (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                "TM-VT-001",
                "Vũng Tàu Discovery 3N2Đ",
                guide_id,
                start,
                end,
                time(7, 30),
                "Khách sạn Imperial Vũng Tàu",
                "The Imperial Hotel",
                "29-seat Tourist Bus",
                "Lê Văn Nam",
                20,
                "Scheduled",
                "Tour demo Vũng Tàu.",
            ),
        )

        tour = query_one(
            """
            SELECT id
            FROM tours
            WHERE code = %s
            LIMIT 1
            """,
            ("TM-VT-001",),
        )

    tour_id = tour["id"]


    # ========================================================
    # TOUR 2
    # ========================================================

    tour2 = query_one(
        """
        SELECT id
        FROM tours
        WHERE code = %s
        LIMIT 1
        """,
        ("TM-DL-002",),
    )

    if not tour2:

        start2 = date.today() + timedelta(days=4)
        end2 = date.today() + timedelta(days=6)

        execute(
            """
            INSERT INTO tours
            (
                code,
                name,
                guide_id,
                start_date,
                end_date,
                start_time,
                pickup_location,
                hotel,
                vehicle,
                driver,
                total_guests,
                status,
                notes
            )
            VALUES
            (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                "TM-DL-002",
                "Đà Lạt City Escape",
                guide_id,
                start2,
                end2,
                time(6, 30),
                "Bến xe Vũng Tàu",
                "Terracotta Hotel",
                "45-seat Tourist Bus",
                "Phạm Văn Bình",
                32,
                "Scheduled",
                "Tour demo Đà Lạt.",
            ),
        )


    # ========================================================
    # ITINERARY
    # ========================================================

    count = query_one(
        """
        SELECT COUNT(*) AS total
        FROM itinerary
        WHERE tour_id = %s
        """,
        (tour_id,),
    )["total"]

    if count == 0:

        data = [

            (
                tour_id,
                date.today(),
                time(8, 0),
                "Bãi Sau",
                "Đón khách và giới thiệu chương trình.",
                "Bus",
                "Kiểm tra đủ khách.",
            ),

            (
                tour_id,
                date.today(),
                time(9, 30),
                "Tượng Chúa Kitô Vua",
                "Tham quan và chụp ảnh.",
                "Bus",
                "Nhắc khách mang nước.",
            ),

            (
                tour_id,
                date.today(),
                time(11, 30),
                "Nhà hàng Gành Hào",
                "Ăn trưa.",
                "Bus",
                "Kiểm tra suất ăn.",
            ),

            (
                tour_id,
                date.today(),
                time(14, 0),
                "Hải đăng Vũng Tàu",
                "Tham quan và thuyết minh.",
                "Bus",
                "Theo dõi thời gian.",
            ),

        ]

        for item in data:

            execute(
                """
                INSERT INTO itinerary
                (
                    tour_id,
                    tour_date,
                    time,
                    place,
                    activity,
                    transport,
                    notes
                )
                VALUES
                (%s,%s,%s,%s,%s,%s,%s)
                """,
                item,
            )


    # ========================================================
    # GUESTS
    # ========================================================

    count = query_one(
        """
        SELECT COUNT(*) AS total
        FROM guests
        WHERE tour_id = %s
        """,
        (tour_id,),
    )["total"]

    if count == 0:

        guests = [

            (
                "Nguyễn Văn An",
                "Male",
                31,
                "Vietnam",
                "0901111111",
                "101",
            ),

            (
                "Trần Thị Lan",
                "Female",
                28,
                "Vietnam",
                "0902222222",
                "102",
            ),

            (
                "John Smith",
                "Male",
                35,
                "United States",
                "0903333333",
                "103",
            ),

            (
                "Emily Brown",
                "Female",
                29,
                "United Kingdom",
                "0904444444",
                "104",
            ),

            (
                "Sophie Martin",
                "Female",
                32,
                "France",
                "0905555555",
                "105",
            ),

        ]

        for g in guests:

            execute(
                """
                INSERT INTO guests
                (
                    tour_id,
                    full_name,
                    gender,
                    age,
                    nationality,
                    phone,
                    room_number,
                    attendance
                )
                VALUES
                (%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    tour_id,
                    g[0],
                    g[1],
                    g[2],
                    g[3],
                    g[4],
                    g[5],
                    "Present",
                ),
            )


    # ========================================================
    # TASKS
    # ========================================================

    count = query_one(
        """
        SELECT COUNT(*) AS total
        FROM tasks
        WHERE tour_id = %s
        """,
        (tour_id,),
    )["total"]

    if count == 0:

        tasks = [

            (
                "Kiểm tra Arrival List",
                "Pre-tour",
                date.today(),
                time(6, 30),
                "Nguyễn Minh Anh",
                1,
            ),

            (
                "Chuẩn bị nước uống",
                "Preparation",
                date.today(),
                time(6, 45),
                "Nguyễn Minh Anh",
                1,
            ),

            (
                "Kiểm tra xe",
                "Transport",
                date.today(),
                time(7, 0),
                "Lê Văn Nam",
                0,
            ),

            (
                "Điểm danh khách",
                "Guest",
                date.today(),
                time(7, 30),
                "Nguyễn Minh Anh",
                0,
            ),

        ]

        for task in tasks:

            execute(
                """
                INSERT INTO tasks
                (
                    tour_id,
                    task_name,
                    task_type,
                    due_date,
                    due_time,
                    assigned_to,
                    done
                )
                VALUES
                (%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    tour_id,
                    task[0],
                    task[1],
                    task[2],
                    task[3],
                    task[4],
                    task[5],
                ),
            )


    # ========================================================
    # PLACES
    # ========================================================

    places = [

        (
            "Tượng Chúa Kitô Vua",
            "Vũng Tàu",
            "Landmark",
            "Một trong những biểu tượng nổi bật của Vũng Tàu.",
            "Công trình nằm trên Núi Nhỏ.",
            "Tầm nhìn thành phố và biển.",
            "Nên mang nước uống.",
        ),

        (
            "Hải đăng Vũng Tàu",
            "Núi Nhỏ",
            "Landmark",
            "Địa điểm nổi tiếng với góc nhìn rộng ra biển.",
            "Một công trình hàng hải lâu đời.",
            "Ngắm biển và chụp ảnh.",
            "Nên đến sáng sớm hoặc chiều.",
        ),

        (
            "Bãi Sau",
            "Vũng Tàu",
            "Beach",
            "Một trong những bãi biển nổi tiếng của thành phố.",
            "Khu vực phát triển mạnh về du lịch.",
            "Tắm biển và ngắm bình minh.",
            "Theo dõi thời tiết.",
        ),

        (
            "Hồ Mây Park",
            "Vũng Tàu",
            "Entertainment",
            "Khu vui chơi và nghỉ dưỡng trên Núi Lớn.",
            "Khu du lịch kết hợp thiên nhiên và vui chơi.",
            "Cáp treo, vui chơi và ngắm cảnh.",
            "Nên dành nửa ngày.",
        ),

    ]


    for p in places:

        exists = query_one(
            """
            SELECT id
            FROM places
            WHERE name = %s
            LIMIT 1
            """,
            (p[0],),
        )

        if not exists:

            execute(
                """
                INSERT INTO places
                (
                    name,
                    location,
                    category,
                    introduction,
                    history,
                    highlights,
                    tips
                )
                VALUES
                (%s,%s,%s,%s,%s,%s,%s)
                """,
                p,
            )


    # ========================================================
    # INCIDENT
    # ========================================================

    incident = query_one(
        """
        SELECT id
        FROM incidents
        WHERE title = %s
        LIMIT 1
        """,
        ("Khách quên hành lý trên xe",),
    )

    if not incident:

        execute(
            """
            INSERT INTO incidents
            (
                tour_id,
                incident_date,
                incident_time,
                type,
                title,
                description,
                solution,
                status,
                created_by
            )
            VALUES
            (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                tour_id,
                date.today(),
                time(15, 30),
                "Lost & Found",
                "Khách quên hành lý trên xe",
                "Khách phát hiện thiếu túi xách.",
                "Liên hệ tài xế kiểm tra và đã tìm thấy.",
                "Resolved",
                "Nguyễn Minh Anh",
            ),
        )


# ============================================================
# 11. START SYSTEM
# ============================================================

try:

    database_test()

    create_base_tables()

    repair_old_database()

    seed_demo_data()

except Exception as e:

    st.error(
        "❌ Không thể khởi động hệ thống database."
    )

    st.code(
        str(e),
        language="text",
    )

    st.info(
        """
        Kết nối MySQL đã được kiểm tra trước khi khởi tạo.

        Nếu xuất hiện lỗi SQL mới, hãy gửi nguyên dòng
        MySQL Error cho anh.
        """
    )

    st.stop()


# ============================================================
# 12. HEADER
# ============================================================

st.markdown(
    """
    <div class="hero">

        <h1>🧭 TourMate</h1>

        <p>
        Smart Tour Guide Management System
        </p>

        <p>
        Quản lý tour • Lịch trình • Khách hàng • Checklist
        • Điểm tham quan • Sự cố • Hướng dẫn viên
        </p>

    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 13. SIDEBAR
# ============================================================

st.sidebar.markdown(
    """
    <div style="text-align:center">

        <div style="font-size:55px">
        🧭
        </div>

        <h2>TourMate</h2>

        <p>
        Smart Tour Guide
        </p>

    </div>
    """,
    unsafe_allow_html=True,
)

menu = st.sidebar.radio(
    "MENU",
    [
        "📊 Dashboard",
        "🚌 Quản lý Tour",
        "🗺️ Lịch trình",
        "👥 Khách hàng",
        "✅ Checklist",
        "📍 Điểm tham quan",
        "🎤 Thư viện thuyết minh",
        "⚠️ Sự cố",
        "🧑‍💼 Hướng dẫn viên",
        "⚙️ Cài đặt",
    ],
)

st.sidebar.markdown("---")

st.sidebar.success(
    "🟢 MySQL Connected"
)

st.sidebar.caption(
    "TourMate v1.0"
)


# ============================================================
# 14. DASHBOARD
# ============================================================

if menu == "📊 Dashboard":

    st.subheader("📊 Dashboard")

    c1, c2, c3, c4 = st.columns(4)

    total_tours = query_one(
        "SELECT COUNT(*) AS total FROM tours"
    )["total"]

    total_guests = query_one(
        "SELECT COUNT(*) AS total FROM guests"
    )["total"]

    total_guides = query_one(
        "SELECT COUNT(*) AS total FROM guides"
    )["total"]

    open_incidents = query_one(
        """
        SELECT COUNT(*) AS total
        FROM incidents
        WHERE status = 'Open'
        """
    )["total"]

    c1.metric(
        "🚌 Tổng Tour",
        total_tours,
    )

    c2.metric(
        "👥 Khách",
        total_guests,
    )

    c3.metric(
        "🧑‍💼 Hướng dẫn viên",
        total_guides,
    )

    c4.metric(
        "⚠️ Sự cố mở",
        open_incidents,
    )

    st.markdown("---")

    st.subheader("🚌 Tour hôm nay")

    today = date.today()

    today_tours = query_df(
        """
        SELECT

            t.code AS 'Mã tour',

            t.name AS 'Tên tour',

            t.start_date AS 'Bắt đầu',

            t.end_date AS 'Kết thúc',

            t.start_time AS 'Giờ',

            t.pickup_location AS 'Điểm đón',

            t.total_guests AS 'Khách',

            t.status AS 'Trạng thái',

            COALESCE(
                g.name,
                'Chưa phân công'
            ) AS 'HDV'

        FROM tours t

        LEFT JOIN guides g
            ON t.guide_id = g.id

        WHERE t.start_date <= %s
          AND t.end_date >= %s

        ORDER BY t.start_time
        """,
        (today, today),
    )

    if today_tours.empty:

        st.info(
            "Hôm nay chưa có tour."
        )

    else:

        st.dataframe(
            today_tours,
            use_container_width=True,
            hide_index=True,
        )


    st.subheader("📅 Tour sắp tới")

    upcoming = query_df(
        """
        SELECT

            t.code AS 'Mã tour',

            t.name AS 'Tên tour',

            t.start_date AS 'Ngày bắt đầu',

            t.end_date AS 'Ngày kết thúc',

            t.total_guests AS 'Khách',

            t.status AS 'Trạng thái',

            COALESCE(
                g.name,
                'Chưa phân công'
            ) AS 'HDV'

        FROM tours t

        LEFT JOIN guides g
            ON t.guide_id = g.id

        WHERE t.start_date >= %s

        ORDER BY t.start_date

        LIMIT 10
        """,
        (today,),
    )

    st.dataframe(
        upcoming,
        use_container_width=True,
        hide_index=True,
    )


    st.subheader("✅ Checklist")

    task_info = query_one(
        """
        SELECT

            COUNT(*) AS total,

            SUM(
                CASE
                WHEN done = 1
                THEN 1
                ELSE 0
                END
            ) AS completed

        FROM tasks
        """
    )

    total_tasks = task_info["total"] or 0
    completed = task_info["completed"] or 0

    if total_tasks:

        progress = completed / total_tasks

        st.progress(progress)

        st.write(
            f"Hoàn thành **{completed}/{total_tasks}** công việc "
            f"({progress:.0%})"
        )


# ============================================================
# 15. TOUR MANAGEMENT
# ============================================================

elif menu == "🚌 Quản lý Tour":

    st.subheader("🚌 Quản lý Tour")

    tab1, tab2 = st.tabs(
        [
            "📋 Danh sách",
            "➕ Tạo Tour",
        ]
    )

    with tab1:

        search = st.text_input(
            "🔎 Tìm kiếm",
            placeholder="Mã tour hoặc tên tour",
        )

        if search:

            tours = query_df(
                """
                SELECT

                    t.code AS 'Mã tour',

                    t.name AS 'Tên tour',

                    t.start_date AS 'Bắt đầu',

                    t.end_date AS 'Kết thúc',

                    t.start_time AS 'Giờ',

                    t.total_guests AS 'Khách',

                    t.status AS 'Trạng thái',

                    COALESCE(
                        g.name,
                        'Chưa phân công'
                    ) AS 'HDV'

                FROM tours t

                LEFT JOIN guides g
                    ON t.guide_id = g.id

                WHERE
                    t.code LIKE %s
                    OR t.name LIKE %s

                ORDER BY t.start_date DESC
                """,
                (
                    f"%{search}%",
                    f"%{search}%",
                ),
            )

        else:

            tours = query_df(
                """
                SELECT

                    t.code AS 'Mã tour',

                    t.name AS 'Tên tour',

                    t.start_date AS 'Bắt đầu',

                    t.end_date AS 'Kết thúc',

                    t.start_time AS 'Giờ',

                    t.total_guests AS 'Khách',

                    t.status AS 'Trạng thái',

                    COALESCE(
                        g.name,
                        'Chưa phân công'
                    ) AS 'HDV'

                FROM tours t

                LEFT JOIN guides g
                    ON t.guide_id = g.id

                ORDER BY t.start_date DESC
                """
            )

        if tours.empty:

            st.info(
                "Chưa có tour."
            )

        else:

            st.dataframe(
                tours,
                use_container_width=True,
                hide_index=True,
            )


    with tab2:

        guides = query(
            """
            SELECT id, name
            FROM guides
            WHERE status = 'Active'
            ORDER BY name
            """
        )

        if not guides:

            st.warning(
                "Chưa có hướng dẫn viên."
            )

        else:

            with st.form("create_tour"):

                c1, c2 = st.columns(2)

                with c1:

                    code = st.text_input(
                        "Mã tour *",
                        placeholder="TM-VT-003",
                    )

                    name = st.text_input(
                        "Tên tour *",
                        placeholder="Vũng Tàu Discovery",
                    )

                    start_date = st.date_input(
                        "Ngày bắt đầu",
                        date.today(),
                    )

                    end_date = st.date_input(
                        "Ngày kết thúc",
                        date.today(),
                    )

                    start_time = st.time_input(
                        "Giờ xuất phát",
                        time(7, 30),
                    )

                with c2:

                    pickup = st.text_input(
                        "Điểm đón"
                    )

                    hotel = st.text_input(
                        "Khách sạn"
                    )

                    vehicle = st.text_input(
                        "Phương tiện",
                        "Tourist Bus",
                    )

                    driver = st.text_input(
                        "Tài xế"
                    )

                    guests = st.number_input(
                        "Số khách",
                        0,
                        500,
                        20,
                    )

                    guide = st.selectbox(
                        "Hướng dẫn viên",
                        guides,
                        format_func=lambda x:
                        x["name"],
                    )

                status = st.selectbox(
                    "Trạng thái",
                    [
                        "Scheduled",
                        "In Progress",
                        "Completed",
                        "Cancelled",
                    ],
                )

                notes = st.text_area(
                    "Ghi chú"
                )

                submit = st.form_submit_button(
                    "💾 Tạo Tour",
                    type="primary",
                )

                if submit:

                    if not code or not name:

                        st.error(
                            "Vui lòng nhập mã và tên tour."
                        )

                    elif end_date < start_date:

                        st.error(
                            "Ngày kết thúc phải sau hoặc bằng ngày bắt đầu."
                        )

                    else:

                        try:

                            execute(
                                """
                                INSERT INTO tours
                                (
                                    code,
                                    name,
                                    guide_id,
                                    start_date,
                                    end_date,
                                    start_time,
                                    pickup_location,
                                    hotel,
                                    vehicle,
                                    driver,
                                    total_guests,
                                    status,
                                    notes
                                )
                                VALUES
                                (
                                    %s,%s,%s,%s,%s,%s,%s,
                                    %s,%s,%s,%s,%s,%s
                                )
                                """,
                                (
                                    code,
                                    name,
                                    guide["id"],
                                    start_date,
                                    end_date,
                                    start_time,
                                    pickup,
                                    hotel,
                                    vehicle,
                                    driver,
                                    guests,
                                    status,
                                    notes,
                                ),
                            )

                            st.success(
                                "🎉 Tạo tour thành công!"
                            )

                            st.rerun()

                        except Exception as e:

                            st.error(
                                "Không thể tạo tour."
                            )

                            st.code(
                                str(e)
                            )


# ============================================================
# 16. ITINERARY
# ============================================================

elif menu == "🗺️ Lịch trình":

    st.subheader("🗺️ Lịch trình")

    tours = query(
        """
        SELECT id, code, name
        FROM tours
        ORDER BY start_date DESC
        """
    )

    if not tours:

        st.info(
            "Chưa có tour."
        )

    else:

        selected = st.selectbox(
            "Chọn tour",
            tours,
            format_func=lambda x:
            f"{x['code']} - {x['name']}",
        )

        data = query_df(
            """
            SELECT

                tour_date AS 'Ngày',

                time AS 'Giờ',

                place AS 'Địa điểm',

                activity AS 'Hoạt động',

                transport AS 'Phương tiện',

                notes AS 'Ghi chú'

            FROM itinerary

            WHERE tour_id = %s

            ORDER BY tour_date, time
            """,
            (selected["id"],),
        )

        if data.empty:

            st.info(
                "Tour chưa có lịch trình."
            )

        else:

            st.dataframe(
                data,
                use_container_width=True,
                hide_index=True,
            )


        st.markdown("### ➕ Thêm lịch trình")

        with st.form("add_itinerary"):

            c1, c2 = st.columns(2)

            with c1:

                d = st.date_input(
                    "Ngày",
                    date.today(),
                )

                t = st.time_input(
                    "Giờ",
                    time(8, 0),
                )

                place = st.text_input(
                    "Địa điểm *"
                )

            with c2:

                activity = st.text_area(
                    "Hoạt động"
                )

                transport = st.text_input(
                    "Phương tiện",
                    "Bus",
                )

                notes = st.text_area(
                    "Ghi chú"
                )

            submit = st.form_submit_button(
                "➕ Thêm",
                type="primary",
            )

            if submit:

                if not place:

                    st.error(
                        "Vui lòng nhập địa điểm."
                    )

                else:

                    execute(
                        """
                        INSERT INTO itinerary
                        (
                            tour_id,
                            tour_date,
                            time,
                            place,
                            activity,
                            transport,
                            notes
                        )
                        VALUES
                        (%s,%s,%s,%s,%s,%s,%s)
                        """,
                        (
                            selected["id"],
                            d,
                            t,
                            place,
                            activity,
                            transport,
                            notes,
                        ),
                    )

                    st.success(
                        "Đã thêm lịch trình."
                    )

                    st.rerun()


# ============================================================
# 17. GUESTS
# ============================================================

elif menu == "👥 Khách hàng":

    st.subheader("👥 Khách hàng")

    tours = query(
        """
        SELECT id, code, name
        FROM tours
        ORDER BY start_date DESC
        """
    )

    if not tours:

        st.info(
            "Chưa có tour."
        )

    else:

        selected = st.selectbox(
            "Chọn tour",
            tours,
            format_func=lambda x:
            f"{x['code']} - {x['name']}",
        )

        guests = query_df(
            """
            SELECT

                full_name AS 'Họ tên',

                gender AS 'Giới tính',

                age AS 'Tuổi',

                nationality AS 'Quốc tịch',

                phone AS 'Điện thoại',

                room_number AS 'Phòng',

                attendance AS 'Điểm danh',

                special_request AS 'Yêu cầu'

            FROM guests

            WHERE tour_id = %s

            ORDER BY full_name
            """,
            (selected["id"],),
        )

        st.metric(
            "Tổng khách",
            len(guests),
        )

        if not guests.empty:

            st.dataframe(
                guests,
                use_container_width=True,
                hide_index=True,
            )


        st.markdown("### ➕ Thêm khách")

        with st.form("add_guest"):

            c1, c2 = st.columns(2)

            with c1:

                full_name = st.text_input(
                    "Họ tên *"
                )

                gender = st.selectbox(
                    "Giới tính",
                    [
                        "Male",
                        "Female",
                        "Other",
                    ],
                )

                age = st.number_input(
                    "Tuổi",
                    0,
                    120,
                    25,
                )

                nationality = st.text_input(
                    "Quốc tịch",
                    "Vietnam",
                )

            with c2:

                phone = st.text_input(
                    "Điện thoại"
                )

                room = st.text_input(
                    "Số phòng"
                )

                attendance = st.selectbox(
                    "Điểm danh",
                    [
                        "Present",
                        "Absent",
                        "Late",
                    ],
                )

                special = st.text_area(
                    "Yêu cầu đặc biệt"
                )

            submit = st.form_submit_button(
                "➕ Thêm khách",
                type="primary",
            )

            if submit:

                if not full_name:

                    st.error(
                        "Vui lòng nhập họ tên."
                    )

                else:

                    execute(
                        """
                        INSERT INTO guests
                        (
                            tour_id,
                            full_name,
                            gender,
                            age,
                            nationality,
                            phone,
                            room_number,
                            special_request,
                            attendance
                        )
                        VALUES
                        (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        """,
                        (
                            selected["id"],
                            full_name,
                            gender,
                            age,
                            nationality,
                            phone,
                            room,
                            special,
                            attendance,
                        ),
                    )

                    st.success(
                        "Đã thêm khách."
                    )

                    st.rerun()


# ============================================================
# 18. CHECKLIST
# ============================================================

elif menu == "✅ Checklist":

    st.subheader("✅ Checklist")

    tours = query(
        """
        SELECT id, code, name
        FROM tours
        ORDER BY start_date DESC
        """
    )

    if not tours:

        st.info(
            "Chưa có tour."
        )

    else:

        selected = st.selectbox(
            "Chọn tour",
            tours,
            format_func=lambda x:
            f"{x['code']} - {x['name']}",
        )

        tasks = query(
            """
            SELECT *
            FROM tasks
            WHERE tour_id = %s
            ORDER BY due_date, due_time
            """,
            (selected["id"],),
        )

        if tasks:

            for task in tasks:

                checked = st.checkbox(
                    task["task_name"],
                    value=bool(task["done"]),
                    key=f"task_{task['id']}",
                )

                if checked != bool(task["done"]):

                    execute(
                        """
                        UPDATE tasks
                        SET done = %s
                        WHERE id = %s
                        """,
                        (
                            1 if checked else 0,
                            task["id"],
                        ),
                    )

                    st.rerun()

        else:

            st.info(
                "Chưa có checklist."
            )


# ============================================================
# 19. PLACES
# ============================================================

elif menu == "📍 Điểm tham quan":

    st.subheader("📍 Điểm tham quan")

    places = query(
        """
        SELECT *
        FROM places
        ORDER BY name
        """
    )

    if not places:

        st.info(
            "Chưa có điểm tham quan."
        )

    else:

        for place in places:

            with st.expander(
                f"📍 {place['name']} — {place['location']}"
            ):

                c1, c2 = st.columns(
                    [1, 2]
                )

                with c1:

                    if place["image_url"]:

                        st.image(
                            place["image_url"],
                            use_container_width=True,
                        )

                with c2:

                    st.write(
                        place["introduction"]
                    )

                    st.markdown(
                        "**📖 Lịch sử**"
                    )

                    st.write(
                        place["history"]
                    )

                    st.markdown(
                        "**⭐ Điểm nổi bật**"
                    )

                    st.write(
                        place["highlights"]
                    )

                    st.markdown(
                        "**💡 Lưu ý**"
                    )

                    st.write(
                        place["tips"]
                    )


# ============================================================
# 20. THUYẾT MINH
# ============================================================

elif menu == "🎤 Thư viện thuyết minh":

    st.subheader(
        "🎤 Thư viện thuyết minh"
    )

    places = query(
        """
        SELECT *
        FROM places
        ORDER BY name
        """
    )

    if not places:

        st.info(
            "Chưa có điểm tham quan."
        )

    else:

        selected = st.selectbox(
            "Chọn địa điểm",
            places,
            format_func=lambda x:
            x["name"],
        )

        st.markdown(
            f"## 🎙️ {selected['name']}"
        )

        st.info(
            selected["introduction"]
        )

        st.markdown("### 📖 Lịch sử")

        st.write(
            selected["history"]
        )

        st.markdown("### ⭐ Điểm nổi bật")

        st.write(
            selected["highlights"]
        )

        st.markdown("### 💡 Lưu ý cho HDV")

        st.warning(
            selected["tips"]
        )

        st.markdown(
            "### 🗣️ Mẫu lời dẫn"
        )

        st.code(
            f"""
Xin chào quý khách!

Ngay trước mắt chúng ta là
{selected['name']}.

{selected['introduction']}

Trong quá trình tham quan,
quý khách vui lòng đi theo đoàn
và chú ý thời gian tập trung.

Chúc quý khách có một trải nghiệm
thật vui vẻ và đáng nhớ!
            """,
            language="text",
        )


# ============================================================
# 21. INCIDENTS
# ============================================================

elif menu == "⚠️ Sự cố":

    st.subheader(
        "⚠️ Quản lý sự cố"
    )

    incidents = query_df(
        """
        SELECT

            incident_date AS 'Ngày',

            incident_time AS 'Giờ',

            type AS 'Loại',

            title AS 'Tiêu đề',

            description AS 'Mô tả',

            solution AS 'Xử lý',

            status AS 'Trạng thái',

            created_by AS 'Người tạo'

        FROM incidents

        ORDER BY
            incident_date DESC,
            incident_time DESC
        """
    )

    if incidents.empty:

        st.info(
            "Chưa có sự cố."
        )

    else:

        st.dataframe(
            incidents,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# 22. GUIDES
# ============================================================

elif menu == "🧑‍💼 Hướng dẫn viên":

    st.subheader(
        "🧑‍💼 Hướng dẫn viên"
    )

    guides = query_df(
        """
        SELECT

            name AS 'Họ tên',

            phone AS 'Điện thoại',

            email AS 'Email',

            language AS 'Ngôn ngữ',

            experience_years AS 'Kinh nghiệm',

            status AS 'Trạng thái'

        FROM guides

        ORDER BY name
        """
    )

    if not guides.empty:

        st.dataframe(
            guides,
            use_container_width=True,
            hide_index=True,
        )

    st.markdown(
        "### ➕ Thêm hướng dẫn viên"
    )

    with st.form("new_guide"):

        c1, c2 = st.columns(2)

        with c1:

            name = st.text_input(
                "Họ tên *"
            )

            phone = st.text_input(
                "Điện thoại"
            )

            email = st.text_input(
                "Email"
            )

        with c2:

            language = st.text_input(
                "Ngôn ngữ",
                "Vietnamese, English",
            )

            experience = st.number_input(
                "Kinh nghiệm",
                0,
                50,
                1,
            )

            status = st.selectbox(
                "Trạng thái",
                [
                    "Active",
                    "Inactive",
                ],
            )

        submit = st.form_submit_button(
            "➕ Thêm HDV",
            type="primary",
        )

        if submit:

            if not name:

                st.error(
                    "Vui lòng nhập họ tên."
                )

            else:

                execute(
                    """
                    INSERT INTO guides
                    (
                        name,
                        phone,
                        email,
                        language,
                        experience_years,
                        status
                    )
                    VALUES
                    (%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        name,
                        phone,
                        email,
                        language,
                        experience,
                        status,
                    ),
                )

                st.success(
                    "Đã thêm hướng dẫn viên."
                )

                st.rerun()


# ============================================================
# 23. SETTINGS
# ============================================================

elif menu == "⚙️ Cài đặt":

    st.subheader(
        "⚙️ Cài đặt hệ thống"
    )

    try:

        info = database_test()

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Database",
            info["database"],
        )

        c2.metric(
            "User",
            info["user"],
        )

        c3.metric(
            "Status",
            "Connected",
        )

        st.success(
            "🟢 Aiven MySQL đang hoạt động."
        )

        st.write(
            f"MySQL version: `{info['version']}`"
        )

    except Exception as e:

        st.error(
            "Không thể kiểm tra database."
        )

        st.code(
            str(e)
        )


    st.markdown("---")

    st.subheader(
        "📊 Database"
    )

    table_list = [
        "guides",
        "tours",
        "itinerary",
        "guests",
        "tasks",
        "places",
        "incidents",
    ]

    stats = []

    for table in table_list:

        try:

            result = query_one(
                f"""
                SELECT COUNT(*) AS total
                FROM `{table}`
                """
            )

            stats.append(
                {
                    "Bảng": table,
                    "Số bản ghi": result["total"],
                }
            )

        except Exception:

            stats.append(
                {
                    "Bảng": table,
                    "Số bản ghi": "Error",
                }
            )

    st.dataframe(
        pd.DataFrame(stats),
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# 24. FOOTER
# ============================================================

st.markdown(
    """
    <div style="
        text-align:center;
        padding:40px 0 10px;
        color:#64748b;
        font-size:13px;
    ">

        🧭 <b>TourMate</b>
        <br>
        Smart Tour Guide Management System
        <br>
        Tourism & Travel Management Application

    </div>
    """,
    unsafe_allow_html=True,
)
