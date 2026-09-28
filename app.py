import streamlit as st
import pymysql
import pandas as pd

from pymysql.cursors import DictCursor
from datetime import datetime, date, time


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="TourMate - Smart Tour Guide",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# DATABASE CONFIG
# ============================================================

# Khuyến nghị:
# Streamlit Cloud → Settings → Secrets
#
# [mysql]
# password = "MAT_KHAU_AIVEN_CUA_EM"
#
# Không nên commit password thật lên GitHub.

try:
    AIVEN_PASSWORD = st.secrets["mysql"]["password"]
except Exception:
    AIVEN_PASSWORD = ""


MYSQL_CONFIG = {
    "host": "mysql-19728385-npmaihuong-927f.b.aivencloud.com",
    "port": 27942,
    "user": "avnadmin",
    "password": AVNS_zBDlzsF9I5fC-EdWcl0,
    "database": "defaultdb",
}


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_conn():

    if not MYSQL_CONFIG["password"]:
        raise RuntimeError(
            "Chưa cấu hình mật khẩu Aiven MySQL. "
            "Hãy thêm password vào Streamlit Secrets."
        )

    return pymysql.connect(
        host=MYSQL_CONFIG["host"],
        port=int(MYSQL_CONFIG["port"]),
        user=MYSQL_CONFIG["user"],
        password=MYSQL_CONFIG["password"],
        database=MYSQL_CONFIG["database"],
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=True,
        connect_timeout=20,
        read_timeout=30,
        write_timeout=30
    )


# ============================================================
# DATABASE HELPERS
# ============================================================

def execute(sql, params=()):

    conn = None

    try:

        conn = get_conn()

        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.lastrowid

    except pymysql.MySQLError as e:

        error_code = e.args[0] if e.args else "UNKNOWN"
        error_message = (
            e.args[1]
            if len(e.args) > 1
            else str(e)
        )

        raise RuntimeError(
            f"MySQL Error {error_code}: {error_message}"
        ) from e

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

        error_code = e.args[0] if e.args else "UNKNOWN"
        error_message = (
            e.args[1]
            if len(e.args) > 1
            else str(e)
        )

        raise RuntimeError(
            f"MySQL Error {error_code}: {error_message}"
        ) from e

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
# DATABASE CHECK
# ============================================================

def check_database():

    conn = None

    try:

        conn = get_conn()

        with conn.cursor() as cursor:

            cursor.execute(
                "SELECT 1 AS connection_ok"
            )

            result = cursor.fetchone()

            cursor.execute(
                "SELECT VERSION() AS db_version"
            )

            version_result = cursor.fetchone()

            cursor.execute(
                "SELECT DATABASE() AS db_name"
            )

            database_result = cursor.fetchone()

            # Không dùng alias current_user
            cursor.execute(
                "SELECT CURRENT_USER() AS db_user"
            )

            user_result = cursor.fetchone()

        return True, {
            "connection_ok": result["connection_ok"],
            "version": version_result["db_version"],
            "database_name": database_result["db_name"],
            "current_user": user_result["db_user"]
        }

    except Exception as e:

        return False, str(e)

    finally:

        if conn:
            conn.close()


# ============================================================
# CHECK TABLE EXISTENCE
# ============================================================

def table_exists(table_name):

    rows = query(
        """
        SELECT COUNT(*) AS total
        FROM information_schema.tables
        WHERE table_schema = DATABASE()
          AND table_name = %s
        """,
        (table_name,)
    )

    return rows[0]["total"] > 0


# ============================================================
# GET EXISTING COLUMNS
# ============================================================

def get_columns(table_name):

    rows = query(
        """
        SELECT
            COLUMN_NAME
        FROM information_schema.columns
        WHERE table_schema = DATABASE()
          AND table_name = %s
        """,
        (table_name,)
    )

    return {
        row["COLUMN_NAME"]
        for row in rows
    }


# ============================================================
# ADD MISSING COLUMN
# ============================================================

