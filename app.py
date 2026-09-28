import streamlit as st
import pymysql
import pandas as pd

from pymysql.cursors import DictCursor
from datetime import datetime, date, time
from calendar import monthrange


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="TourMate - Smart Tour Guide",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }

    .sub-title {
        color: #6b7280;
        margin-bottom: 1.5rem;
    }

    .metric-card {
        padding: 20px;
        border-radius: 15px;
        background: #ffffff;
        border: 1px solid #e5e7eb;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }

    .tour-card {
        padding: 18px;
        border-radius: 15px;
        background: #ffffff;
        border: 1px solid #e5e7eb;
        margin-bottom: 12px;
    }

    .small-text {
        color: #6b7280;
        font-size: 0.9rem;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# MYSQL CONFIG
# ============================================================

try:
    AIVEN_PASSWORD = st.secrets["mysql"]["password"]
except Exception:
    AIVEN_PASSWORD = ""


MYSQL_CONFIG = {
    "host": "mysql-19728385-npmaihuong-927f.b.aivencloud.com",
    "port": 27942,
    "user": "avnadmin",
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
# DATABASE CONNECTION
# ============================================================

def get_conn():
    if not MYSQL_CONFIG["password"]:
        raise RuntimeError(
            "Chưa tìm thấy password MySQL trong Streamlit Secrets."
        )

    try:
        return pymysql.connect(**MYSQL_CONFIG)

    except pymysql.MySQLError as e:
        code = e.args[0] if e.args else "UNKNOWN"
        message = e.args[1] if len(e.args) > 1 else str(e)

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
            cursor.execute(sql, params)

            try:
                last_id = cursor.lastrowid
            except Exception:
                last_id = None

        return last_id

    except pymysql.MySQLError as e:

        code = e.args[0] if e.args else "UNKNOWN"
        message = e.args[1] if len(e.args) > 1 else str(e)

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


# ============================================================
# QUERY ONE
# ============================================================

def query_one(sql, params=()):
    rows = query(sql, params)

    if rows:
        return rows[0]

    return None


# ============================================================
# QUERY DATAFRAME
# ============================================================

def query_df(sql, params=()):
    rows = query(sql, params)

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows)


# ============================================================
# DATABASE CHECK
# ============================================================

def check_database():

    conn = None

    try:

        conn = get_conn()

        with conn.cursor() as cursor:

            cursor.execute("SELECT 1 AS connection_ok")
            connection = cursor.fetchone()

            cursor.execute("SELECT VERSION() AS db_version")
            version = cursor.fetchone()

            cursor.execute("SELECT DATABASE() AS db_name")
            database = cursor.fetchone()

            cursor.execute("SELECT CURRENT_USER() AS db_user")
            user = cursor.fetchone()

        return {
            "ok": True,
            "connection": connection,
            "version": version,
            "database": database,
            "user": user,
        }

    except Exception as e:

        return {
            "ok": False,
            "error": str(e),
        }

    finally:

        if conn:
            conn.close()


# ============================================================
# TABLE CHECK
# ============================================================

def table_exists(table_name):

    row = query_one(
        """
        SELECT COUNT(*) AS total
        FROM information_schema.tables
        WHERE table_schema = DATABASE()
        AND table_name = %s
        """,
        (table_name,)
    )

    return bool(row and row["total"] > 0)


# ============================================================
# GET COLUMNS
# ============================================================

def get_columns(table_name):

    rows = query(
        """
        SELECT COLUMN_NAME
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
# SAFE ENSURE COLUMN
# ============================================================

def ensure_column(
    table_name,
    column_name,
    column_definition
):
    """
    Đảm bảo column tồn tại.

    Nếu column đã tồn tại:
        -> bỏ qua

    Nếu column chưa tồn tại:
        -> tạo column

    Nếu MySQL trả lỗi 1060 Duplicate column:
        -> bỏ qua

    Cách này giúp tránh app crash khi
    Streamlit chạy migration nhiều lần đồng thời.
    """

    try:

        columns = get_columns(table_name)

        if column_name in columns:
            return False

        execute(
            f"""
            ALTER TABLE `{table_name}`
            ADD COLUMN `{column_name}` {column_definition}
            """
        )

        return True

    except RuntimeError as e:

        error_text = str(e)

        if "MySQL Error 1060" in error_text:
            return False

        raise


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_db():

    # --------------------------------------------------------
    # GUIDES
    # --------------------------------------------------------

    execute(
        """
        CREATE TABLE IF NOT EXISTS guides (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(150) NOT NULL,
            phone VARCHAR(50),
            email VARCHAR(150),
            language VARCHAR(100),
            experience_years INT DEFAULT 0,
            status VARCHAR(50) DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # --------------------------------------------------------
    # TOURS
    # --------------------------------------------------------

    execute(
        """
        CREATE TABLE IF NOT EXISTS tours (
            id INT AUTO_INCREMENT PRIMARY KEY,
            code VARCHAR(50) UNIQUE,
            name VARCHAR(255),
            guide_id INT NULL,
            start_date DATE NULL,
            end_date DATE NULL,
            start_time VARCHAR(10) NULL,
            pickup_location VARCHAR(255),
            hotel VARCHAR(255),
            vehicle VARCHAR(255),
            driver VARCHAR(150),
            total_guests INT DEFAULT 0,
            status VARCHAR(50) DEFAULT 'Scheduled',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # --------------------------------------------------------
    # ITINERARY
    # --------------------------------------------------------

    execute(
        """
        CREATE TABLE IF NOT EXISTS itinerary (
            id INT AUTO_INCREMENT PRIMARY KEY,
            tour_id INT NULL,
            tour_date DATE NULL,
            time VARCHAR(20),
            place VARCHAR(255),
            activity VARCHAR(255),
            transport VARCHAR(255),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # --------------------------------------------------------
    # GUESTS
    # --------------------------------------------------------

    execute(
        """
        CREATE TABLE IF NOT EXISTS guests (
            id INT AUTO_INCREMENT PRIMARY KEY,
            tour_id INT NULL,
            full_name VARCHAR(255),
            gender VARCHAR(30),
            age INT NULL,
            nationality VARCHAR(100),
            phone VARCHAR(50),
            room_number VARCHAR(50),
            special_request TEXT,
            attendance VARCHAR(50) DEFAULT 'Pending',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # --------------------------------------------------------
    # TASKS
    # --------------------------------------------------------

    execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INT AUTO_INCREMENT PRIMARY KEY,
            tour_id INT NULL,
            task_name VARCHAR(255),
            task_type VARCHAR(100),
            due_date DATE NULL,
            due_time VARCHAR(20),
            assigned_to VARCHAR(150),
            done TINYINT DEFAULT 0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # --------------------------------------------------------
    # PLACES
    # --------------------------------------------------------

    execute(
        """
        CREATE TABLE IF NOT EXISTS places (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255),
            location VARCHAR(255),
            category VARCHAR(100),
            introduction TEXT,
            history TEXT,
            highlights TEXT,
            tips TEXT,
            image_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # --------------------------------------------------------
    # INCIDENTS
    # --------------------------------------------------------

    execute(
        """
        CREATE TABLE IF NOT EXISTS incidents (
            id INT AUTO_INCREMENT PRIMARY KEY,
            tour_id INT NULL,
            incident_date DATE NULL,
            incident_time VARCHAR(20),
            type VARCHAR(100),
            title VARCHAR(255),
            description TEXT,
            solution TEXT,
            status VARCHAR(50) DEFAULT 'Open',
            created_by VARCHAR(150),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # ========================================================
    # MIGRATION
    # ========================================================

    guide_columns = {
        "phone": "VARCHAR(50) NULL",
        "email": "VARCHAR(150) NULL",
        "language": "VARCHAR(100) NULL",
        "experience_years": "INT DEFAULT 0",
        "status": "VARCHAR(50) DEFAULT 'Active'",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    }

    for column, definition in guide_columns.items():
        ensure_column(
            "guides",
            column,
            definition
        )

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
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    }

    for column, definition in tour_columns.items():
        ensure_column(
            "tours",
            column,
            definition
        )

    itinerary_columns = {
        "tour_id": "INT NULL",
        "tour_date": "DATE NULL",
        "time": "VARCHAR(20) NULL",
        "place": "VARCHAR(255) NULL",
        "activity": "VARCHAR(255) NULL",
        "transport": "VARCHAR(255) NULL",
        "notes": "TEXT NULL",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    }

    for column, definition in itinerary_columns.items():
        ensure_column(
            "itinerary",
            column,
            definition
        )

    guest_columns = {
        "tour_id": "INT NULL",
        "full_name": "VARCHAR(255) NULL",
        "gender": "VARCHAR(30) NULL",
        "age": "INT NULL",
        "nationality": "VARCHAR(100) NULL",
        "phone": "VARCHAR(50) NULL",
        "room_number": "VARCHAR(50) NULL",
        "special_request": "TEXT NULL",
        "attendance": "VARCHAR(50) DEFAULT 'Pending'",
        "notes": "TEXT NULL",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    }

    for column, definition in guest_columns.items():
        ensure_column(
            "guests",
            column,
            definition
        )

    task_columns = {
        "tour_id": "INT NULL",
        "task_name": "VARCHAR(255) NULL",
        "task_type": "VARCHAR(100) NULL",
        "due_date": "DATE NULL",
        "due_time": "VARCHAR(20) NULL",
        "assigned_to": "VARCHAR(150) NULL",
        "done": "TINYINT DEFAULT 0",
        "notes": "TEXT NULL",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    }

    for column, definition in task_columns.items():
        ensure_column(
            "tasks",
            column,
            definition
        )

    place_columns = {
        "name": "VARCHAR(255) NULL",
        "location": "VARCHAR(255) NULL",
        "category": "VARCHAR(100) NULL",
        "introduction": "TEXT NULL",
        "history": "TEXT NULL",
        "highlights": "TEXT NULL",
        "tips": "TEXT NULL",
        "image_url": "TEXT NULL",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    }

    for column, definition in place_columns.items():
        ensure_column(
            "places",
            column,
            definition
        )

    incident_columns = {
        "tour_id": "INT NULL",
        "incident_date": "DATE NULL",
        "incident_time": "VARCHAR(20) NULL",
        "type": "VARCHAR(100) NULL",
        "title": "VARCHAR(255) NULL",
        "description": "TEXT NULL",
        "solution": "TEXT NULL",
        "status": "VARCHAR(50) DEFAULT 'Open'",
        "created_by": "VARCHAR(150) NULL",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    }

    for column, definition in incident_columns.items():
        ensure_column(
            "incidents",
            column,
            definition
        )

    # ========================================================
    # SEED DEMO GUIDE
    # ========================================================

    guide_count = query_one(
        """
        SELECT COUNT(*) AS total
        FROM guides
        """
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
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                "Nguyễn Trần Hương",
                "",
                "",
                "Vietnamese / English",
                2,
                "Active",
            )
        )

    # ========================================================
    # SEED PLACES
    # ========================================================

    place_count = query_one(
        """
        SELECT COUNT(*) AS total
        FROM places
        """
    )["total"]

    if place_count == 0:

        demo_places = [
            (
                "Tháp Tam Thắng",
                "Vũng Tàu",
                "Landmark",
                "Một điểm tham quan nổi bật tại Vũng Tàu.",
                "Công trình mang ý nghĩa biểu tượng và gắn với hình ảnh biển Vũng Tàu.",
                "Kiến trúc, vị trí, cảnh quan.",
                "Nên tham quan vào buổi sáng hoặc chiều để có ánh sáng đẹp.",
                "",
            ),
            (
                "Tượng Chúa Kitô Vua",
                "Vũng Tàu",
                "Religious",
                "Một trong những địa điểm tham quan nổi tiếng của Vũng Tàu.",
                "Công trình nằm trên Núi Nhỏ.",
                "Tượng Chúa, cảnh biển, đường lên núi.",
                "Nên chuẩn bị nước uống và giày thoải mái.",
                "",
            ),
            (
                "Bãi Sau",
                "Vũng Tàu",
                "Beach",
                "Bãi biển nổi tiếng phục vụ hoạt động nghỉ dưỡng và vui chơi.",
                "Một trong những khu vực biển du lịch chính của thành phố.",
                "Bãi biển rộng, cảnh hoàng hôn.",
                "Cẩn thận khi tắm biển và tuân thủ hướng dẫn an toàn.",
                "",
            ),
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
                VALUES
                (%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                place
            )


# ============================================================
# INITIAL DATABASE CHECK
# ============================================================

db_status = check_database()

if not db_status["ok"]:

    st.error("❌ Không thể kết nối MySQL.")

    st.code(
        db_status.get(
            "error",
            "Unknown database error"
        )
    )

    st.info(
        """
        Kiểm tra:

        1. Streamlit Secrets có đúng password Aiven chưa.
        2. Host / Port Aiven còn đúng không.
        3. Database là defaultdb.
        4. User là avnadmin.
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
        "❌ Không thể khởi tạo/cập nhật database."
    )

    st.code(str(e))

    st.stop()


# ============================================================
# HELPER
# ============================================================

def safe_date(value):

    if isinstance(value, date):
        return value

    if not value:
        return None

    try:
        return datetime.strptime(
            str(value),
            "%Y-%m-%d"
        ).date()

    except Exception:
        return None


def format_date(value):

    d = safe_date(value)

    if not d:
        return ""

    return d.strftime("%d/%m/%Y")


def status_badge(status):

    if status == "Completed":
        return "🟢 Completed"

    if status == "Cancelled":
        return "🔴 Cancelled"

    if status == "In Progress":
        return "🟡 In Progress"

    return "🔵 Scheduled"


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🧭 TourMate")

st.sidebar.caption(
    "Smart Tour Guide Management System"
)

menu = st.sidebar.radio(
    "MENU",
    [
        "🏠 Dashboard",
        "📅 Tour Calendar",
        "🚌 Tour Management",
        "🗺️ Itinerary",
        "👥 Guests",
        "📚 Commentary Library",
        "✅ Checklist",
        "🚨 Incidents",
        "🧑‍💼 Guides",
        "⚙️ Settings",
    ]
)

st.sidebar.divider()

st.sidebar.success(
    "🟢 MySQL Connected"
)


# ============================================================
# DASHBOARD
# ============================================================

if menu == "🏠 Dashboard":

    st.markdown(
        '<div class="main-title">🧭 TourMate Dashboard</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="sub-title">Smart Tour Guide Management System</div>',
        unsafe_allow_html=True
    )

    today = date.today()

    tour_total = query_one(
        """
        SELECT COUNT(*) AS total
        FROM tours
        WHERE status != 'Cancelled'
        """
    )["total"]

    guest_total = query_one(
        """
        SELECT COUNT(*) AS total
        FROM guests
        """
    )["total"]

    task_total = query_one(
        """
        SELECT COUNT(*) AS total
        FROM tasks
        WHERE done = 0
        """
    )["total"]

    incident_total = query_one(
        """
        SELECT COUNT(*) AS total
        FROM incidents
        WHERE status != 'Resolved'
        """
    )["total"]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "🚌 Tours",
        tour_total
    )

    c2.metric(
        "👥 Guests",
        guest_total
    )

    c3.metric(
        "✅ Pending Tasks",
        task_total
    )

    c4.metric(
        "🚨 Open Incidents",
        incident_total
    )

    st.divider()

    st.subheader(
        f"📅 Tours hôm nay — {today.strftime('%d/%m/%Y')}"
    )

    tours_today = query_df(
        """
        SELECT
            t.id,
            t.code AS `Mã tour`,
            t.name AS `Tên tour`,
            t.start_date AS `Ngày bắt đầu`,
            t.end_date AS `Ngày kết thúc`,
            t.start_time AS `Giờ`,
            t.pickup_location AS `Đón khách`,
            t.total_guests AS `Khách`,
            t.status AS `Trạng thái`,
            g.name AS `Hướng dẫn viên`
        FROM tours t
        LEFT JOIN guides g
            ON t.guide_id = g.id
        WHERE t.start_date <= %s
        AND t.end_date >= %s
        AND t.status != 'Cancelled'
        ORDER BY t.start_time
        """,
        (today, today)
    )

    if tours_today.empty:

        st.info(
            "Hôm nay chưa có tour nào."
        )

    else:

        st.dataframe(
            tours_today.drop(
                columns=["id"],
                errors="ignore"
            ),
            use_container_width=True,
            hide_index=True
        )

    st.divider()

    st.subheader("✅ Checklist hôm nay")

    tasks_today = query_df(
        """
        SELECT
            id,
            task_name AS `Công việc`,
            task_type AS `Loại`,
            due_time AS `Giờ`,
            assigned_to AS `Phụ trách`,
            done AS `Hoàn thành`
        FROM tasks
        WHERE due_date = %s
        ORDER BY due_time
        """,
        (today,)
    )

    if tasks_today.empty:

        st.info(
            "Không có checklist hôm nay."
        )

    else:

        tasks_display = tasks_today.copy()

        tasks_display["Hoàn thành"] = (
            tasks_display["Hoàn thành"]
            .apply(
                lambda x: "✅" if x else "⬜"
            )
        )

        st.dataframe(
            tasks_display.drop(
                columns=["id"],
                errors="ignore"
            ),
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# TOUR CALENDAR
# ============================================================

elif menu == "📅 Tour Calendar":

    st.title("📅 Tour Calendar")

    col1, col2 = st.columns(2)

    with col1:

        selected_year = st.number_input(
            "Năm",
            min_value=2020,
            max_value=2100,
            value=date.today().year
        )

    with col2:

        selected_month = st.selectbox(
            "Tháng",
            range(1, 13),
            index=date.today().month - 1
        )

    guides = query(
        """
        SELECT id, name
        FROM guides
        ORDER BY name
        """
    )

    guide_options = {
        "Tất cả": None
    }

    for guide in guides:
        guide_options[
            guide["name"]
        ] = guide["id"]

    guide_name = st.selectbox(
        "Hướng dẫn viên",
        list(guide_options.keys())
    )

    guide_id = guide_options[guide_name]

    first_day = date(
        selected_year,
        selected_month,
        1
    )

    last_day = date(
        selected_year,
        selected_month,
        monthrange(
            selected_year,
            selected_month
        )[1]
    )

    if guide_id:

        calendar_tours = query_df(
            """
            SELECT
                t.code AS `Mã`,
                t.name AS `Tour`,
                t.start_date AS `Bắt đầu`,
                t.end_date AS `Kết thúc`,
                t.start_time AS `Giờ`,
                t.pickup_location AS `Điểm đón`,
                t.total_guests AS `Khách`,
                t.status AS `Trạng thái`
            FROM tours t
            WHERE t.guide_id = %s
            AND t.start_date <= %s
            AND t.end_date >= %s
            ORDER BY t.start_date
            """,
            (
                guide_id,
                last_day,
                first_day
            )
        )

    else:

        calendar_tours = query_df(
            """
            SELECT
                t.code AS `Mã`,
                t.name AS `Tour`,
                t.start_date AS `Bắt đầu`,
                t.end_date AS `Kết thúc`,
                t.start_time AS `Giờ`,
                t.pickup_location AS `Điểm đón`,
                t.total_guests AS `Khách`,
                t.status AS `Trạng thái`
            FROM tours t
            WHERE t.start_date <= %s
            AND t.end_date >= %s
            ORDER BY t.start_date
            """,
            (
                last_day,
                first_day
            )
        )

    if calendar_tours.empty:

        st.info(
            "Không có tour trong khoảng thời gian này."
        )

    else:

        st.dataframe(
            calendar_tours,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# TOUR MANAGEMENT
# ============================================================

elif menu == "🚌 Tour Management":

    st.title("🚌 Tour Management")

    tab1, tab2 = st.tabs(
        [
            "📋 Danh sách tour",
            "➕ Tạo tour"
        ]
    )

    with tab1:

        tours = query_df(
            """
            SELECT
                t.id,
                t.code AS `Mã tour`,
                t.name AS `Tên tour`,
                t.start_date AS `Bắt đầu`,
                t.end_date AS `Kết thúc`,
                t.start_time AS `Giờ`,
                t.pickup_location AS `Đón khách`,
                t.hotel AS `Khách sạn`,
                t.vehicle AS `Phương tiện`,
                t.driver AS `Tài xế`,
                t.total_guests AS `Khách`,
                t.status AS `Trạng thái`,
                g.name AS `Hướng dẫn viên`
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
                tours.drop(
                    columns=["id"],
                    errors="ignore"
                ),
                use_container_width=True,
                hide_index=True
            )

            tour_map = {
                f"{row['Mã tour']} - {row['Tên tour']}":
                row["id"]
                for _, row in tours.iterrows()
            }

            selected_tour = st.selectbox(
                "Chọn tour để xóa",
                list(tour_map.keys())
            )

            if st.button(
                "🗑️ Xóa tour",
                type="secondary"
            ):

                tour_id = tour_map[selected_tour]

                execute(
                    "DELETE FROM itinerary WHERE tour_id = %s",
                    (tour_id,)
                )

                execute(
                    "DELETE FROM guests WHERE tour_id = %s",
                    (tour_id,)
                )

                execute(
                    "DELETE FROM tasks WHERE tour_id = %s",
                    (tour_id,)
                )

                execute(
                    "DELETE FROM incidents WHERE tour_id = %s",
                    (tour_id,)
                )

                execute(
                    "DELETE FROM tours WHERE id = %s",
                    (tour_id,)
                )

                st.success(
                    "Đã xóa tour."
                )

                st.rerun()

    with tab2:

        guides = query(
            """
            SELECT id, name
            FROM guides
            WHERE status = 'Active'
            ORDER BY name
            """
        )

        guide_options = {
            "Chưa phân công": None
        }

        for guide in guides:
            guide_options[
                guide["name"]
            ] = guide["id"]

        with st.form("create_tour_form"):

            code = st.text_input(
                "Mã tour",
                placeholder="TM-001"
            )

            name = st.text_input(
                "Tên tour",
                placeholder="Vũng Tàu 1 ngày"
            )

            c1, c2, c3 = st.columns(3)

            with c1:

                start_date = st.date_input(
                    "Ngày bắt đầu",
                    date.today()
                )

            with c2:

                end_date = st.date_input(
                    "Ngày kết thúc",
                    date.today()
                )

            with c3:

                start_time = st.text_input(
                    "Giờ bắt đầu",
                    "08:00"
                )

            pickup = st.text_input(
                "Điểm đón khách"
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

            guide_name = st.selectbox(
                "Hướng dẫn viên",
                list(guide_options.keys())
            )

            total_guests = st.number_input(
                "Số khách",
                min_value=0,
                value=0
            )

            status = st.selectbox(
                "Trạng thái",
                [
                    "Scheduled",
                    "In Progress",
                    "Completed",
                    "Cancelled"
                ]
            )

            notes = st.text_area(
                "Ghi chú"
            )

            submitted = st.form_submit_button(
                "💾 Tạo tour",
                use_container_width=True
            )

        if submitted:

            if not code.strip():

                st.error(
                    "Vui lòng nhập mã tour."
                )

            elif not name.strip():

                st.error(
                    "Vui lòng nhập tên tour."
                )

            elif end_date < start_date:

                st.error(
                    "Ngày kết thúc không được trước ngày bắt đầu."
                )

            else:

                guide_id = guide_options[
                    guide_name
                ]

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
                            code.strip(),
                            name.strip(),
                            guide_id,
                            start_date,
                            end_date,
                            start_time,
                            pickup,
                            hotel,
                            vehicle,
                            driver,
                            total_guests,
                            status,
                            notes,
                        )
                    )

                    st.success(
                        "✅ Tạo tour thành công."
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        "Không thể tạo tour."
                    )

                    st.code(str(e))


# ============================================================
# ITINERARY
# ============================================================

elif menu == "🗺️ Itinerary":

    st.title("🗺️ Itinerary")

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

        tour_options = {
            f"{t['code']} - {t['name']}":
            t["id"]
            for t in tours
        }

        selected = st.selectbox(
            "Chọn tour",
            list(tour_options.keys())
        )

        tour_id = tour_options[selected]

        itinerary = query_df(
            """
            SELECT
                id,
                tour_date AS `Ngày`,
                time AS `Giờ`,
                place AS `Địa điểm`,
                activity AS `Hoạt động`,
                transport AS `Phương tiện`,
                notes AS `Ghi chú`
            FROM itinerary
            WHERE tour_id = %s
            ORDER BY tour_date, time
            """,
            (tour_id,)
        )

        if itinerary.empty:

            st.info(
                "Tour chưa có lịch trình."
            )

        else:

            st.dataframe(
                itinerary.drop(
                    columns=["id"],
                    errors="ignore"
                ),
                use_container_width=True,
                hide_index=True
            )

            itinerary_options = {
                f"{row['Ngày']} - {row['Giờ']} - {row['Địa điểm']}":
                row["id"]
                for _, row in itinerary.iterrows()
            }

            delete_item = st.selectbox(
                "Chọn lịch trình để xóa",
                list(itinerary_options.keys())
            )

            if st.button(
                "🗑️ Xóa lịch trình"
            ):

                execute(
                    """
                    DELETE FROM itinerary
                    WHERE id = %s
                    """,
                    (
                        itinerary_options[
                            delete_item
                        ],
                    )
                )

                st.success(
                    "Đã xóa."
                )

                st.rerun()

        st.divider()

        st.subheader(
            "➕ Thêm lịch trình"
        )

        with st.form("add_itinerary"):

            c1, c2 = st.columns(2)

            with c1:

                tour_date = st.date_input(
                    "Ngày",
                    date.today()
                )

            with c2:

                itinerary_time = st.text_input(
                    "Giờ",
                    "08:00"
                )

            place = st.text_input(
                "Địa điểm"
            )

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
                "💾 Lưu lịch trình"
            )

        if submit:

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
                    tour_id,
                    tour_date,
                    itinerary_time,
                    place,
                    activity,
                    transport,
                    notes,
                )
            )

            st.success(
                "Đã thêm lịch trình."
            )

            st.rerun()


# ============================================================
# GUESTS
# ============================================================

elif menu == "👥 Guests":

    st.title("👥 Guest Management")

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

        tour_options = {
            f"{t['code']} - {t['name']}":
            t["id"]
            for t in tours
        }

        selected = st.selectbox(
            "Chọn tour",
            list(tour_options.keys())
        )

        tour_id = tour_options[selected]

        guests = query_df(
            """
            SELECT
                id,
                full_name AS `Họ tên`,
                gender AS `Giới tính`,
                age AS `Tuổi`,
                nationality AS `Quốc tịch`,
                phone AS `Điện thoại`,
                room_number AS `Phòng`,
                special_request AS `Yêu cầu đặc biệt`,
                attendance AS `Điểm danh`,
                notes AS `Ghi chú`
            FROM guests
            WHERE tour_id = %s
            ORDER BY full_name
            """,
            (tour_id,)
        )

        if guests.empty:

            st.info(
                "Chưa có khách."
            )

        else:

            st.dataframe(
                guests.drop(
                    columns=["id"],
                    errors="ignore"
                ),
                use_container_width=True,
                hide_index=True
            )

            guest_options = {
                row["Họ tên"]: row["id"]
                for _, row in guests.iterrows()
            }

            guest_name = st.selectbox(
                "Chọn khách",
                list(guest_options.keys())
            )

            attendance = st.selectbox(
                "Trạng thái điểm danh",
                [
                    "Pending",
                    "Present",
                    "Absent"
                ]
            )

            if st.button(
                "💾 Cập nhật điểm danh"
            ):

                execute(
                    """
                    UPDATE guests
                    SET attendance = %s
                    WHERE id = %s
                    """,
                    (
                        attendance,
                        guest_options[
                            guest_name
                        ],
                    )
                )

                st.success(
                    "Đã cập nhật."
                )

                st.rerun()

        st.divider()

        st.subheader(
            "➕ Thêm khách"
        )

        with st.form("add_guest"):

            full_name = st.text_input(
                "Họ tên *"
            )

            c1, c2, c3 = st.columns(3)

            with c1:

                gender = st.selectbox(
                    "Giới tính",
                    [
                        "Male",
                        "Female",
                        "Other"
                    ]
                )

            with c2:

                age = st.number_input(
                    "Tuổi",
                    min_value=0,
                    max_value=120,
                    value=18
                )

            with c3:

                nationality = st.text_input(
                    "Quốc tịch",
                    "Vietnam"
                )

            phone = st.text_input(
                "Điện thoại"
            )

            room_number = st.text_input(
                "Số phòng"
            )

            special_request = st.text_area(
                "Yêu cầu đặc biệt"
            )

            notes = st.text_area(
                "Ghi chú"
            )

            submit = st.form_submit_button(
                "💾 Thêm khách"
            )

        if submit:

            if not full_name.strip():

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
                        attendance,
                        notes
                    )
                    VALUES
                    (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        tour_id,
                        full_name,
                        gender,
                        age,
                        nationality,
                        phone,
                        room_number,
                        special_request,
                        "Pending",
                        notes,
                    )
                )

                guest_count = query_one(
                    """
                    SELECT COUNT(*) AS total
                    FROM guests
                    WHERE tour_id = %s
                    """,
                    (tour_id,)
                )["total"]

                execute(
                    """
                    UPDATE tours
                    SET total_guests = %s
                    WHERE id = %s
                    """,
                    (
                        guest_count,
                        tour_id,
                    )
                )

                st.success(
                    "Đã thêm khách."
                )

                st.rerun()


# ============================================================
# COMMENTARY LIBRARY
# ============================================================

elif menu == "📚 Commentary Library":

    st.title(
        "📚 Commentary Library"
    )

    search = st.text_input(
        "🔎 Tìm kiếm địa điểm"
    )

    if search:

        places = query_df(
            """
            SELECT
                id,
                name AS `Tên`,
                location AS `Địa điểm`,
                category AS `Danh mục`,
                introduction AS `Giới thiệu`
            FROM places
            WHERE name LIKE %s
            OR location LIKE %s
            OR category LIKE %s
            ORDER BY name
            """,
            (
                f"%{search}%",
                f"%{search}%",
                f"%{search}%",
            )
        )

    else:

        places = query_df(
            """
            SELECT
                id,
                name AS `Tên`,
                location AS `Địa điểm`,
                category AS `Danh mục`,
                introduction AS `Giới thiệu`
            FROM places
            ORDER BY name
            """
        )

    if places.empty:

        st.info(
            "Không tìm thấy địa điểm."
        )

    else:

        st.dataframe(
            places.drop(
                columns=["id"],
                errors="ignore"
            ),
            use_container_width=True,
            hide_index=True
        )

        place_options = {
            row["Tên"]: row["id"]
            for _, row in places.iterrows()
        }

        selected_place = st.selectbox(
            "Chọn địa điểm",
            list(place_options.keys())
        )

        place = query_one(
            """
            SELECT *
            FROM places
            WHERE id = %s
            """,
            (
                place_options[
                    selected_place
                ],
            )
        )

        if place:

            st.subheader(
                place["name"]
            )

            if place.get("image_url"):

                try:

                    st.image(
                        place["image_url"],
                        use_container_width=True
                    )

                except Exception:
                    pass

            c1, c2 = st.columns(2)

            with c1:

                st.markdown(
                    "### 📍 Địa điểm"
                )

                st.write(
                    place.get("location") or ""
                )

                st.markdown(
                    "### 📖 Giới thiệu"
                )

                st.write(
                    place.get("introduction") or ""
                )

                st.markdown(
                    "### 🏛️ Lịch sử"
                )

                st.write(
                    place.get("history") or ""
                )

            with c2:

                st.markdown(
                    "### ⭐ Điểm nổi bật"
                )

                st.write(
                    place.get("highlights") or ""
                )

                st.markdown(
                    "### 💡 Tips cho hướng dẫn viên"
                )

                st.write(
                    place.get("tips") or ""
                )

            if st.button(
                "🗑️ Xóa địa điểm"
            ):

                execute(
                    """
                    DELETE FROM places
                    WHERE id = %s
                    """,
                    (
                        place_options[
                            selected_place
                        ],
                    )
                )

                st.success(
                    "Đã xóa địa điểm."
                )

                st.rerun()

    st.divider()

    st.subheader(
        "➕ Thêm địa điểm"
    )

    with st.form("add_place"):

        place_name = st.text_input(
            "Tên địa điểm"
        )

        location = st.text_input(
            "Vị trí"
        )

        category = st.text_input(
            "Danh mục",
            "Landmark"
        )

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
            "Tips cho hướng dẫn viên"
        )

        image_url = st.text_input(
            "URL hình ảnh"
        )

        submit = st.form_submit_button(
            "💾 Thêm địa điểm"
        )

    if submit:

        if not place_name.strip():

            st.error(
                "Vui lòng nhập tên địa điểm."
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
                VALUES
                (%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    place_name,
                    location,
                    category,
                    introduction,
                    history,
                    highlights,
                    tips,
                    image_url,
                )
            )

            st.success(
                "Đã thêm địa điểm."
            )

            st.rerun()


# ============================================================
# CHECKLIST
# ============================================================

elif menu == "✅ Checklist":

    st.title(
        "✅ Tour Guide Checklist"
    )

    tours = query(
        """
        SELECT id, code, name
        FROM tours
        ORDER BY start_date DESC
        """
    )

    filter_options = {
        "Tất cả": None
    }

    for t in tours:

        filter_options[
            f"{t['code']} - {t['name']}"
        ] = t["id"]

    selected_filter = st.selectbox(
        "Lọc theo tour",
        list(filter_options.keys())
    )

    tour_id = filter_options[
        selected_filter
    ]

    if tour_id:

        tasks = query_df(
            """
            SELECT
                id,
                task_name AS `Công việc`,
                task_type AS `Loại`,
                due_date AS `Ngày`,
                due_time AS `Giờ`,
                assigned_to AS `Phụ trách`,
                done AS `Hoàn thành`,
                notes AS `Ghi chú`
            FROM tasks
            WHERE tour_id = %s
            ORDER BY due_date, due_time
            """,
            (tour_id,)
        )

    else:

        tasks = query_df(
            """
            SELECT
                id,
                task_name AS `Công việc`,
                task_type AS `Loại`,
                due_date AS `Ngày`,
                due_time AS `Giờ`,
                assigned_to AS `Phụ trách`,
                done AS `Hoàn thành`,
                notes AS `Ghi chú`
            FROM tasks
            ORDER BY due_date, due_time
            """
        )

    if tasks.empty:

        st.info(
            "Chưa có checklist."
        )

    else:

        display_tasks = tasks.copy()

        display_tasks["Hoàn thành"] = (
            display_tasks["Hoàn thành"]
            .apply(
                lambda x:
                "✅" if x else "⬜"
            )
        )

        st.dataframe(
            display_tasks.drop(
                columns=["id"],
                errors="ignore"
            ),
            use_container_width=True,
            hide_index=True
        )

        task_options = {
            row["Công việc"]:
            row["id"]
            for _, row in tasks.iterrows()
        }

        selected_task = st.selectbox(
            "Chọn công việc",
            list(task_options.keys())
        )

        if st.button(
            "🔄 Đổi trạng thái"
        ):

            current = query_one(
                """
                SELECT done
                FROM tasks
                WHERE id = %s
                """,
                (
                    task_options[
                        selected_task
                    ],
                )
            )

            new_value = 0 if current["done"] else 1

            execute(
                """
                UPDATE tasks
                SET done = %s
                WHERE id = %s
                """,
                (
                    new_value,
                    task_options[
                        selected_task
                    ],
                )
            )

            st.rerun()

        if st.button(
            "🗑️ Xóa công việc"
        ):

            execute(
                """
                DELETE FROM tasks
                WHERE id = %s
                """,
                (
                    task_options[
                        selected_task
                    ],
                )
            )

            st.rerun()

    st.divider()

    st.subheader(
        "➕ Thêm checklist"
    )

    with st.form("add_task"):

        task_name = st.text_input(
            "Tên công việc"
        )

        task_type = st.text_input(
            "Loại công việc",
            "Before Tour"
        )

        c1, c2 = st.columns(2)

        with c1:

            due_date = st.date_input(
                "Ngày",
                date.today()
            )

        with c2:

            due_time = st.text_input(
                "Giờ",
                "07:00"
            )

        assigned_to = st.text_input(
            "Người phụ trách"
        )

        notes = st.text_area(
            "Ghi chú"
        )

        submit = st.form_submit_button(
            "💾 Thêm checklist"
        )

    if submit:

        if not task_name.strip():

            st.error(
                "Vui lòng nhập tên công việc."
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
                    done,
                    notes
                )
                VALUES
                (%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    tour_id,
                    task_name,
                    task_type,
                    due_date,
                    due_time,
                    assigned_to,
                    0,
                    notes,
                )
            )

            st.success(
                "Đã thêm checklist."
            )

            st.rerun()


# ============================================================
# INCIDENTS
# ============================================================

elif menu == "🚨 Incidents":

    st.title(
        "🚨 Incident Management"
    )

    tours = query(
        """
        SELECT id, code, name
        FROM tours
        ORDER BY start_date DESC
        """
    )

    tour_filter = {
        "Tất cả": None
    }

    for t in tours:

        tour_filter[
            f"{t['code']} - {t['name']}"
        ] = t["id"]

    selected = st.selectbox(
        "Lọc theo tour",
        list(tour_filter.keys())
    )

    tour_id = tour_filter[selected]

    if tour_id:

        incidents = query_df(
            """
            SELECT
                i.id,
                i.incident_date AS `Ngày`,
                i.incident_time AS `Giờ`,
                i.type AS `Loại`,
                i.title AS `Tiêu đề`,
                i.description AS `Mô tả`,
                i.solution AS `Xử lý`,
                i.status AS `Trạng thái`,
                i.created_by AS `Người tạo`
            FROM incidents i
            WHERE i.tour_id = %s
            ORDER BY i.incident_date DESC
            """,
            (tour_id,)
        )

    else:

        incidents = query_df(
            """
            SELECT
                i.id,
                i.incident_date AS `Ngày`,
                i.incident_time AS `Giờ`,
                i.type AS `Loại`,
                i.title AS `Tiêu đề`,
                i.description AS `Mô tả`,
                i.solution AS `Xử lý`,
                i.status AS `Trạng thái`,
                i.created_by AS `Người tạo`
            FROM incidents i
            ORDER BY i.incident_date DESC
            """
        )

    if incidents.empty:

        st.info(
            "Chưa có sự cố."
        )

    else:

        st.dataframe(
            incidents.drop(
                columns=["id"],
                errors="ignore"
            ),
            use_container_width=True,
            hide_index=True
        )

        incident_options = {
            f"{row['Ngày']} - {row['Tiêu đề']}":
            row["id"]
            for _, row in incidents.iterrows()
        }

        selected_incident = st.selectbox(
            "Chọn sự cố",
            list(incident_options.keys())
        )

        new_status = st.selectbox(
            "Cập nhật trạng thái",
            [
                "Open",
                "Investigating",
                "Resolved"
            ]
        )

        c1, c2 = st.columns(2)

        with c1:

            if st.button(
                "💾 Cập nhật"
            ):

                execute(
                    """
                    UPDATE incidents
                    SET status = %s
                    WHERE id = %s
                    """,
                    (
                        new_status,
                        incident_options[
                            selected_incident
                        ],
                    )
                )

                st.success(
                    "Đã cập nhật."
                )

                st.rerun()

        with c2:

            if st.button(
                "🗑️ Xóa"
            ):

                execute(
                    """
                    DELETE FROM incidents
                    WHERE id = %s
                    """,
                    (
                        incident_options[
                            selected_incident
                        ],
                    )
                )

                st.success(
                    "Đã xóa."
                )

                st.rerun()

    st.divider()

    st.subheader(
        "➕ Ghi nhận sự cố"
    )

    with st.form("add_incident"):

        incident_date = st.date_input(
            "Ngày",
            date.today()
        )

        incident_time = st.text_input(
            "Giờ",
            "10:00"
        )

        incident_type = st.selectbox(
            "Loại sự cố",
            [
                "Guest",
                "Transport",
                "Hotel",
                "Weather",
                "Health",
                "Lost & Found",
                "Other"
            ]
        )

        title = st.text_input(
            "Tiêu đề"
        )

        description = st.text_area(
            "Mô tả sự cố"
        )

        solution = st.text_area(
            "Cách xử lý"
        )

        created_by = st.text_input(
            "Người tạo",
            "Tour Guide"
        )

        submit = st.form_submit_button(
            "🚨 Lưu sự cố"
        )

    if submit:

        if not title.strip():

            st.error(
                "Vui lòng nhập tiêu đề."
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
                    status,
                    created_by
                )
                VALUES
                (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    tour_id,
                    incident_date,
                    incident_time,
                    incident_type,
                    title,
                    description,
                    solution,
                    "Open",
                    created_by,
                )
            )

            st.success(
                "Đã ghi nhận sự cố."
            )

            st.rerun()


# ============================================================
# GUIDES
# ============================================================

elif menu == "🧑‍💼 Guides":

    st.title(
        "🧑‍💼 Tour Guides"
    )

    guides = query_df(
        """
        SELECT
            id,
            name AS `Họ tên`,
            phone AS `Điện thoại`,
            email AS `Email`,
            language AS `Ngôn ngữ`,
            experience_years AS `Kinh nghiệm`,
            status AS `Trạng thái`
        FROM guides
        ORDER BY name
        """
    )

    if guides.empty:

        st.info(
            "Chưa có hướng dẫn viên."
        )

    else:

        st.dataframe(
            guides.drop(
                columns=["id"],
                errors="ignore"
            ),
            use_container_width=True,
            hide_index=True
        )

    st.divider()

    st.subheader(
        "➕ Thêm hướng dẫn viên"
    )

    with st.form("add_guide"):

        name = st.text_input(
            "Họ tên"
        )

        phone = st.text_input(
            "Điện thoại"
        )

        email = st.text_input(
            "Email"
        )

        language = st.text_input(
            "Ngôn ngữ",
            "Vietnamese / English"
        )

        experience = st.number_input(
            "Số năm kinh nghiệm",
            min_value=0,
            value=0
        )

        status = st.selectbox(
            "Trạng thái",
            [
                "Active",
                "Inactive"
            ]
        )

        submit = st.form_submit_button(
            "💾 Thêm hướng dẫn viên"
        )

    if submit:

        if not name.strip():

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
                )
            )

            st.success(
                "Đã thêm hướng dẫn viên."
            )

            st.rerun()


# ============================================================
# SETTINGS
# ============================================================

elif menu == "⚙️ Settings":

    st.title(
        "⚙️ System Settings"
    )

    st.subheader(
        "🗄️ MySQL Connection"
    )

    status = check_database()

    if status["ok"]:

        st.success(
            "🟢 MySQL connection hoạt động."
        )

        c1, c2, c3 = st.columns(3)

        with c1:

            st.metric(
                "Database",
                status["database"]["db_name"]
            )

        with c2:

            st.metric(
                "MySQL",
                status["version"]["db_version"]
            )

        with c3:

            st.metric(
                "User",
                status["user"]["db_user"]
            )

    else:

        st.error(
            status["error"]
        )

    st.divider()

    st.subheader(
        "📊 Database Statistics"
    )

    tables = [
        "guides",
        "tours",
        "itinerary",
        "guests",
        "tasks",
        "places",
        "incidents",
    ]

    stats = []

    for table in tables:

        try:

            total = query_one(
                f"""
                SELECT COUNT(*) AS total
                FROM `{table}`
                """
            )["total"]

        except Exception:

            total = "Error"

        stats.append(
            {
                "Table": table,
                "Records": total,
            }
        )

    st.dataframe(
        pd.DataFrame(stats),
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    st.subheader(
        "🧱 Database Structure"
    )

    selected_table = st.selectbox(
        "Chọn table",
        tables
    )

    columns = query_df(
        """
        SELECT
            COLUMN_NAME AS `Column`,
            COLUMN_TYPE AS `Type`,
            IS_NULLABLE AS `Nullable`,
            COLUMN_KEY AS `Key`,
            COLUMN_DEFAULT AS `Default`,
            EXTRA AS `Extra`
        FROM information_schema.columns
        WHERE table_schema = DATABASE()
        AND table_name = %s
        ORDER BY ORDINAL_POSITION
        """,
        (
            selected_table,
        )
    )

    st.dataframe(
        columns,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    st.subheader(
        "🧪 Test MySQL"
    )

    if st.button(
        "🔄 Test connection"
    ):

        result = check_database()

        if result["ok"]:

            st.success(
                "✅ Kết nối MySQL thành công!"
            )

        else:

            st.error(
                result["error"]
            )

    st.divider()

    st.subheader(
        "🏗️ Architecture"
    )

    st.markdown(
        """
        **TourMate**

        `Streamlit`
        ↓
        `PyMySQL`
        ↓
        `Aiven MySQL`
        ↓
        `TourMate Database`

        Các module:

        - 🏠 Dashboard
        - 📅 Tour Calendar
        - 🚌 Tour Management
        - 🗺️ Itinerary
        - 👥 Guest Management
        - 📚 Commentary Library
        - ✅ Checklist
        - 🚨 Incident Management
        - 🧑‍💼 Tour Guides
        - ⚙️ Database Settings
        """
    )


# ============================================================
# FOOTER
# ============================================================

st.sidebar.divider()

st.sidebar.caption(
    "TourMate © 2026"
)

st.sidebar.caption(
    "Smart Tour Guide Management System"
)
