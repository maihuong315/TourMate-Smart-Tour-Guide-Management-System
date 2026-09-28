import streamlit as st
import pymysql
import pandas as pd

from datetime import date, datetime, time, timedelta
from pymysql.cursors import DictCursor


# ============================================================
# 1. CẤU HÌNH TRANG
# ============================================================

st.set_page_config(
    page_title="TourMate - Smart Tour Guide",
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
        background: #f6f8fb;
    }

    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        max-width: 1500px;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #172554 100%);
    }

    [data-testid="stSidebar"] * {
        color: white !important;
    }

    .hero {
        padding: 28px 30px;
        border-radius: 20px;
        background: linear-gradient(135deg, #0f766e, #2563eb);
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.15);
    }

    .hero h1 {
        margin: 0;
        font-size: 36px;
    }

    .hero p {
        margin-top: 8px;
        font-size: 16px;
        opacity: 0.9;
    }

    .metric-card {
        padding: 20px;
        border-radius: 16px;
        background: white;
        border: 1px solid #e5e7eb;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.05);
    }

    .metric-title {
        color: #64748b;
        font-size: 14px;
    }

    .metric-value {
        font-size: 30px;
        font-weight: 700;
        color: #0f172a;
        margin-top: 5px;
    }

    .section-title {
        font-size: 24px;
        font-weight: 700;
        color: #0f172a;
        margin-top: 20px;
        margin-bottom: 12px;
    }

    .tour-card {
        background: white;
        border-radius: 16px;
        padding: 18px;
        border: 1px solid #e5e7eb;
        margin-bottom: 12px;
    }

    .status-active {
        color: #166534;
        background: #dcfce7;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 600;
    }

    .status-pending {
        color: #92400e;
        background: #fef3c7;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 600;
    }

    .status-cancelled {
        color: #991b1b;
        background: #fee2e2;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 600;
    }

    .small-muted {
        color: #64748b;
        font-size: 13px;
    }

    div[data-testid="stMetric"] {
        background: white;
        padding: 15px;
        border-radius: 15px;
        border: 1px solid #e5e7eb;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 3. THÔNG TIN MYSQL AIVEN
# ============================================================

MYSQL_CONFIG = {
    "host": "mysql-19728385-npmaihuong-927f.b.aivencloud.com",
    "port": 27942,
    "user": "avnadmin",

    # DÁN MẬT KHẨU AIVEN CỦA EM VÀO ĐÂY
    "password": "YOUR_AIVEN_PASSWORD",

    "database": "defaultdb",
    "charset": "utf8mb4",
    "cursorclass": DictCursor,
    "autocommit": True,
    "connect_timeout": 15,
    "read_timeout": 30,
    "write_timeout": 30,
}


# ============================================================
# 4. KẾT NỐI DATABASE
# ============================================================

def get_conn():
    if not MYSQL_CONFIG["password"] or MYSQL_CONFIG["password"] == "YOUR_AIVEN_PASSWORD":
        raise RuntimeError(
            "Chưa nhập mật khẩu Aiven. "
            "Hãy sửa MYSQL_CONFIG['password'] trong app.py."
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
# 5. HIỂN THỊ LỖI DATABASE
# ============================================================

def safe_database_call(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)

    except Exception as e:
        st.error("❌ Có lỗi khi làm việc với MySQL")
        st.code(str(e))

        st.info(
            "Nếu lỗi liên quan đến database, hãy vào "
            "Cài đặt → Kiểm tra Database để xem chi tiết."
        )

        return None


# ============================================================
# 6. KIỂM TRA DATABASE
# ============================================================

def database_test():
    conn = None

    try:
        conn = get_conn()

        with conn.cursor() as cursor:
            cursor.execute("SELECT VERSION() AS version")
            version = cursor.fetchone()

            cursor.execute("SELECT DATABASE() AS database_name")
            database = cursor.fetchone()

            cursor.execute("SELECT CURRENT_USER() AS db_user")
            user = cursor.fetchone()

        return {
            "version": version["version"],
            "database": database["database_name"],
            "user": user["db_user"],
            "connected": True,
        }

    finally:
        if conn:
            conn.close()


# ============================================================
# 7. TẠO DATABASE
# ============================================================

def init_db():

    tables = [

        # ----------------------------------------------------
        # GUIDES
        # ----------------------------------------------------

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
        )
        """,

        # ----------------------------------------------------
        # TOURS
        # ----------------------------------------------------

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
            status VARCHAR(30) DEFAULT 'Scheduled',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,

        # ----------------------------------------------------
        # ITINERARY
        # ----------------------------------------------------

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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,

        # ----------------------------------------------------
        # GUESTS
        # ----------------------------------------------------

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
            attendance VARCHAR(30) DEFAULT 'Present',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,

        # ----------------------------------------------------
        # TASKS
        # ----------------------------------------------------

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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,

        # ----------------------------------------------------
        # PLACES
        # ----------------------------------------------------

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
        )
        """,

        # ----------------------------------------------------
        # INCIDENTS
        # ----------------------------------------------------

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
            status VARCHAR(30) DEFAULT 'Open',
            created_by VARCHAR(150),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
    ]

    for sql in tables:
        execute(sql)


# ============================================================
# 8. DỮ LIỆU DEMO
# ============================================================

def seed_demo_data():

    # --------------------------------------------------------
    # GUIDE
    # --------------------------------------------------------

    guide = query_one(
        """
        SELECT id
        FROM guides
        WHERE email = %s
        LIMIT 1
        """,
        ("huong.demo@tourmate.vn",),
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
                "huong.demo@tourmate.vn",
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
            ("huong.demo@tourmate.vn",),
        )

    guide_id = guide["id"]

    # --------------------------------------------------------
    # SECOND GUIDE
    # --------------------------------------------------------

    guide2 = query_one(
        """
        SELECT id
        FROM guides
        WHERE email = %s
        LIMIT 1
        """,
        ("guide2@tourmate.vn",),
    )

    if not guide2:

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
                "Trần Quốc Huy",
                "0912345678",
                "guide2@tourmate.vn",
                "Vietnamese, English, Chinese",
                7,
                "Active",
            ),
        )

    # --------------------------------------------------------
    # TOUR DEMO
    # --------------------------------------------------------

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
                "The Imperial Hotel Vũng Tàu",
                "29-seat tourist bus",
                "Lê Văn Nam",
                20,
                "Scheduled",
                "Tour demo cho hệ thống TourMate.",
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

    # --------------------------------------------------------
    # TOUR 2
    # --------------------------------------------------------

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
                "Terracotta Hotel & Resort",
                "45-seat tourist bus",
                "Phạm Văn Bình",
                32,
                "Scheduled",
                "Tour mẫu Đà Lạt.",
            ),
        )

        tour2 = query_one(
            """
            SELECT id
            FROM tours
            WHERE code = %s
            LIMIT 1
            """,
            ("TM-DL-002",),
        )

    tour2_id = tour2["id"]

    # --------------------------------------------------------
    # ITINERARY
    # --------------------------------------------------------

    itinerary_count = query_one(
        """
        SELECT COUNT(*) AS total
        FROM itinerary
        WHERE tour_id = %s
        """,
        (tour_id,),
    )["total"]

    if itinerary_count == 0:

        itinerary_data = [
            (
                tour_id,
                date.today(),
                time(8, 0),
                "Bãi Sau",
                "Đón khách và giới thiệu chương trình tour.",
                "Bus",
                "Kiểm tra đủ khách trước khi xuất phát.",
            ),
            (
                tour_id,
                date.today(),
                time(9, 30),
                "Tượng Chúa Kitô Vua",
                "Tham quan và chụp ảnh.",
                "Bus",
                "Nhắc khách mang nước uống.",
            ),
            (
                tour_id,
                date.today(),
                time(11, 30),
                "Nhà hàng Gành Hào",
                "Ăn trưa.",
                "Bus",
                "Kiểm tra số lượng suất ăn.",
            ),
            (
                tour_id,
                date.today(),
                time(14, 0),
                "Hải đăng Vũng Tàu",
                "Tham quan và thuyết minh.",
                "Bus",
                "Theo dõi thời gian đoàn.",
            ),
            (
                tour_id,
                date.today() + timedelta(days=1),
                time(8, 30),
                "Hồ Mây Park",
                "Vui chơi và tham quan.",
                "Bus",
                "Tập trung khách đúng giờ.",
            ),
        ]

        for item in itinerary_data:

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

    # --------------------------------------------------------
    # GUESTS
    # --------------------------------------------------------

    guest_count = query_one(
        """
        SELECT COUNT(*) AS total
        FROM guests
        WHERE tour_id = %s
        """,
        (tour_id,),
    )["total"]

    if guest_count == 0:

        guests = [
            ("Nguyễn Văn An", "Male", 31, "Vietnam", "0901111111", "101"),
            ("Trần Thị Lan", "Female", 28, "Vietnam", "0902222222", "102"),
            ("John Smith", "Male", 35, "United States", "0903333333", "103"),
            ("Emily Brown", "Female", 29, "United Kingdom", "0904444444", "104"),
            ("Sophie Martin", "Female", 32, "France", "0905555555", "105"),
            ("Lê Minh Tuấn", "Male", 25, "Vietnam", "0906666666", "106"),
        ]

        for guest in guests:

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
                    guest[0],
                    guest[1],
                    guest[2],
                    guest[3],
                    guest[4],
                    guest[5],
                    "Present",
                ),
            )

    # --------------------------------------------------------
    # TASKS
    # --------------------------------------------------------

    task_count = query_one(
        """
        SELECT COUNT(*) AS total
        FROM tasks
        WHERE tour_id = %s
        """,
        (tour_id,),
    )["total"]

    if task_count == 0:

        tasks = [
            (
                "Kiểm tra Arrival List",
                "Pre-tour",
                date.today(),
                time(6, 30),
                "Nguyễn Minh Anh",
                1,
                "Kiểm tra danh sách khách.",
            ),
            (
                "Chuẩn bị nước uống",
                "Preparation",
                date.today(),
                time(6, 45),
                "Nguyễn Minh Anh",
                1,
                "",
            ),
            (
                "Kiểm tra xe",
                "Transport",
                date.today(),
                time(7, 0),
                "Lê Văn Nam",
                1,
                "",
            ),
            (
                "Điểm danh khách",
                "Guest",
                date.today(),
                time(7, 30),
                "Nguyễn Minh Anh",
                0,
                "",
            ),
            (
                "Gửi feedback form",
                "Post-tour",
                date.today() + timedelta(days=2),
                time(18, 0),
                "Nguyễn Minh Anh",
                0,
                "",
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
                    done,
                    notes
                )
                VALUES
                (%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    tour_id,
                    task[0],
                    task[1],
                    task[2],
                    task[3],
                    task[4],
                    task[5],
                    task[6],
                ),
            )

    # --------------------------------------------------------
    # PLACES
    # --------------------------------------------------------

    places = [
        (
            "Tượng Chúa Kitô Vua",
            "Vũng Tàu",
            "Religious / Landmark",
            "Tượng Chúa Kitô Vua là một trong những biểu tượng nổi bật của Vũng Tàu.",
            "Công trình nằm trên Núi Nhỏ và là điểm tham quan nổi tiếng của thành phố.",
            "Tượng lớn, góc nhìn thành phố và biển, cảnh quan đẹp.",
            "Nên đi giày thoải mái và chuẩn bị nước uống.",
            "https://images.unsplash.com/photo-1500534623283-312aade485b7?w=1200",
        ),
        (
            "Hải đăng Vũng Tàu",
            "Núi Nhỏ, Vũng Tàu",
            "Landmark",
            "Hải đăng Vũng Tàu là địa điểm có tầm nhìn đẹp ra biển và thành phố.",
            "Ngọn hải đăng là một công trình hàng hải lâu đời của khu vực.",
            "Check-in, ngắm biển, chụp ảnh.",
            "Nên đến vào sáng sớm hoặc chiều mát.",
            "https://images.unsplash.com/photo-1498307833015-e7b400441eb8?w=1200",
        ),
        (
            "Bãi Sau",
            "Vũng Tàu",
            "Beach",
            "Bãi Sau là một trong những bãi biển nổi tiếng nhất tại Vũng Tàu.",
            "Khu vực phát triển mạnh về du lịch nghỉ dưỡng và dịch vụ biển.",
            "Tắm biển, đi dạo, ngắm bình minh.",
            "Theo dõi thời tiết và thủy triều.",
            "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1200",
        ),
        (
            "Hồ Mây Park",
            "Vũng Tàu",
            "Entertainment",
            "Khu du lịch Hồ Mây nằm trên Núi Lớn.",
            "Khu du lịch kết hợp thiên nhiên và các hoạt động vui chơi.",
            "Cáp treo, vui chơi, ngắm cảnh.",
            "Nên dành ít nhất nửa ngày.",
            "https://images.unsplash.com/photo-1513883049090-d0b7439799bf?w=1200",
        ),
    ]

    for place in places:

        exists = query_one(
            """
            SELECT id
            FROM places
            WHERE name = %s
            LIMIT 1
            """,
            (place[0],),
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
                    tips,
                    image_url
                )
                VALUES
                (%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                place,
            )

    # --------------------------------------------------------
    # INCIDENT
    # --------------------------------------------------------

    incident_exists = query_one(
        """
        SELECT id
        FROM incidents
        WHERE title = %s
        LIMIT 1
        """,
        ("Khách quên hành lý trên xe",),
    )

    if not incident_exists:

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
                "Một khách phát hiện thiếu túi xách sau khi xuống xe.",
                "Liên hệ tài xế kiểm tra xe và đã tìm thấy túi.",
                "Resolved",
                "Nguyễn Minh Anh",
            ),
        )