def ensure_column(
    table_name,
    column_name,
    column_definition
):

    columns = get_columns(table_name)

    if column_name not in columns:

        execute(
            f"""
            ALTER TABLE `{table_name}`
            ADD COLUMN `{column_name}` {column_definition}
            """
        )

        return True

    return False


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_db():

    # ========================================================
    # 1. GUIDES
    # ========================================================

    execute(
        """
        CREATE TABLE IF NOT EXISTS guides (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(150) NOT NULL,
            phone VARCHAR(30),
            email VARCHAR(150),
            language VARCHAR(100),
            experience_years INT DEFAULT 0,
            status VARCHAR(30) DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )

    # ========================================================
    # 2. TOURS
    # ========================================================

    execute(
        """
        CREATE TABLE IF NOT EXISTS tours (
            id INT AUTO_INCREMENT PRIMARY KEY,
            code VARCHAR(50) NOT NULL UNIQUE,
            name VARCHAR(255) NOT NULL,
            guide_id INT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            start_time VARCHAR(10),
            pickup_location VARCHAR(255),
            hotel VARCHAR(255),
            vehicle VARCHAR(255),
            driver VARCHAR(150),
            total_guests INT DEFAULT 0,
            status VARCHAR(50) DEFAULT 'Scheduled',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )

    # ========================================================
    # 3. ITINERARY
    # ========================================================

    execute(
        """
        CREATE TABLE IF NOT EXISTS itinerary (
            id INT AUTO_INCREMENT PRIMARY KEY,
            tour_id INT NOT NULL,
            tour_date DATE NOT NULL,
            time VARCHAR(10),
            place VARCHAR(255) NOT NULL,
            activity VARCHAR(255),
            transport VARCHAR(100),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )

    # ========================================================
    # 4. GUESTS
    # ========================================================

    execute(
        """
        CREATE TABLE IF NOT EXISTS guests (
            id INT AUTO_INCREMENT PRIMARY KEY,
            tour_id INT NOT NULL,
            full_name VARCHAR(150) NOT NULL,
            gender VARCHAR(30),
            age INT,
            nationality VARCHAR(100),
            phone VARCHAR(30),
            room_number VARCHAR(50),
            special_request TEXT,
            attendance VARCHAR(50) DEFAULT 'Chưa điểm danh',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )

    # ========================================================
    # 5. TASKS
    # ========================================================

    execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INT AUTO_INCREMENT PRIMARY KEY,
            tour_id INT NULL,
            task_name VARCHAR(255) NOT NULL,
            task_type VARCHAR(100),
            due_date DATE,
            due_time VARCHAR(10),
            assigned_to VARCHAR(150),
            done TINYINT(1) DEFAULT 0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )

    # ========================================================
    # 6. PLACES
    # ========================================================

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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )

    # ========================================================
    # 7. INCIDENTS
    # ========================================================

    execute(
        """
        CREATE TABLE IF NOT EXISTS incidents (
            id INT AUTO_INCREMENT PRIMARY KEY,
            tour_id INT NULL,
            incident_date DATE NOT NULL,
            incident_time VARCHAR(10),
            type VARCHAR(100),
            title VARCHAR(255) NOT NULL,
            description TEXT,
            solution TEXT,
            status VARCHAR(50) DEFAULT 'Open',
            created_by VARCHAR(150),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )

    # ========================================================
    # SCHEMA MIGRATION
    #
    # Quan trọng:
    # CREATE TABLE IF NOT EXISTS không sửa bảng cũ.
    # Vì vậy phải kiểm tra cột và bổ sung nếu thiếu.
    # ========================================================

    # --------------------------------------------------------
    # GUIDES
    # --------------------------------------------------------

    guide_columns = {
        "name": "VARCHAR(150) NULL",
        "phone": "VARCHAR(30) NULL",
        "email": "VARCHAR(150) NULL",
        "language": "VARCHAR(100) NULL",
        "experience_years": "INT DEFAULT 0",
        "status": "VARCHAR(30) DEFAULT 'Active'",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    }

    for column, definition in guide_columns.items():

        ensure_column(
            "guides",
            column,
            definition
        )

    # --------------------------------------------------------
    # TOURS
    # --------------------------------------------------------

    tour_columns = {
        "code": "VARCHAR(50) NULL",
        "name": "VARCHAR(255) NULL",
        "guide_id": "INT NULL",
        "start_date": "DATE NULL",
        "end_date": "DATE NULL",
        "start_time": "VARCHAR(10) NULL",
        "pickup_location": "VARCHAR(255) NULL",
        "hotel": "VARCHAR(255) NULL",
        "vehicle": "VARCHAR(255) NULL",
        "driver": "VARCHAR(150) NULL",
        "total_guests": "INT DEFAULT 0",
        "status": "VARCHAR(50) DEFAULT 'Scheduled'",
        "notes": "TEXT NULL",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    }

    for column, definition in tour_columns.items():

        ensure_column(
            "tours",
            column,
            definition
        )

    # --------------------------------------------------------
    # ITINERARY
    # --------------------------------------------------------

    itinerary_columns = {
        "tour_id": "INT NULL",
        "tour_date": "DATE NULL",
        "time": "VARCHAR(10) NULL",
        "place": "VARCHAR(255) NULL",
        "activity": "VARCHAR(255) NULL",
        "transport": "VARCHAR(100) NULL",
        "notes": "TEXT NULL",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    }

    for column, definition in itinerary_columns.items():

        ensure_column(
            "itinerary",
            column,
            definition
        )

    # --------------------------------------------------------
    # GUESTS
    # --------------------------------------------------------

    guest_columns = {
        "tour_id": "INT NULL",
        "full_name": "VARCHAR(150) NULL",
        "gender": "VARCHAR(30) NULL",
        "age": "INT NULL",
        "nationality": "VARCHAR(100) NULL",
        "phone": "VARCHAR(30) NULL",
        "room_number": "VARCHAR(50) NULL",
        "special_request": "TEXT NULL",
        "attendance": "VARCHAR(50) DEFAULT 'Chưa điểm danh'",
        "notes": "TEXT NULL",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    }

    for column, definition in guest_columns.items():

        ensure_column(
            "guests",
            column,
            definition
        )

    # --------------------------------------------------------
    # TASKS
    # --------------------------------------------------------

    task_columns = {
        "tour_id": "INT NULL",
        "task_name": "VARCHAR(255) NULL",
        "task_type": "VARCHAR(100) NULL",
        "due_date": "DATE NULL",
        "due_time": "VARCHAR(10) NULL",
        "assigned_to": "VARCHAR(150) NULL",
        "done": "TINYINT(1) DEFAULT 0",
        "notes": "TEXT NULL",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    }

    for column, definition in task_columns.items():

        ensure_column(
            "tasks",
            column,
            definition
        )

    # --------------------------------------------------------
    # PLACES
    # --------------------------------------------------------

    place_columns = {
        "name": "VARCHAR(255) NULL",
        "location": "VARCHAR(255) NULL",
        "category": "VARCHAR(100) NULL",
        "introduction": "TEXT NULL",
        "history": "TEXT NULL",
        "highlights": "TEXT NULL",
        "tips": "TEXT NULL",
        "image_url": "TEXT NULL",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    }

    for column, definition in place_columns.items():

        ensure_column(
            "places",
            column,
            definition
        )

    # --------------------------------------------------------
    # INCIDENTS
    # --------------------------------------------------------

    incident_columns = {
        "tour_id": "INT NULL",
        "incident_date": "DATE NULL",
        "incident_time": "VARCHAR(10) NULL",
        "type": "VARCHAR(100) NULL",
        "title": "VARCHAR(255) NULL",
        "description": "TEXT NULL",
        "solution": "TEXT NULL",
        "status": "VARCHAR(50) DEFAULT 'Open'",
        "created_by": "VARCHAR(150) NULL",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    }

    for column, definition in incident_columns.items():

        ensure_column(
            "incidents",
            column,
            definition
        )

    # ========================================================
    # DEMO GUIDE
    # ========================================================

    guide_count = query_one(
        "SELECT COUNT(*) AS total FROM guides"
    )["total"]

    if guide_count == 0:

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
            VALUES (%s,%s,%s,%s,%s,%s)
            """,
            (
                "Nguyễn Thị Hương",
                "0900000000",
                "guide@example.com",
                "Vietnamese, English",
                2,
                "Active"
            )
        )

    # ========================================================
    # DEMO PLACES
    # ========================================================

    place_count = query_one(
        "SELECT COUNT(*) AS total FROM places"
    )["total"]

    if place_count == 0:

        demo_places = [

            (
                "Tháp Tam Thắng",
                "Vũng Tàu",
                "Điểm tham quan",
                "Tháp Tam Thắng là một công trình biểu tượng gắn với thành phố Vũng Tàu.",
                "Đây là địa điểm mang ý nghĩa văn hóa và du lịch của khu vực.",
                "Kiến trúc, cảnh quan, chụp ảnh.",
                "Nên giới thiệu ngắn gọn lịch sử và ý nghĩa biểu tượng.",
                ""
            ),

            (
                "Bãi Sau Vũng Tàu",
                "Vũng Tàu",
                "Biển",
                "Bãi Sau là một trong những khu vực biển nổi tiếng của Vũng Tàu.",
                "Khu vực phát triển mạnh về du lịch biển.",
                "Tắm biển, ngắm cảnh, hoạt động tập thể.",
                "Nhắc khách giữ tài sản cá nhân và tuân thủ quy định an toàn.",
                ""
            ),

            (
                "Chợ Đà Lạt",
                "Đà Lạt",
                "Mua sắm",
                "Chợ Đà Lạt là khu vực mua sắm và trải nghiệm ẩm thực nổi tiếng.",
                "Chợ phát triển cùng quá trình đô thị hóa và du lịch Đà Lạt.",
                "Đặc sản, đồ lưu niệm, trái cây.",
                "Hướng dẫn khách thống nhất thời gian tập trung.",
                ""
            )
        ]

        for place in demo_places:

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
                    tips,
                    image_url
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                place
            )


# ============================================================
# INITIAL DATABASE
# ============================================================

if not MYSQL_CONFIG["password"]:

    st.error(
        "🔐 Chưa cấu hình mật khẩu Aiven MySQL."
    )

    st.info(
        """
        Vào Streamlit Cloud:

        Manage app → Settings → Secrets

        Thêm:

        [mysql]
        password = "MẬT_KHẨU_AIVEN_CỦA_EM"
        """
    )

    st.stop()


db_ok, db_info = check_database()

if not db_ok:

    st.error(
        "🔴 KHÔNG THỂ KẾT NỐI AIVEN MYSQL"
    )

    st.code(
        db_info,
        language="text"
    )

    st.warning(
        """
        Kiểm tra:
        • Host
        • Port
        • Username
        • Password
        • Aiven service đang Running
        """
    )

    st.stop()


# ============================================================
# INIT DATABASE
# ============================================================

try:

    init_db()

except Exception as e:

    st.error(
        "🔴 Không thể khởi tạo/cập nhật database."
    )

    st.code(
        str(e),
        language="text"
    )

    st.stop()


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def format_date(value):

    if value is None:
        return ""

    try:
        return pd.to_datetime(value).strftime(
            "%d/%m/%Y"
        )

    except Exception:

        return str(value)


def status_badge(status):

    badges = {

        "Scheduled":
            "🟡 Đã lên lịch",

        "Confirmed":
            "🟢 Đã xác nhận",

        "Completed":
            "🔵 Hoàn thành",

        "Cancelled":
            "🔴 Đã hủy",

        "Open":
            "🔴 Đang xử lý",

        "Processing":
            "🟡 Đang xử lý",

        "Resolved":
            "🟢 Đã xử lý"
    }

    return badges.get(
        status,
        status
    )


def get_today_tours():

    return query(
        """
        SELECT
            t.*,
            g.name AS guide_name
        FROM tours t
        LEFT JOIN guides g
            ON t.guide_id = g.id
        WHERE t.start_date <= CURDATE()
          AND t.end_date >= CURDATE()
          AND COALESCE(t.status, '') != 'Cancelled'
        ORDER BY t.start_time ASC
        """
    )


def get_tour_options():

    tours = query(
        """
        SELECT
            id,
            code,
            name,
            start_date,
            end_date
        FROM tours
        ORDER BY start_date DESC, id DESC
        """
    )

    result = {}

    for tour in tours:

        label = (
            f"{tour['code'] or 'NO-CODE'} - "
            f"{tour['name'] or 'Chưa đặt tên'} "
            f"({format_date(tour['start_date'])})"
        )

        result[label] = tour["id"]

    return result


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("🧭 TourMate")

    st.caption(
        "Smart Tour Guide Management System"
    )

    st.divider()

    menu = st.radio(
        "MENU",
        [
            "🏠 Dashboard",
            "📅 Lịch tour",
            "🚌 Quản lý tour",
            "🗺️ Lịch trình",
            "👥 Khách du lịch",
            "🎤 Kho thuyết minh",
            "✅ Checklist",
            "🚨 Sự cố",
            "👨‍✈️ Hướng dẫn viên",
            "⚙️ Cài đặt dữ liệu"
        ]
    )

    st.divider()

    st.success(
        "🟢 MySQL Connected"
    )

    st.caption(
        f"Database: {MYSQL_CONFIG['database']}"
    )

    st.caption(
        f"Server: {MYSQL_CONFIG['host']}"
    )


# ============================================================
# DASHBOARD
# ============================================================

if menu == "🏠 Dashboard":

    st.title("🏠 Dashboard")

    st.markdown(
        "## Xin chào 👋 Chào mừng đến với **TourMate**"
    )

    st.caption(
        "Hệ thống quản lý công việc dành cho hướng dẫn viên du lịch."
    )

    today = date.today()

    # --------------------------------------------------------
    # METRICS
    # --------------------------------------------------------

    tour_today_row = query_one(
        """
        SELECT COUNT(*) AS total
        FROM tours
        WHERE start_date <= %s
          AND end_date >= %s
          AND COALESCE(status, '') != 'Cancelled'
        """,
        (today, today)
    )

    tour_today = (
        tour_today_row["total"]
        if tour_today_row
        else 0
    )

    guests_today_row = query_one(
        """
        SELECT COUNT(*) AS total
        FROM guests g
        INNER JOIN tours t
            ON g.tour_id = t.id
        WHERE t.start_date <= %s
          AND t.end_date >= %s
          AND COALESCE(t.status, '') != 'Cancelled'
        """,
        (today, today)
    )

    guests_today = (
        guests_today_row["total"]
        if guests_today_row
        else 0
    )

    tasks_today_row = query_one(
        """
        SELECT COUNT(*) AS total
        FROM tasks
        WHERE due_date = %s
        """,
        (today,)
    )

    tasks_today = (
        tasks_today_row["total"]
        if tasks_today_row
        else 0
    )

    open_incidents_row = query_one(
        """
        SELECT COUNT(*) AS total
        FROM incidents
        WHERE COALESCE(status, 'Open') != 'Resolved'
        """
    )

    open_incidents = (
        open_incidents_row["total"]
        if open_incidents_row
        else 0
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "📅 Tour hôm nay",
        tour_today
    )

    c2.metric(
        "👥 Khách hôm nay",
        guests_today
    )

    c3.metric(
        "✅ Việc hôm nay",
        tasks_today
    )

    c4.metric(
        "🚨 Sự cố",
        open_incidents
    )

    st.divider()

    # --------------------------------------------------------
    # TODAY TOUR
    # --------------------------------------------------------

    st.subheader(
        "📅 Công việc hôm nay"
    )

    today_tours = get_today_tours()

    if not today_tours:

        st.info(
            "🎉 Hôm nay chưa có tour nào."
        )

    else:

        for tour in today_tours:

            with st.container(border=True):

                col1, col2, col3 = st.columns(
                    [2.2, 2, 1]
                )

                with col1:

                    st.markdown(
                        f"### 🚌 {tour['name']}"
                    )

                    st.write(
                        f"**Mã tour:** "
                        f"{tour['code']}"
                    )

                    st.write(
                        f"👨‍✈️ HDV: "
                        f"{tour['guide_name'] or 'Chưa phân công'}"
                    )

                with col2:

                    st.write(
                        f"🕐 **Giờ đón:** "
                        f"{tour['start_time'] or '--'}"
                    )

                    st.write(
                        f"📍 **Điểm đón:** "
                        f"{tour['pickup_location'] or '--'}"
                    )

                    st.write(
                        f"🏨 **Khách sạn:** "
                        f"{tour['hotel'] or '--'}"
                    )

                    st.write(
                        f"🚌 **Xe:** "
                        f"{tour['vehicle'] or '--'}"
                    )

                with col3:

                    st.metric(
                        "👥 Khách",
                        tour["total_guests"] or 0
                    )

                    st.write(
                        status_badge(
                            tour["status"]
                        )
                    )

    st.divider()

    # --------------------------------------------------------
    # TODAY CHECKLIST
    # --------------------------------------------------------

    st.subheader(
        "✅ Checklist hôm nay"
    )

    tasks_today_data = query(
        """
        SELECT
            t.*,
            tr.code AS tour_code
        FROM tasks t
        LEFT JOIN tours tr
            ON t.tour_id = tr.id
        WHERE t.due_date = %s
        ORDER BY
            t.done ASC,
            t.due_time ASC
        """,
        (today,)
    )

    if not tasks_today_data:

        st.info(
            "Hôm nay không có checklist."
        )

    else:

        for task in tasks_today_data:

            label = task["task_name"]

            if task["tour_code"]:

                label += (
                    f" — {task['tour_code']}"
                )

            checked = st.checkbox(
                label,
                value=bool(task["done"]),
                key=f"dashboard_task_{task['id']}"
            )

            if checked != bool(task["done"]):

                execute(
                    """
                    UPDATE tasks
                    SET done=%s
                    WHERE id=%s
                    """,
                    (
                        1 if checked else 0,
                        task["id"]
                    )
                )

                st.rerun()