# ============================================================
# 9. KHỞI ĐỘNG DATABASE
# ============================================================

db_ready = False

try:

    database_test()
    init_db()
    seed_demo_data()

    db_ready = True

except Exception as e:

    st.error("❌ Không thể khởi động hệ thống database.")

    st.code(str(e))

    st.warning(
        "Kiểm tra lại Host, Port, User, Password Aiven "
        "và quyền truy cập MySQL."
    )

    st.stop()


# ============================================================
# 10. HEADER
# ============================================================

st.markdown(
    """
    <div class="hero">
        <h1>🧭 TourMate</h1>
        <p>
            Smart Tour Guide Management System —
            Hệ thống quản lý tour dành cho hướng dẫn viên du lịch
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 11. SIDEBAR
# ============================================================

st.sidebar.markdown(
    """
    <div style="text-align:center; padding:10px;">
        <div style="font-size:48px;">🧭</div>
        <h2>TourMate</h2>
        <p style="font-size:13px;">Smart Tour Guide System</p>
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

st.sidebar.success("🟢 MySQL: Connected")

st.sidebar.caption(
    f"Ngày: {date.today().strftime('%d/%m/%Y')}"
)


# ============================================================
# 12. DASHBOARD
# ============================================================

if menu == "📊 Dashboard":

    st.subheader("📊 Tổng quan hoạt động")

    today = date.today()

    tour_total = query_one(
        """
        SELECT COUNT(*) AS total
        FROM tours
        """
    )["total"]

    active_tours = query_one(
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

    guide_total = query_one(
        """
        SELECT COUNT(*) AS total
        FROM guides
        WHERE status = 'Active'
        """
    )["total"]

    open_incidents = query_one(
        """
        SELECT COUNT(*) AS total
        FROM incidents
        WHERE status = 'Open'
        """
    )["total"]

    pending_tasks = query_one(
        """
        SELECT COUNT(*) AS total
        FROM tasks
        WHERE done = 0
        """
    )["total"]

    c1, c2, c3, c4, c5, c6 = st.columns(6)

    c1.metric("🚌 Tổng tour", tour_total)
    c2.metric("📅 Tour hoạt động", active_tours)
    c3.metric("👥 Khách hàng", guest_total)
    c4.metric("🧑‍💼 HDV", guide_total)
    c5.metric("⚠️ Sự cố mở", open_incidents)
    c6.metric("⏳ Task chưa xong", pending_tasks)

    st.markdown("### 🚌 Tour hôm nay")

    tours_today = query_df(
        """
        SELECT
            t.code AS 'Mã tour',
            t.name AS 'Tên tour',
            t.start_date AS 'Ngày bắt đầu',
            t.end_date AS 'Ngày kết thúc',
            t.start_time AS 'Giờ xuất phát',
            t.pickup_location AS 'Điểm đón',
            t.total_guests AS 'Số khách',
            t.status AS 'Trạng thái',
            COALESCE(g.name, 'Chưa phân công') AS 'Hướng dẫn viên'
        FROM tours t
        LEFT JOIN guides g
            ON t.guide_id = g.id
        WHERE t.start_date <= %s
          AND t.end_date >= %s
          AND t.status != 'Cancelled'
        ORDER BY t.start_time
        """,
        (today, today),
    )

    if not tours_today.empty:

        st.dataframe(
            tours_today,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info("Hôm nay chưa có tour.")

    st.markdown("### 📅 Tour sắp tới")

    upcoming = query_df(
        """
        SELECT
            t.code AS 'Mã tour',
            t.name AS 'Tên tour',
            t.start_date AS 'Bắt đầu',
            t.end_date AS 'Kết thúc',
            t.total_guests AS 'Khách',
            COALESCE(g.name, 'Chưa phân công') AS 'HDV',
            t.status AS 'Trạng thái'
        FROM tours t
        LEFT JOIN guides g
            ON t.guide_id = g.id
        WHERE t.start_date >= %s
        ORDER BY t.start_date
        LIMIT 10
        """,
        (today,),
    )

    if not upcoming.empty:

        st.dataframe(
            upcoming,
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("### ✅ Tiến độ Checklist")

    task_stats = query_one(
        """
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN done = 1 THEN 1 ELSE 0 END) AS completed
        FROM tasks
        """
    )

    total_tasks = task_stats["total"] or 0
    completed_tasks = task_stats["completed"] or 0

    if total_tasks > 0:

        progress = completed_tasks / total_tasks

        st.progress(progress)

        st.write(
            f"Đã hoàn thành **{completed_tasks}/{total_tasks}** công việc "
            f"({progress:.0%})"
        )


# ============================================================
# 13. QUẢN LÝ TOUR
# ============================================================

elif menu == "🚌 Quản lý Tour":

    st.subheader("🚌 Quản lý Tour")

    tab1, tab2 = st.tabs(
        [
            "📋 Danh sách Tour",
            "➕ Tạo Tour",
        ]
    )

    with tab1:

        search = st.text_input(
            "🔎 Tìm kiếm tour",
            placeholder="Nhập mã tour hoặc tên tour...",
        )

        if search:

            tours = query_df(
                """
                SELECT
                    t.id,
                    t.code AS 'Mã tour',
                    t.name AS 'Tên tour',
                    t.start_date AS 'Bắt đầu',
                    t.end_date AS 'Kết thúc',
                    t.start_time AS 'Giờ',
                    t.pickup_location AS 'Điểm đón',
                    t.total_guests AS 'Khách',
                    t.status AS 'Trạng thái',
                    COALESCE(g.name, 'Chưa phân công') AS 'HDV'
                FROM tours t
                LEFT JOIN guides g
                    ON t.guide_id = g.id
                WHERE t.code LIKE %s
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
                    t.id,
                    t.code AS 'Mã tour',
                    t.name AS 'Tên tour',
                    t.start_date AS 'Bắt đầu',
                    t.end_date AS 'Kết thúc',
                    t.start_time AS 'Giờ',
                    t.pickup_location AS 'Điểm đón',
                    t.total_guests AS 'Khách',
                    t.status AS 'Trạng thái',
                    COALESCE(g.name, 'Chưa phân công') AS 'HDV'
                FROM tours t
                LEFT JOIN guides g
                    ON t.guide_id = g.id
                ORDER BY t.start_date DESC
                """
            )

        if not tours.empty:

            st.dataframe(
                tours.drop(columns=["id"]),
                use_container_width=True,
                hide_index=True,
            )

            st.markdown("### 🗑️ Xóa Tour")

            tour_options = query(
                """
                SELECT id, code, name
                FROM tours
                ORDER BY start_date DESC
                """
            )

            if tour_options:

                selected_delete = st.selectbox(
                    "Chọn tour muốn xóa",
                    tour_options,
                    format_func=lambda x:
                    f"{x['code']} - {x['name']}",
                )

                if st.button(
                    "🗑️ Xóa tour",
                    type="secondary",
                ):

                    tour_id = selected_delete["id"]

                    execute(
                        "DELETE FROM itinerary WHERE tour_id = %s",
                        (tour_id,),
                    )

                    execute(
                        "DELETE FROM guests WHERE tour_id = %s",
                        (tour_id,),
                    )

                    execute(
                        "DELETE FROM tasks WHERE tour_id = %s",
                        (tour_id,),
                    )

                    execute(
                        "DELETE FROM incidents WHERE tour_id = %s",
                        (tour_id,),
                    )

                    execute(
                        "DELETE FROM tours WHERE id = %s",
                        (tour_id,),
                    )

                    st.success("Đã xóa tour.")

                    st.rerun()

        else:

            st.info("Chưa có tour phù hợp.")

    with tab2:

        guides = query(
            """
            SELECT id, name
            FROM guides
            WHERE status = 'Active'
            ORDER BY name
            """
        )

        with st.form("create_tour_form"):

            col1, col2 = st.columns(2)

            with col1:

                code = st.text_input(
                    "Mã tour *",
                    placeholder="TM-VT-003",
                )

                name = st.text_input(
                    "Tên tour *",
                    placeholder="Vũng Tàu 3 ngày 2 đêm",
                )

                start_date = st.date_input(
                    "Ngày bắt đầu",
                    value=date.today(),
                )

                end_date = st.date_input(
                    "Ngày kết thúc",
                    value=date.today(),
                )

                start_time = st.time_input(
                    "Giờ khởi hành",
                    value=time(7, 30),
                )

            with col2:

                pickup = st.text_input(
                    "Điểm đón",
                    placeholder="Khách sạn...",
                )

                hotel = st.text_input(
                    "Khách sạn",
                )

                vehicle = st.text_input(
                    "Phương tiện",
                    value="Tourist bus",
                )

                driver = st.text_input(
                    "Tài xế",
                )

                total_guests = st.number_input(
                    "Số khách",
                    min_value=0,
                    max_value=1000,
                    value=20,
                )

                guide_choice = st.selectbox(
                    "Hướng dẫn viên",
                    guides,
                    format_func=lambda x: x["name"],
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

            notes = st.text_area("Ghi chú")

            submitted = st.form_submit_button(
                "💾 Tạo Tour",
                type="primary",
            )

            if submitted:

                if not code or not name:

                    st.error(
                        "Vui lòng nhập Mã tour và Tên tour."
                    )

                elif end_date < start_date:

                    st.error(
                        "Ngày kết thúc không thể trước ngày bắt đầu."
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
                            (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                            """,
                            (
                                code,
                                name,
                                guide_choice["id"],
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
                            ),
                        )

                        st.success(
                            f"Đã tạo tour {code} thành công!"
                        )

                        st.rerun()

                    except Exception as e:

                        st.error(
                            "Không thể tạo tour."
                        )

                        st.code(str(e))


# ============================================================
# 14. LỊCH TRÌNH
# ============================================================

elif menu == "🗺️ Lịch trình":

    st.subheader("🗺️ Lịch trình tour")

    tours = query(
        """
        SELECT id, code, name
        FROM tours
        ORDER BY start_date DESC
        """
    )

    if not tours:

        st.info("Chưa có tour.")

    else:

        selected_tour = st.selectbox(
            "Chọn tour",
            tours,
            format_func=lambda x:
            f"{x['code']} - {x['name']}",
        )

        itinerary = query_df(
            """
            SELECT
                id,
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
            (selected_tour["id"],),
        )

        if not itinerary.empty:

            st.dataframe(
                itinerary.drop(columns=["id"]),
                use_container_width=True,
                hide_index=True,
            )

        else:

            st.info("Tour chưa có lịch trình.")

        st.markdown("### ➕ Thêm điểm trong lịch trình")

        with st.form("add_itinerary"):

            c1, c2 = st.columns(2)

            with c1:

                itinerary_date = st.date_input(
                    "Ngày",
                    value=date.today(),
                )

                itinerary_time = st.time_input(
                    "Giờ",
                    value=time(8, 0),
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
                    value="Bus",
                )

                notes = st.text_area(
                    "Ghi chú"
                )

            submit = st.form_submit_button(
                "➕ Thêm vào lịch trình",
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
                            selected_tour["id"],
                            itinerary_date,
                            itinerary_time,
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
# 15. KHÁCH HÀNG
# ============================================================

elif menu == "👥 Khách hàng":

    st.subheader("👥 Quản lý khách hàng")

    tours = query(
        """
        SELECT id, code, name
        FROM tours
        ORDER BY start_date DESC
        """
    )

    if not tours:

        st.info("Chưa có tour.")

    else:

        selected_tour = st.selectbox(
            "Chọn tour",
            tours,
            format_func=lambda x:
            f"{x['code']} - {x['name']}",
        )

        guests = query_df(
            """
            SELECT
                id,
                full_name AS 'Họ tên',
                gender AS 'Giới tính',
                age AS 'Tuổi',
                nationality AS 'Quốc tịch',
                phone AS 'Điện thoại',
                room_number AS 'Phòng',
                attendance AS 'Điểm danh',
                special_request AS 'Yêu cầu đặc biệt'
            FROM guests
            WHERE tour_id = %s
            ORDER BY full_name
            """,
            (selected_tour["id"],),
        )

        st.metric(
            "Tổng số khách",
            len(guests),
        )

        if not guests.empty:

            st.dataframe(
                guests.drop(columns=["id"]),
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
                    min_value=0,
                    max_value=120,
                    value=25,
                )

                nationality = st.text_input(
                    "Quốc tịch",
                    value="Vietnam",
                )

            with c2:

                phone = st.text_input(
                    "Số điện thoại"
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
                            selected_tour["id"],
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
# 16. CHECKLIST
# ============================================================

elif menu == "✅ Checklist":

    st.subheader("✅ Checklist hướng dẫn viên")

    tours = query(
        """
        SELECT id, code, name
        FROM tours
        ORDER BY start_date DESC
        """
    )

    if not tours:

        st.info("Chưa có tour.")

    else:

        selected_tour = st.selectbox(
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
            (selected_tour["id"],),
        )

        if tasks:

            for task in tasks:

                checked = st.checkbox(
                    f"{'✅' if task['done'] else '⬜'} "
                    f"{task['task_name']} "
                    f"— {task['assigned_to'] or 'Chưa giao'}",
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

            st.info("Chưa có checklist.")

        st.markdown("### ➕ Thêm công việc")

        with st.form("add_task"):

            task_name = st.text_input(
                "Tên công việc *"
            )

            c1, c2 = st.columns(2)

            with c1:

                task_type = st.text_input(
                    "Loại công việc",
                    value="General",
                )

                due_date = st.date_input(
                    "Ngày thực hiện",
                    value=date.today(),
                )

            with c2:

                due_time = st.time_input(
                    "Giờ",
                    value=time(8, 0),
                )

                assigned_to = st.text_input(
                    "Người phụ trách"
                )

            notes = st.text_area(
                "Ghi chú"
            )

            submit = st.form_submit_button(
                "➕ Thêm task",
                type="primary",
            )

            if submit:

                if not task_name:

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
                            notes
                        )
                        VALUES
                        (%s,%s,%s,%s,%s,%s,%s)
                        """,
                        (
                            selected_tour["id"],
                            task_name,
                            task_type,
                            due_date,
                            due_time,
                            assigned_to,
                            notes,
                        ),
                    )

                    st.success(
                        "Đã thêm công việc."
                    )

                    st.rerun()


# ============================================================
# 17. ĐIỂM THAM QUAN
# ============================================================

elif menu == "📍 Điểm tham quan":

    st.subheader("📍 Thư viện điểm tham quan")

    search = st.text_input(
        "🔎 Tìm điểm tham quan",
        placeholder="Ví dụ: Vũng Tàu...",
    )

    if search:

        places_df = query_df(
            """
            SELECT *
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
            ),
        )

    else:

        places_df = query_df(
            """
            SELECT *
            FROM places
            ORDER BY name
            """
        )

    if places_df.empty:

        st.info("Chưa có điểm tham quan.")

    else:

        for _, place in places_df.iterrows():

            with st.container():

                c1, c2 = st.columns([1, 2])

                with c1:

                    if (
                        place["image_url"]
                        and str(place["image_url"]).strip()
                    ):

                        st.image(
                            place["image_url"],
                            use_container_width=True,
                        )

                with c2:

                    st.markdown(
                        f"### 📍 {place['name']}"
                    )

                    st.caption(
                        f"{place['location']} • "
                        f"{place['category']}"
                    )

                    st.write(
                        place["introduction"] or ""
                    )

                    with st.expander(
                        "Xem nội dung thuyết minh"
                    ):

                        st.markdown(
                            "**📖 Lịch sử**"
                        )

                        st.write(
                            place["history"] or ""
                        )

                        st.markdown(
                            "**⭐ Điểm nổi bật**"
                        )

                        st.write(
                            place["highlights"] or ""
                        )

                        st.markdown(
                            "**💡 Lưu ý cho HDV**"
                        )

                        st.write(
                            place["tips"] or ""
                        )

                st.divider()

    st.markdown("### ➕ Thêm điểm tham quan")

    with st.form("add_place"):

        c1, c2 = st.columns(2)

        with c1:

            name = st.text_input(
                "Tên địa điểm *"
            )

            location = st.text_input(
                "Vị trí"
            )

            category = st.text_input(
                "Loại địa điểm"
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
                "Lưu ý cho HDV"
            )

        submit = st.form_submit_button(
            "➕ Thêm địa điểm",
            type="primary",
        )

        if submit:

            if not name:

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
                        name,
                        location,
                        category,
                        introduction,
                        history,
                        highlights,
                        tips,
                        image_url,
                    ),
                )

                st.success(
                    "Đã thêm điểm tham quan."
                )

                st.rerun()


# ============================================================
# 18. THƯ VIỆN THUYẾT MINH
# ============================================================

elif menu == "🎤 Thư viện thuyết minh":

    st.subheader("🎤 Thư viện thuyết minh")

    places = query(
        """
        SELECT *
        FROM places
        ORDER BY name
        """
    )

    if not places:

        st.info(
            "Chưa có dữ liệu điểm tham quan."
        )

    else:

        selected_place = st.selectbox(
            "Chọn điểm tham quan",
            places,
            format_func=lambda x:
            f"{x['name']} - {x['location']}",
        )

        st.markdown(
            f"## 🎙️ {selected_place['name']}"
        )

        st.caption(
            selected_place["location"]
        )

        st.markdown("### 🎤 Nội dung giới thiệu")

        st.info(
            selected_place["introduction"]
            or "Chưa có nội dung."
        )

        col1, col2 = st.columns(2)

        with col1:

            st.markdown("### 📖 Lịch sử")

            st.write(
                selected_place["history"]
                or "Chưa có nội dung."
            )

        with col2:

            st.markdown("### ⭐ Điểm nổi bật")

            st.write(
                selected_place["highlights"]
                or "Chưa có nội dung."
            )

        st.markdown("### 💡 Lưu ý khi thuyết minh")

        st.warning(
            selected_place["tips"]
            or "Chưa có lưu ý."
        )

        st.markdown("### 🗣️ Gợi ý lời dẫn")

        st.code(
            f"""
Xin chào quý khách!

Ngay trước mắt chúng ta là
{selected_place['name']}.

{selected_place['introduction']}

Trong quá trình tham quan, quý khách
vui lòng đi theo đoàn và chú ý thời gian
tập trung theo hướng dẫn của HDV.

Chúc quý khách có một trải nghiệm thật
vui vẻ và đáng nhớ!
            """,
            language="text",
        )


# ============================================================
# 19. SỰ CỐ
# ============================================================

elif menu == "⚠️ Sự cố":

    st.subheader("⚠️ Quản lý sự cố")

    incidents = query_df(
        """
        SELECT
            i.id,
            i.incident_date AS 'Ngày',
            i.incident_time AS 'Giờ',
            i.type AS 'Loại',
            i.title AS 'Tiêu đề',
            i.description AS 'Mô tả',
            i.solution AS 'Xử lý',
            i.status AS 'Trạng thái',
            i.created_by AS 'Người tạo'
        FROM incidents i
        ORDER BY i.incident_date DESC, i.incident_time DESC
        """
    )

    if not incidents.empty:

        st.dataframe(
            incidents.drop(columns=["id"]),
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info("Chưa có sự cố.")

    st.markdown("### ➕ Ghi nhận sự cố")

    tours = query(
        """
        SELECT id, code, name
        FROM tours
        ORDER BY start_date DESC
        """
    )

    with st.form("add_incident"):

        selected_tour = st.selectbox(
            "Tour",
            tours,
            format_func=lambda x:
            f"{x['code']} - {x['name']}",
        )

        c1, c2 = st.columns(2)

        with c1:

            incident_date = st.date_input(
                "Ngày",
                value=date.today(),
            )

            incident_time = st.time_input(
                "Giờ",
                value=datetime.now().time().replace(
                    second=0,
                    microsecond=0,
                ),
            )

            incident_type = st.selectbox(
                "Loại sự cố",
                [
                    "Guest",
                    "Transport",
                    "Hotel",
                    "Lost & Found",
                    "Health",
                    "Weather",
                    "Other",
                ],
            )

        with c2:

            title = st.text_input(
                "Tiêu đề *"
            )

            status = st.selectbox(
                "Trạng thái",
                [
                    "Open",
                    "Investigating",
                    "Resolved",
                ],
            )

            created_by = st.text_input(
                "Người tạo",
                value="Tour Guide",
            )

        description = st.text_area(
            "Mô tả sự cố"
        )

        solution = st.text_area(
            "Cách xử lý"
        )

        submit = st.form_submit_button(
            "🚨 Lưu sự cố",
            type="primary",
        )

        if submit:

            if not title:

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
                        selected_tour["id"],
                        incident_date,
                        incident_time,
                        incident_type,
                        title,
                        description,
                        solution,
                        status,
                        created_by,
                    ),
                )

                st.success(
                    "Đã ghi nhận sự cố."
                )

                st.rerun()


# ============================================================
# 20. HƯỚNG DẪN VIÊN
# ============================================================

elif menu == "🧑‍💼 Hướng dẫn viên":

    st.subheader("🧑‍💼 Quản lý hướng dẫn viên")

    guides = query_df(
        """
        SELECT
            id,
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
            guides.drop(columns=["id"]),
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("### ➕ Thêm hướng dẫn viên")

    with st.form("add_guide"):

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
                value="Vietnamese, English",
            )

            experience = st.number_input(
                "Số năm kinh nghiệm",
                min_value=0,
                max_value=50,
                value=1,
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
# 21. CÀI ĐẶT
# ============================================================

elif menu == "⚙️ Cài đặt":

    st.subheader("⚙️ Cài đặt hệ thống")

    st.markdown("### 🗄️ Thông tin MySQL")

    try:

        db_info = database_test()

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Trạng thái",
            "Connected",
        )

        c2.metric(
            "Database",
            db_info["database"],
        )

        c3.metric(
            "User",
            db_info["user"],
        )

        st.success(
            "🟢 Kết nối Aiven MySQL thành công."
        )

        st.write(
            f"MySQL version: `{db_info['version']}`"
        )

    except Exception as e:

        st.error(
            "Không thể kết nối database."
        )

        st.code(str(e))

    st.markdown("### 📊 Thống kê Database")

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

            result = query_one(
                f"SELECT COUNT(*) AS total FROM `{table}`"
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

    st.markdown("### 🧪 Kiểm tra kết nối")

    if st.button(
        "🔄 Test MySQL",
        type="primary",
    ):

        try:

            result = database_test()

            st.success(
                "Kết nối MySQL hoạt động bình thường."
            )

            st.json(result)

        except Exception as e:

            st.error(
                "Kết nối thất bại."
            )

            st.code(str(e))

    st.markdown("---")

    st.info(
        """
        **TourMate – Smart Tour Guide Management System**

        Phiên bản demo phục vụ học tập và phát triển
        ứng dụng quản lý nghiệp vụ hướng dẫn viên du lịch.

        Các module:

        • Quản lý tour  
        • Lịch trình  
        • Khách hàng  
        • Checklist  
        • Điểm tham quan  
        • Thư viện thuyết minh  
        • Quản lý sự cố  
        • Quản lý hướng dẫn viên  
        • Dashboard  
        • MySQL Cloud Database
        """
    )


# ============================================================
# 22. FOOTER
# ============================================================

st.markdown(
    """
    <div style="
        text-align:center;
        color:#64748b;
        padding:30px 0 10px 0;
        font-size:13px;
    ">
        🧭 TourMate • Smart Tour Guide Management System
        <br>
        Tourism & Travel Management Application
    </div>
    """,
    unsafe_allow_html=True,
)