# ============================================================
# TOUR CALENDAR
# ============================================================

elif menu == "📅 Lịch tour":

    st.title("📅 Lịch tour")

    c1, c2 = st.columns(2)

    with c1:

        selected_month = st.date_input(
            "Chọn tháng",
            value=date.today().replace(day=1)
        )

    with c2:

        guide_list = query(
            """
            SELECT id, name
            FROM guides
            ORDER BY name
            """
        )

        guide_options = {
            "Tất cả": None
        }

        for guide in guide_list:

            guide_options[
                guide["name"]
            ] = guide["id"]

        guide_filter = st.selectbox(
            "Lọc hướng dẫn viên",
            list(guide_options.keys())
        )

    first_day = selected_month.replace(
        day=1
    )

    if first_day.month == 12:

        next_month = date(
            first_day.year + 1,
            1,
            1
        )

    else:

        next_month = date(
            first_day.year,
            first_day.month + 1,
            1
        )

    sql = """
        SELECT
            t.code AS `Mã tour`,
            t.name AS `Tên tour`,
            t.start_date AS `Ngày bắt đầu`,
            t.end_date AS `Ngày kết thúc`,
            t.start_time AS `Giờ đón`,
            t.pickup_location AS `Điểm đón`,
            t.hotel AS `Khách sạn`,
            t.total_guests AS `Số khách`,
            t.status AS `Trạng thái`,
            g.name AS `Hướng dẫn viên`
        FROM tours t
        LEFT JOIN guides g
            ON t.guide_id = g.id
        WHERE t.start_date < %s
          AND t.end_date >= %s
    """

    params = [
        next_month,
        first_day
    ]

    if guide_filter != "Tất cả":

        sql += """
            AND t.guide_id = %s
        """

        params.append(
            guide_options[guide_filter]
        )

    sql += """
        ORDER BY
            t.start_date ASC,
            t.start_time ASC
    """

    df = query_df(
        sql,
        tuple(params)
    )

    if df.empty:

        st.info(
            "📭 Chưa có tour trong tháng này."
        )

    else:

        df["Ngày bắt đầu"] = df[
            "Ngày bắt đầu"
        ].apply(format_date)

        df["Ngày kết thúc"] = df[
            "Ngày kết thúc"
        ].apply(format_date)

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# TOUR MANAGEMENT
# ============================================================

elif menu == "🚌 Quản lý tour":

    st.title("🚌 Quản lý tour")

    tab1, tab2 = st.tabs(
        [
            "📋 Danh sách tour",
            "➕ Tạo tour mới"
        ]
    )

    # ========================================================
    # TOUR LIST
    # ========================================================

    with tab1:

        tours = query(
            """
            SELECT
                t.*,
                g.name AS guide_name
            FROM tours t
            LEFT JOIN guides g
                ON t.guide_id = g.id
            ORDER BY
                t.start_date DESC,
                t.id DESC
            """
        )

        if not tours:

            st.info(
                "Chưa có tour."
            )

        else:

            for tour in tours:

                with st.expander(
                    f"🚌 {tour['code']} — "
                    f"{tour['name']}"
                ):

                    c1, c2, c3 = st.columns(3)

                    c1.write(
                        f"📅 "
                        f"{format_date(tour['start_date'])}"
                        f" → "
                        f"{format_date(tour['end_date'])}"
                    )

                    c2.write(
                        f"👨‍✈️ HDV: "
                        f"{tour['guide_name'] or 'Chưa phân công'}"
                    )

                    c3.write(
                        f"👥 "
                        f"{tour['total_guests'] or 0} khách"
                    )

                    st.write(
                        f"🕐 Giờ đón: "
                        f"{tour['start_time'] or '--'}"
                    )

                    st.write(
                        f"📍 Điểm đón: "
                        f"{tour['pickup_location'] or '--'}"
                    )

                    st.write(
                        f"🏨 Khách sạn: "
                        f"{tour['hotel'] or '--'}"
                    )

                    st.write(
                        f"🚌 Phương tiện: "
                        f"{tour['vehicle'] or '--'}"
                    )

                    st.write(
                        f"👨‍✈️ Tài xế: "
                        f"{tour['driver'] or '--'}"
                    )

                    st.write(
                        status_badge(
                            tour["status"]
                        )
                    )

                    if tour["notes"]:

                        st.info(
                            f"📝 {tour['notes']}"
                        )

                    st.divider()

                    if st.button(
                        "🗑️ Xóa tour",
                        key=f"delete_tour_{tour['id']}"
                    ):

                        try:

                            execute(
                                """
                                DELETE FROM tours
                                WHERE id=%s
                                """,
                                (tour["id"],)
                            )

                            st.success(
                                "Đã xóa tour."
                            )

                            st.rerun()

                        except Exception as e:

                            st.error(
                                str(e)
                            )

    # ========================================================
    # CREATE TOUR
    # ========================================================

    with tab2:

        st.subheader(
            "➕ Tạo tour mới"
        )

        guides = query(
            """
            SELECT id, name
            FROM guides
            WHERE status='Active'
            ORDER BY name
            """
        )

        guide_options = {
            "Chưa phân công": None
        }

        for guide in guides:

            guide_options[
                f"{guide['name']} — ID {guide['id']}"
            ] = guide["id"]

        with st.form(
            "create_tour_form",
            clear_on_submit=True
        ):

            c1, c2 = st.columns(2)

            with c1:

                code = st.text_input(
                    "Mã tour *",
                    placeholder="VD: VT-001"
                )

                name = st.text_input(
                    "Tên tour *",
                    placeholder="Vũng Tàu 1 ngày"
                )

                start_date = st.date_input(
                    "Ngày bắt đầu",
                    value=date.today()
                )

                start_time = st.time_input(
                    "Giờ bắt đầu",
                    value=time(8, 0)
                )

                pickup = st.text_input(
                    "Điểm đón"
                )

            with c2:

                end_date = st.date_input(
                    "Ngày kết thúc",
                    value=date.today()
                )

                guide_name = st.selectbox(
                    "Hướng dẫn viên",
                    list(guide_options.keys())
                )

                hotel = st.text_input(
                    "Khách sạn"
                )

                vehicle = st.text_input(
                    "Phương tiện"
                )

                driver = st.text_input(
                    "Tài xế"
                )

                total_guests = st.number_input(
                    "Số khách dự kiến",
                    min_value=0,
                    value=0,
                    step=1
                )

            status = st.selectbox(
                "Trạng thái",
                [
                    "Scheduled",
                    "Confirmed",
                    "Completed",
                    "Cancelled"
                ]
            )

            notes = st.text_area(
                "Ghi chú"
            )

            submitted = st.form_submit_button(
                "💾 LƯU TOUR",
                type="primary",
                use_container_width=True
            )

            if submitted:

                code_clean = code.strip()
                name_clean = name.strip()

                if not code_clean:

                    st.error(
                        "❌ Vui lòng nhập mã tour."
                    )

                elif not name_clean:

                    st.error(
                        "❌ Vui lòng nhập tên tour."
                    )

                elif end_date < start_date:

                    st.error(
                        "❌ Ngày kết thúc không thể "
                        "trước ngày bắt đầu."
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
                                %s,%s,%s,%s,%s,%s,
                                %s,%s,%s,%s,%s,%s,%s
                            )
                            """,
                            (
                                code_clean,
                                name_clean,
                                guide_options[
                                    guide_name
                                ],
                                start_date,
                                end_date,
                                start_time.strftime(
                                    "%H:%M"
                                ),
                                pickup.strip(),
                                hotel.strip(),
                                vehicle.strip(),
                                driver.strip(),
                                int(total_guests),
                                status,
                                notes.strip()
                            )
                        )

                        st.success(
                            "🎉 Tạo tour thành công!"
                        )

                        st.rerun()

                    except Exception as e:

                        st.error(
                            str(e)
                        )


# ============================================================
# ITINERARY
# ============================================================

elif menu == "🗺️ Lịch trình":

    st.title("🗺️ Lịch trình tour")

    tour_options = get_tour_options()

    if not tour_options:

        st.info(
            "Chưa có tour. Hãy tạo tour trước."
        )

    else:

        selected_tour_name = st.selectbox(
            "Chọn tour",
            list(tour_options.keys())
        )

        selected_tour_id = tour_options[
            selected_tour_name
        ]

        selected_tour = query_one(
            """
            SELECT *
            FROM tours
            WHERE id=%s
            """,
            (selected_tour_id,)
        )

        st.divider()

        if selected_tour:

            c1, c2, c3, c4 = st.columns(4)

            c1.metric(
                "Mã tour",
                selected_tour["code"]
            )

            c2.metric(
                "Khách",
                selected_tour["total_guests"]
            )

            c3.metric(
                "Bắt đầu",
                format_date(
                    selected_tour["start_date"]
                )
            )

            c4.metric(
                "Kết thúc",
                format_date(
                    selected_tour["end_date"]
                )
            )

        st.divider()

        itinerary = query(
            """
            SELECT *
            FROM itinerary
            WHERE tour_id=%s
            ORDER BY
                tour_date,
                time,
                id
            """,
            (selected_tour_id,)
        )

        st.subheader(
            "📍 Lịch trình hiện tại"
        )

        if not itinerary:

            st.info(
                "Tour này chưa có lịch trình."
            )

        else:

            for item in itinerary:

                with st.container(
                    border=True
                ):

                    c1, c2, c3 = st.columns(
                        [1.2, 2.5, 1]
                    )

                    with c1:

                        st.write(
                            f"📅 "
                            f"{format_date(item['tour_date'])}"
                        )

                    with c2:

                        st.markdown(
                            f"### 📍 {item['place']}"
                        )

                        if item["activity"]:

                            st.write(
                                item["activity"]
                            )

                    with c3:

                        st.write(
                            f"🕐 "
                            f"{item['time'] or '--'}"
                        )

                    if item["transport"]:

                        st.write(
                            f"🚌 Phương tiện: "
                            f"{item['transport']}"
                        )

                    if item["notes"]:

                        st.write(
                            f"📝 {item['notes']}"
                        )

                    if st.button(
                        "🗑️ Xóa điểm",
                        key=f"delete_itinerary_{item['id']}"
                    ):

                        execute(
                            """
                            DELETE FROM itinerary
                            WHERE id=%s
                            """,
                            (item["id"],)
                        )

                        st.rerun()

        st.divider()

        st.subheader(
            "➕ Thêm điểm vào lịch trình"
        )

        with st.form(
            "add_itinerary",
            clear_on_submit=True
        ):

            c1, c2 = st.columns(2)

            with c1:

                itinerary_date = st.date_input(
                    "Ngày",
                    value=selected_tour[
                        "start_date"
                    ]
                    or date.today()
                )

                itinerary_time = st.time_input(
                    "Giờ",
                    value=time(9, 0)
                )

                place = st.text_input(
                    "Điểm đến *"
                )

            with c2:

                activity = st.text_input(
                    "Hoạt động"
                )

                transport = st.text_input(
                    "Phương tiện"
                )

                notes = st.text_area(
                    "Ghi chú"
                )

            submit = st.form_submit_button(
                "➕ THÊM ĐIỂM",
                type="primary"
            )

            if submit:

                if not place.strip():

                    st.error(
                        "❌ Vui lòng nhập điểm đến."
                    )

                elif (
                    selected_tour["start_date"]
                    and
                    itinerary_date <
                    selected_tour["start_date"]
                ):

                    st.error(
                        "❌ Ngày lịch trình phải nằm "
                        "trong thời gian của tour."
                    )

                elif (
                    selected_tour["end_date"]
                    and
                    itinerary_date >
                    selected_tour["end_date"]
                ):

                    st.error(
                        "❌ Ngày lịch trình phải nằm "
                        "trong thời gian của tour."
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
                            selected_tour_id,
                            itinerary_date,
                            itinerary_time.strftime(
                                "%H:%M"
                            ),
                            place.strip(),
                            activity.strip(),
                            transport.strip(),
                            notes.strip()
                        )
                    )

                    st.success(
                        "Đã thêm lịch trình."
                    )

                    st.rerun()


# ============================================================
# GUESTS
# ============================================================

elif menu == "👥 Khách du lịch":

    st.title("👥 Khách du lịch")

    tour_options = get_tour_options()

    if not tour_options:

        st.info(
            "Chưa có tour."
        )

    else:

        selected = st.selectbox(
            "Chọn tour",
            list(tour_options.keys())
        )

        tour_id = tour_options[selected]

        st.divider()

        guests = query(
            """
            SELECT *
            FROM guests
            WHERE tour_id=%s
            ORDER BY full_name
            """,
            (tour_id,)
        )

        st.subheader(
            f"👥 Danh sách khách ({len(guests)})"
        )

        if guests:

            df = pd.DataFrame(guests)

            show_columns = [
                "full_name",
                "gender",
                "age",
                "nationality",
                "phone",
                "room_number",
                "attendance",
                "special_request"
            ]

            show_columns = [
                c for c in show_columns
                if c in df.columns
            ]

            st.dataframe(
                df[show_columns],
                use_container_width=True,
                hide_index=True
            )

            st.subheader(
                "📋 Điểm danh"
            )

            status_options = [
                "Chưa điểm danh",
                "Có mặt",
                "Vắng",
                "Đã xác nhận"
            ]

            for guest in guests:

                current = guest["attendance"]

                if current not in status_options:

                    current = "Chưa điểm danh"

                c1, c2 = st.columns(
                    [3, 1]
                )

                with c1:

                    st.write(
                        f"**{guest['full_name']}**"
                    )

                with c2:

                    new_status = st.selectbox(
                        "Trạng thái",
                        status_options,
                        index=status_options.index(
                            current
                        ),
                        key=f"attendance_{guest['id']}",
                        label_visibility="collapsed"
                    )

                if new_status != guest["attendance"]:

                    execute(
                        """
                        UPDATE guests
                        SET attendance=%s
                        WHERE id=%s
                        """,
                        (
                            new_status,
                            guest["id"]
                        )
                    )

                    st.rerun()

        else:

            st.info(
                "Chưa có khách trong tour này."
            )

        st.divider()

        st.subheader(
            "➕ Thêm khách"
        )

        with st.form(
            "add_guest",
            clear_on_submit=True
        ):

            c1, c2 = st.columns(2)

            with c1:

                full_name = st.text_input(
                    "Họ tên *"
                )

                gender = st.selectbox(
                    "Giới tính",
                    [
                        "Không xác định",
                        "Nam",
                        "Nữ"
                    ]
                )

                age = st.number_input(
                    "Tuổi",
                    min_value=0,
                    max_value=120,
                    value=0
                )

                nationality = st.text_input(
                    "Quốc tịch"
                )

            with c2:

                phone = st.text_input(
                    "Số điện thoại"
                )

                room_number = st.text_input(
                    "Số phòng"
                )

                special_request = st.text_area(
                    "Yêu cầu đặc biệt"
                )

                guest_notes = st.text_area(
                    "Ghi chú"
                )

            submit = st.form_submit_button(
                "➕ THÊM KHÁCH",
                type="primary"
            )

            if submit:

                if not full_name.strip():

                    st.error(
                        "❌ Vui lòng nhập họ tên khách."
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
                            notes
                        )
                        VALUES
                        (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        """,
                        (
                            tour_id,
                            full_name.strip(),
                            gender,
                            int(age)
                            if age > 0
                            else None,
                            nationality.strip(),
                            phone.strip(),
                            room_number.strip(),
                            special_request.strip(),
                            guest_notes.strip()
                        )
                    )

                    execute(
                        """
                        UPDATE tours
                        SET total_guests = (
                            SELECT COUNT(*)
                            FROM guests
                            WHERE tour_id=%s
                        )
                        WHERE id=%s
                        """,
                        (
                            tour_id,
                            tour_id
                        )
                    )

                    st.success(
                        "Đã thêm khách."
                    )

                    st.rerun()


# ============================================================
# COMMENTARY LIBRARY
# ============================================================

elif menu == "🎤 Kho thuyết minh":

    st.title("🎤 Kho thuyết minh")

    search = st.text_input(
        "🔎 Tìm kiếm điểm đến",
        placeholder="VD: Vũng Tàu, Đà Lạt..."
    )

    if search.strip():

        search_value = (
            f"%{search.strip()}%"
        )

        places = query(
            """
            SELECT *
            FROM places
            WHERE name LIKE %s
               OR location LIKE %s
               OR category LIKE %s
            ORDER BY name
            """,
            (
                search_value,
                search_value,
                search_value
            )
        )

    else:

        places = query(
            """
            SELECT *
            FROM places
            ORDER BY name
            """
        )

    if not places:

        st.info(
            "Không tìm thấy điểm thuyết minh."
        )

    for place in places:

        with st.expander(
            f"📍 {place['name']} — "
            f"{place['location'] or ''}"
        ):

            if place["image_url"]:

                try:

                    st.image(
                        place["image_url"],
                        use_container_width=True
                    )

                except Exception:

                    st.warning(
                        "Không thể tải hình ảnh."
                    )

            c1, c2 = st.columns(2)

            with c1:

                st.markdown(
                    "### 🎤 Giới thiệu"
                )

                st.write(
                    place["introduction"]
                    or "Chưa có nội dung."
                )

                st.markdown(
                    "### 📚 Lịch sử"
                )

                st.write(
                    place["history"]
                    or "Chưa có nội dung."
                )

            with c2:

                st.markdown(
                    "### ⭐ Điểm nổi bật"
                )

                st.write(
                    place["highlights"]
                    or "Chưa có nội dung."
                )

                st.markdown(
                    "### 💡 Lưu ý cho HDV"
                )

                st.write(
                    place["tips"]
                    or "Chưa có nội dung."
                )

            if st.button(
                "🗑️ Xóa điểm",
                key=f"delete_place_{place['id']}"
            ):

                execute(
                    """
                    DELETE FROM places
                    WHERE id=%s
                    """,
                    (place["id"],)
                )

                st.success(
                    "Đã xóa điểm."
                )

                st.rerun()

    st.divider()

    st.subheader(
        "➕ Thêm điểm thuyết minh"
    )

    with st.form(
        "add_place",
        clear_on_submit=True
    ):

        c1, c2 = st.columns(2)

        with c1:

            name = st.text_input(
                "Tên điểm đến *"
            )

            location = st.text_input(
                "Địa điểm"
            )

            category = st.text_input(
                "Loại điểm"
            )

            image_url = st.text_input(
                "URL hình ảnh"
            )

        with c2:

            introduction = st.text_area(
                "Giới thiệu"
            )

            history = st.text_area(
                "Lịch sử"
            )

            highlights = st.text_area(
                "Điểm nổi bật"
            )

            tips = st.text_area(
                "Lưu ý cho hướng dẫn viên"
            )

        submit = st.form_submit_button(
            "💾 LƯU ĐIỂM ĐẾN",
            type="primary"
        )

        if submit:

            if not name.strip():

                st.error(
                    "❌ Vui lòng nhập tên điểm đến."
                )

            else:

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
                        tips,
                        image_url
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        name.strip(),
                        location.strip(),
                        category.strip(),
                        introduction.strip(),
                        history.strip(),
                        highlights.strip(),
                        tips.strip(),
                        image_url.strip()
                    )
                )

                st.success(
                    "Đã thêm điểm thuyết minh."
                )

                st.rerun()


# ============================================================
# CHECKLIST
# ============================================================

elif menu == "✅ Checklist":

    st.title(
        "✅ Checklist hướng dẫn viên"
    )

    tour_options = get_tour_options()

    filter_options = {
        "Tất cả tour": None,
        "Không gắn với tour": -1
    }

    for label, tour_id in tour_options.items():

        filter_options[label] = tour_id

    selected_filter = st.selectbox(
        "🔎 Lọc checklist theo tour",
        list(filter_options.keys())
    )

    selected_filter_id = filter_options[
        selected_filter
    ]

    if selected_filter_id is None:

        tasks = query(
            """
            SELECT
                t.*,
                tr.code AS tour_code,
                tr.name AS tour_name
            FROM tasks t
            LEFT JOIN tours tr
                ON t.tour_id = tr.id
            ORDER BY
                t.done ASC,
                t.due_date ASC,
                t.due_time ASC
            """
        )

    elif selected_filter_id == -1:

        tasks = query(
            """
            SELECT
                t.*,
                tr.code AS tour_code,
                tr.name AS tour_name
            FROM tasks t
            LEFT JOIN tours tr
                ON t.tour_id = tr.id
            WHERE t.tour_id IS NULL
            ORDER BY
                t.done ASC,
                t.due_date ASC,
                t.due_time ASC
            """
        )

    else:

        tasks = query(
            """
            SELECT
                t.*,
                tr.code AS tour_code,
                tr.name AS tour_name
            FROM tasks t
            LEFT JOIN tours tr
                ON t.tour_id = tr.id
            WHERE t.tour_id=%s
            ORDER BY
                t.done ASC,
                t.due_date ASC,
                t.due_time ASC
            """,
            (selected_filter_id,)
        )

    st.subheader(
        f"📋 Checklist ({len(tasks)})"
    )

    if not tasks:

        st.info(
            "Chưa có checklist."
        )

    else:

        for task in tasks:

            with st.container(
                border=True
            ):

                col1, col2, col3 = st.columns(
                    [5, 2, 1]
                )

                with col1:

                    label = task["task_name"]

                    if task["tour_code"]:

                        label += (
                            f" — {task['tour_code']}"
                        )

                    checked = st.checkbox(
                        label,
                        value=bool(task["done"]),
                        key=f"task_{task['id']}"
                    )

                    if checked != bool(
                        task["done"]
                    ):

                        execute(
                            """
                            UPDATE tasks
                            SET done=%s
                            WHERE id=%s
                            """,
                            (
                                1 if checked else 0,
                                task["id"]
                            )
                        )

                        st.rerun()

                with col2:

                    st.caption(
                        f"📅 "
                        f"{format_date(task['due_date'])}"
                    )

                    st.caption(
                        f"🕐 "
                        f"{task['due_time'] or '--'}"
                    )

                    st.caption(
                        f"🏷️ "
                        f"{task['task_type'] or '--'}"
                    )

                with col3:

                    if st.button(
                        "🗑️",
                        key=f"delete_task_{task['id']}"
                    ):

                        execute(
                            """
                            DELETE FROM tasks
                            WHERE id=%s
                            """,
                            (task["id"],)
                        )

                        st.rerun()

    st.divider()

    st.subheader(
        "➕ Thêm checklist"
    )

    add_tour_options = {
        "Không gắn với tour": None
    }

    add_tour_options.update(
        tour_options
    )

    with st.form(
        "add_task",
        clear_on_submit=True
    ):

        task_name = st.text_input(
            "Tên công việc *",
            placeholder="VD: Kiểm tra danh sách khách"
        )

        selected_tour_for_task = st.selectbox(
            "Gắn với tour",
            list(add_tour_options.keys())
        )

        c1, c2 = st.columns(2)

        with c1:

            task_type = st.selectbox(
                "Loại công việc",
                [
                    "Trước tour",
                    "Trong tour",
                    "Sau tour",
                    "Khác"
                ]
            )

            due_date = st.date_input(
                "Ngày thực hiện",
                value=date.today()
            )

        with c2:

            due_time = st.time_input(
                "Giờ thực hiện",
                value=time(7, 0)
            )

            assigned_to = st.text_input(
                "Người phụ trách"
            )

        task_notes = st.text_area(
            "Ghi chú"
        )

        submit = st.form_submit_button(
            "➕ THÊM CHECKLIST",
            type="primary"
        )

        if submit:

            if not task_name.strip():

                st.error(
                    "❌ Vui lòng nhập tên công việc."
                )

            else:

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
                        notes
                    )
                    VALUES
                    (%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        add_tour_options[
                            selected_tour_for_task
                        ],
                        task_name.strip(),
                        task_type,
                        due_date,
                        due_time.strftime(
                            "%H:%M"
                        ),
                        assigned_to.strip(),
                        task_notes.strip()
                    )
                )

                st.success(
                    "Đã thêm checklist."
                )

                st.rerun()


# ============================================================
# INCIDENTS
# ============================================================

elif menu == "🚨 Sự cố":

    st.title(
        "🚨 Quản lý sự cố"
    )

    tour_options = get_tour_options()

    incident_tour_options = {
        "Không gắn với tour": None
    }

    incident_tour_options.update(
        tour_options
    )

    selected_tour = st.selectbox(
        "Tour liên quan",
        list(incident_tour_options.keys())
    )

    selected_tour_id = incident_tour_options[
        selected_tour
    ]

    st.divider()

    incidents = query(
        """
        SELECT
            i.*,
            t.code AS tour_code,
            t.name AS tour_name
        FROM incidents i
        LEFT JOIN tours t
            ON i.tour_id=t.id
        ORDER BY
            i.incident_date DESC,
            i.id DESC
        """
    )

    st.subheader(
        f"📋 Danh sách sự cố ({len(incidents)})"
    )

    if not incidents:

        st.info(
            "Chưa có sự cố nào."
        )

    else:

        for incident in incidents:

            status_icon = {
                "Open": "🔴",
                "Processing": "🟡",
                "Resolved": "🟢"
            }.get(
                incident["status"],
                "⚪"
            )

            with st.expander(
                f"{status_icon} "
                f"{incident['title']}"
            ):

                c1, c2 = st.columns(2)

                with c1:

                    st.write(
                        f"📅 "
                        f"{format_date(incident['incident_date'])}"
                    )

                    st.write(
                        f"🕐 "
                        f"{incident['incident_time'] or '--'}"
                    )

                    st.write(
                        f"🏷️ "
                        f"{incident['type'] or '--'}"
                    )

                with c2:

                    st.write(
                        f"🚌 Tour: "
                        f"{incident['tour_code'] or '--'}"
                    )

                    st.write(
                        f"👤 Người báo cáo: "
                        f"{incident['created_by'] or '--'}"
                    )

                    st.write(
                        f"📌 "
                        f"{status_badge(incident['status'])}"
                    )

                st.markdown(
                    "#### 📋 Mô tả"
                )

                st.write(
                    incident["description"]
                    or "--"
                )

                st.markdown(
                    "#### 🔧 Cách xử lý"
                )

                st.write(
                    incident["solution"]
                    or "--"
                )

                status_options = [
                    "Open",
                    "Processing",
                    "Resolved"
                ]

                current_status = incident[
                    "status"
                ]

                if current_status not in status_options:

                    current_status = "Open"

                new_status = st.selectbox(
                    "Trạng thái",
                    status_options,
                    index=status_options.index(
                        current_status
                    ),
                    key=f"incident_status_{incident['id']}"
                )

                if new_status != incident["status"]:

                    execute(
                        """
                        UPDATE incidents
                        SET status=%s
                        WHERE id=%s
                        """,
                        (
                            new_status,
                            incident["id"]
                        )
                    )

                    st.rerun()

                if st.button(
                    "🗑️ Xóa sự cố",
                    key=f"delete_incident_{incident['id']}"
                ):

                    execute(
                        """
                        DELETE FROM incidents
                        WHERE id=%s
                        """,
                        (incident["id"],)
                    )

                    st.rerun()

    st.divider()

    st.subheader(
        "➕ Báo cáo sự cố"
    )

    with st.form(
        "add_incident",
        clear_on_submit=True
    ):

        title = st.text_input(
            "Tên sự cố *",
            placeholder="VD: Khách thất lạc hành lý"
        )

        c1, c2 = st.columns(2)

        with c1:

            incident_date = st.date_input(
                "Ngày",
                value=date.today()
            )

            incident_time = st.time_input(
                "Thời gian",
                value=datetime.now().time()
            )

        with c2:

            incident_type = st.selectbox(
                "Loại sự cố",
                [
                    "Khách hàng",
                    "Phương tiện",
                    "Khách sạn",
                    "Lịch trình",
                    "Thời tiết",
                    "Sức khỏe",
                    "Khác"
                ]
            )

            created_by = st.text_input(
                "Người báo cáo"
            )

        description = st.text_area(
            "Mô tả sự cố"
        )

        solution = st.text_area(
            "Cách xử lý"
        )

        submit = st.form_submit_button(
            "🚨 GỬI BÁO CÁO",
            type="primary"
        )

        if submit:

            if not title.strip():

                st.error(
                    "❌ Vui lòng nhập tên sự cố."
                )

            else:

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
                        created_by
                    )
                    VALUES
                    (%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        selected_tour_id,
                        incident_date,
                        incident_time.strftime(
                            "%H:%M"
                        ),
                        incident_type,
                        title.strip(),
                        description.strip(),
                        solution.strip(),
                        created_by.strip()
                    )
                )

                st.success(
                    "Đã ghi nhận sự cố."
                )

                st.rerun()


# ============================================================
# GUIDES
# ============================================================

elif menu == "👨‍✈️ Hướng dẫn viên":

    st.title(
        "👨‍✈️ Quản lý hướng dẫn viên"
    )

    guides = query(
        """
        SELECT *
        FROM guides
        ORDER BY name
        """
    )

    if guides:

        df = pd.DataFrame(guides)

        columns = [
            "id",
            "name",
            "phone",
            "email",
            "language",
            "experience_years",
            "status"
        ]

        columns = [
            c for c in columns
            if c in df.columns
        ]

        st.dataframe(
            df[columns],
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "Chưa có hướng dẫn viên."
        )

    st.divider()

    st.subheader(
        "➕ Thêm hướng dẫn viên"
    )

    with st.form(
        "add_guide",
        clear_on_submit=True
    ):

        c1, c2 = st.columns(2)

        with c1:

            name = st.text_input(
                "Họ tên *"
            )

            phone = st.text_input(
                "Số điện thoại"
            )

            email = st.text_input(
                "Email"
            )

        with c2:

            language = st.text_input(
                "Ngôn ngữ",
                placeholder="Vietnamese, English"
            )

            experience = st.number_input(
                "Số năm kinh nghiệm",
                min_value=0,
                value=0,
                step=1
            )

            status = st.selectbox(
                "Trạng thái",
                [
                    "Active",
                    "Inactive"
                ]
            )

        submit = st.form_submit_button(
            "➕ THÊM HDV",
            type="primary"
        )

        if submit:

            if not name.strip():

                st.error(
                    "❌ Vui lòng nhập họ tên."
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
                    VALUES (%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        name.strip(),
                        phone.strip(),
                        email.strip(),
                        language.strip(),
                        int(experience),
                        status
                    )
                )

                st.success(
                    "Đã thêm hướng dẫn viên."
                )

                st.rerun()


# ============================================================
# SETTINGS
# ============================================================

elif menu == "⚙️ Cài đặt dữ liệu":

    st.title(
        "⚙️ Cài đặt dữ liệu"
    )

    st.subheader(
        "🗄️ Thông tin database"
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Database",
        MYSQL_CONFIG["database"]
    )

    c2.metric(
        "User",
        MYSQL_CONFIG["user"]
    )

    c3.metric(
        "Port",
        MYSQL_CONFIG["port"]
    )

    st.success(
        "🟢 Kết nối Aiven MySQL đang hoạt động."
    )

    st.divider()

    # ========================================================
    # DATABASE STRUCTURE
    # ========================================================

    st.subheader(
        "🧱 Cấu trúc bảng"
    )

    selected_table = st.selectbox(
        "Chọn bảng để kiểm tra",
        [
            "guides",
            "tours",
            "itinerary",
            "guests",
            "tasks",
            "places",
            "incidents"
        ]
    )

    try:

        structure = query(
            f"""
            SHOW COLUMNS FROM `{selected_table}`
            """
        )

        structure_df = pd.DataFrame(
            structure
        )

        st.dataframe(
            structure_df,
            use_container_width=True,
            hide_index=True
        )

    except Exception as e:

        st.error(
            str(e)
        )

    st.divider()

    # ========================================================
    # STATISTICS
    # ========================================================

    st.subheader(
        "📊 Thống kê hệ thống"
    )

    tables = [
        ("👨‍✈️ Hướng dẫn viên", "guides"),
        ("🚌 Tour", "tours"),
        ("🗺️ Lịch trình", "itinerary"),
        ("👥 Khách", "guests"),
        ("✅ Checklist", "tasks"),
        ("🎤 Điểm thuyết minh", "places"),
        ("🚨 Sự cố", "incidents")
    ]

    cols = st.columns(4)

    for index, (label, table) in enumerate(tables):

        try:

            count = query_one(
                f"""
                SELECT COUNT(*) AS total
                FROM `{table}`
                """
            )["total"]

            cols[
                index % 4
            ].metric(
                label,
                count
            )

        except Exception as e:

            cols[
                index % 4
            ].error(
                f"{table}: {e}"
            )

    st.divider()

    # ========================================================
    # TEST MYSQL
    # ========================================================

    st.subheader(
        "🔄 Kiểm tra database"
    )

    if st.button(
        "🔌 TEST MYSQL",
        type="primary"
    ):

        ok, result = check_database()

        if ok:

            st.success(
                "🟢 MySQL hoạt động."
            )

            st.write(
                f"**MySQL Version:** "
                f"{result['version']}"
            )

            st.write(
                f"**Database:** "
                f"{result['database_name']}"
            )

            st.write(
                f"**Current User:** "
                f"{result['current_user']}"
            )

        else:

            st.error(
                "🔴 Không kết nối được MySQL."
            )

            st.code(
                result,
                language="text"
            )

    st.divider()

    # ========================================================
    # ARCHITECTURE
    # ========================================================

    st.subheader(
        "🧭 Kiến trúc TourMate"
    )

    st.markdown(
        """
        **TourMate** hiện quản lý:

        - 👨‍✈️ Hướng dẫn viên
        - 🚌 Tour
        - 🗺️ Lịch trình
        - 👥 Khách du lịch
        - ✅ Checklist công việc
        - 🎤 Kho thuyết minh
        - 🚨 Sự cố
        - 🗄️ Aiven MySQL
        """
    )

    st.divider()

    st.caption(
        "TourMate – Smart Tour Guide Management System"
    )

    st.caption(
        "Designed for Tourism & Travel Guide Operations."
    )
