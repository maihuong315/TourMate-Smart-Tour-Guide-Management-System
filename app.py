import streamlit as st
import pymysql
import pandas as pd
from datetime import datetime, date, time, timedelta
from pymysql.cursors import DictCursor


# =========================================================
# 1. CẤU HÌNH TRANG
# =========================================================

st.set_page_config(
    page_title="TourMate – Smart Tour Guide",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# 2. CẤU HÌNH MYSQL AIVEN
# =========================================================

MYSQL_CONFIG = {
    "host": "mysql-19728385-npmaihuong-927f.b.aivencloud.com",
    "port": 27942,
    "user": "avnadmin",

    # =====================================================
    # DÁN PASSWORD AIVEN CỦA EM VÀO ĐÂY
    # PHẢI CÓ DẤU NGOẶC KÉP
    # =====================================================
    "password": "AVNS_zBDlzsF9I5fC-EdWcl0",

    "database": "defaultdb",

    "charset": "utf8mb4",
    "cursorclass": DictCursor,
    "autocommit": True,
    "connect_timeout": 15,
    "read_timeout": 30,
    "write_timeout": 30
}


# =========================================================
# 3. HÀM KẾT NỐI DATABASE
# =========================================================

def get_conn():
    if not MYSQL_CONFIG["password"]:
        raise RuntimeError(
            "Chưa nhập password Aiven trong MYSQL_CONFIG."
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

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows)


# =========================================================
# 4. KIỂM TRA DATABASE
# =========================================================

def database_test():

    row = query_one("""
        SELECT
            VERSION() AS version,
            DATABASE() AS database_name,
            CURRENT_USER() AS db_user
    """)

    return row


# =========================================================
# 5. KIỂM TRA BẢNG
# =========================================================

def table_exists(table_name):

    row = query_one("""
        SELECT COUNT(*) AS total
        FROM information_schema.tables
        WHERE table_schema = DATABASE()
        AND table_name = %s
    """, (table_name,))

    return row and row["total"] > 0


def get_columns(table_name):

    rows = query("""
        SELECT COLUMN_NAME
        FROM information_schema.columns
        WHERE table_schema = DATABASE()
        AND table_name = %s
    """, (table_name,))

    return {
        row["COLUMN_NAME"]
        for row in rows
    }


# =========================================================
# 6. TẠO / CẬP NHẬT COLUMN AN TOÀN
# =========================================================

def ensure_column(
    table_name,
    column_name,
    column_definition
):

    try:

        columns = get_columns(table_name)

        if column_name in columns:
            return

        execute(
            f"""
            ALTER TABLE `{table_name}`
            ADD COLUMN `{column_name}` {column_definition}
            """
        )

    except RuntimeError as e:

        # MySQL 1060 = column đã tồn tại
        if "MySQL Error 1060" in str(e):
            return

        raise


# =========================================================
# 7. KHỞI TẠO DATABASE
# =========================================================

def init_db():

    # -----------------------------------------------------
    # GUIDES
    # -----------------------------------------------------

    execute("""
        CREATE TABLE IF NOT EXISTS guides (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(150) NOT NULL,
            phone VARCHAR(50),
            email VARCHAR(150),
            language VARCHAR(100),
            experience_years INT DEFAULT 0,
            status VARCHAR(50) DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)


    # -----------------------------------------------------
    # TOURS
    # -----------------------------------------------------

    execute("""
        CREATE TABLE IF NOT EXISTS tours (
            id INT AUTO_INCREMENT PRIMARY KEY,
            code VARCHAR(50) UNIQUE,
            name VARCHAR(255) NOT NULL,
            guide_id INT NULL,
            start_date DATE,
            end_date DATE,
            start_time TIME,
            pickup_location VARCHAR(255),
            hotel VARCHAR(255),
            vehicle VARCHAR(255),
            driver VARCHAR(150),
            total_guests INT DEFAULT 0,
            status VARCHAR(50) DEFAULT 'Scheduled',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            INDEX idx_tour_start_date (start_date),
            INDEX idx_tour_guide (guide_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)


    # -----------------------------------------------------
    # ITINERARY
    # -----------------------------------------------------

    execute("""
        CREATE TABLE IF NOT EXISTS itinerary (
            id INT AUTO_INCREMENT PRIMARY KEY,
            tour_id INT NOT NULL,
            tour_date DATE,
            time VARCHAR(20),
            place VARCHAR(255),
            activity TEXT,
            transport VARCHAR(100),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            INDEX idx_itinerary_tour (tour_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)


    # -----------------------------------------------------
    # GUESTS
    # -----------------------------------------------------

    execute("""
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
            attendance VARCHAR(50) DEFAULT 'Present',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            INDEX idx_guest_tour (tour_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)


    # -----------------------------------------------------
    # TASKS
    # -----------------------------------------------------

    execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INT AUTO_INCREMENT PRIMARY KEY,
            tour_id INT NULL,
            task_name VARCHAR(255) NOT NULL,
            task_type VARCHAR(100),
            due_date DATE,
            due_time TIME,
            assigned_to VARCHAR(150),
            done TINYINT(1) DEFAULT 0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            INDEX idx_task_tour (tour_id),
            INDEX idx_task_date (due_date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)


    # -----------------------------------------------------
    # PLACES
    # -----------------------------------------------------

    execute("""
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
    """)


    # -----------------------------------------------------
    # INCIDENTS
    # -----------------------------------------------------

    execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id INT AUTO_INCREMENT PRIMARY KEY,
            tour_id INT NULL,
            incident_date DATE,
            incident_time TIME,
            type VARCHAR(100),
            title VARCHAR(255),
            description TEXT,
            solution TEXT,
            status VARCHAR(50) DEFAULT 'Open',
            created_by VARCHAR(150),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            INDEX idx_incident_tour (tour_id),
            INDEX idx_incident_date (incident_date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)


    # =====================================================
    # MIGRATION AN TOÀN
    # =====================================================

    migration = {

        "guides": {
            "phone": "VARCHAR(50)",
            "email": "VARCHAR(150)",
            "language": "VARCHAR(100)",
            "experience_years": "INT DEFAULT 0",
            "status": "VARCHAR(50) DEFAULT 'Active'"
        },

        "tours": {
            "code": "VARCHAR(50)",
            "guide_id": "INT NULL",
            "start_date": "DATE",
            "end_date": "DATE",
            "start_time": "TIME",
            "pickup_location": "VARCHAR(255)",
            "hotel": "VARCHAR(255)",
            "vehicle": "VARCHAR(255)",
            "driver": "VARCHAR(150)",
            "total_guests": "INT DEFAULT 0",
            "status": "VARCHAR(50) DEFAULT 'Scheduled'",
            "notes": "TEXT"
        },

        "itinerary": {
            "tour_id": "INT",
            "tour_date": "DATE",
            "time": "VARCHAR(20)",
            "place": "VARCHAR(255)",
            "activity": "TEXT",
            "transport": "VARCHAR(100)",
            "notes": "TEXT"
        },

        "guests": {
            "tour_id": "INT",
            "full_name": "VARCHAR(150)",
            "gender": "VARCHAR(30)",
            "age": "INT",
            "nationality": "VARCHAR(100)",
            "phone": "VARCHAR(50)",
            "room_number": "VARCHAR(50)",
            "special_request": "TEXT",
            "attendance": "VARCHAR(50)",
            "notes": "TEXT"
        },

        "tasks": {
            "tour_id": "INT NULL",
            "task_name": "VARCHAR(255)",
            "task_type": "VARCHAR(100)",
            "due_date": "DATE",
            "due_time": "TIME",
            "assigned_to": "VARCHAR(150)",
            "done": "TINYINT(1) DEFAULT 0",
            "notes": "TEXT"
        },

        "places": {
            "location": "VARCHAR(255)",
            "category": "VARCHAR(100)",
            "introduction": "TEXT",
            "history": "TEXT",
            "highlights": "TEXT",
            "tips": "TEXT",
            "image_url": "TEXT"
        },

        "incidents": {
            "tour_id": "INT NULL",
            "incident_date": "DATE",
            "incident_time": "TIME",
            "type": "VARCHAR(100)",
            "title": "VARCHAR(255)",
            "description": "TEXT",
            "solution": "TEXT",
            "status": "VARCHAR(50)",
            "created_by": "VARCHAR(150)"
        }
    }


    for table_name, columns in migration.items():

        if not table_exists(table_name):
            continue

        for column_name, definition in columns.items():

            ensure_column(
                table_name,
                column_name,
                definition
            )


# =========================================================
# 8. DỮ LIỆU MẪU
# =========================================================

def seed_demo_data():

    # =====================================================
    # 1. HƯỚNG DẪN VIÊN MẪU
    # =====================================================

    guides_data = [
        (
            "Nguyễn Minh Anh",
            "0901234567",
            "minhanh@tourmate.vn",
            "Vietnamese, English",
            5,
            "Active"
        ),
        (
            "Trần Quốc Huy",
            "0912345678",
            "quochuy@tourmate.vn",
            "Vietnamese, English, Chinese",
            8,
            "Active"
        ),
        (
            "Lê Ngọc Mai",
            "0923456789",
            "ngocmai@tourmate.vn",
            "Vietnamese, English, Korean",
            3,
            "Active"
        )
    ]

    for guide in guides_data:

        exists = query_one("""
            SELECT id
            FROM guides
            WHERE email = %s
            LIMIT 1
        """, (guide[2],))

        if not exists:

            execute("""
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
            """, guide)


    # =====================================================
    # 2. ĐIỂM THAM QUAN
    # =====================================================

    places_data = [

        (
            "Tháp Tam Thắng",
            "Vũng Tàu",
            "Cultural",
            "Tháp Tam Thắng là công trình mang dấu ấn văn hóa và lịch sử của thành phố Vũng Tàu, thích hợp để hướng dẫn viên giới thiệu cho du khách về quá trình hình thành và phát triển của vùng đất ven biển.",
            "Công trình gắn với hình ảnh ba ngọn tháp và những giá trị văn hóa đặc trưng của Vũng Tàu.",
            "Kiến trúc đặc trưng, không gian tham quan, chụp ảnh và tìm hiểu văn hóa địa phương.",
            "Hướng dẫn viên nên giới thiệu ngắn gọn trước khi khách tự do tham quan.",
            ""
        ),

        (
            "Tượng Chúa Kitô Vua",
            "Núi Nhỏ, Vũng Tàu",
            "Religious",
            "Tượng Chúa Kitô Vua là một trong những biểu tượng nổi tiếng của du lịch Vũng Tàu, nằm trên Núi Nhỏ và hướng ra biển.",
            "Công trình được xây dựng trên núi và trở thành một điểm tham quan nổi tiếng của thành phố.",
            "Tầm nhìn toàn cảnh biển Vũng Tàu, tượng lớn, khu vực leo núi và chụp ảnh.",
            "Nên nhắc khách mang giày thoải mái và chuẩn bị nước uống.",
            ""
        ),

        (
            "Bãi Sau Vũng Tàu",
            "Vũng Tàu",
            "Beach",
            "Bãi Sau là một trong những khu vực biển nổi tiếng của Vũng Tàu, phù hợp với các hoạt động nghỉ dưỡng, vui chơi và ngắm cảnh.",
            "Khu vực Bãi Sau phát triển mạnh cùng với hoạt động du lịch biển của thành phố.",
            "Bãi biển rộng, cảnh biển, hoạt động vui chơi và không gian thư giãn.",
            "Kiểm tra thời tiết và tình trạng biển trước khi tổ chức hoạt động.",
            ""
        ),

        (
            "Hải đăng Vũng Tàu",
            "Núi Nhỏ, Vũng Tàu",
            "Historical",
            "Hải đăng Vũng Tàu là một điểm tham quan có giá trị lịch sử và cũng là vị trí ngắm cảnh nổi tiếng.",
            "Hải đăng được xây dựng nhằm hỗ trợ hoạt động hàng hải trong khu vực.",
            "View thành phố, biển và cung đường ven núi.",
            "Nên đi vào thời điểm thời tiết đẹp để có tầm nhìn tốt.",
            ""
        ),

        (
            "Nhà úp ngược Vũng Tàu",
            "Vũng Tàu",
            "Entertainment",
            "Một điểm check-in độc đáo với không gian nội thất được thiết kế theo phong cách đảo ngược.",
            "Mô hình hướng đến trải nghiệm chụp ảnh và giải trí.",
            "Các căn phòng đảo ngược và nhiều góc chụp ảnh.",
            "Phù hợp với khách trẻ và nhóm bạn.",
            ""
        ),

        (
            "Bạch Dinh",
            "Vũng Tàu",
            "Historical",
            "Bạch Dinh là công trình kiến trúc mang giá trị lịch sử và văn hóa nổi bật tại Vũng Tàu.",
            "Công trình gắn với nhiều giai đoạn lịch sử của khu vực.",
            "Kiến trúc cổ, khuôn viên và các hiện vật.",
            "Hướng dẫn viên nên chuẩn bị trước các thông tin lịch sử quan trọng.",
            ""
        )
    ]

    for place in places_data:

        exists = query_one("""
            SELECT id
            FROM places
            WHERE name = %s
            LIMIT 1
        """, (place[0],))

        if not exists:

            execute("""
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
            """, place)


    # =====================================================
    # 3. TOUR MẪU
    # =====================================================

    guide = query_one("""
        SELECT id
        FROM guides
        WHERE email = %s
        LIMIT 1
    """, ("minhanh@tourmate.vn",))

    if not guide:
        return

    guide_id = guide["id"]

    tours_data = [

        (
            "VT-001",
            "Vũng Tàu Discovery 2N1Đ",
            guide_id,
            date.today(),
            date.today() + timedelta(days=1),
            time(7, 30),
            "Khách sạn Pullman Vũng Tàu",
            "Pullman Vũng Tàu",
            "Xe 29 chỗ",
            "Nguyễn Văn Nam",
            28,
            "In Progress",
            "Tour trải nghiệm Vũng Tàu 2 ngày 1 đêm."
        ),

        (
            "VT-002",
            "Vũng Tàu Beach Escape",
            guide_id,
            date.today() + timedelta(days=3),
            date.today() + timedelta(days=3),
            time(8, 0),
            "Bãi Sau",
            "Không lưu trú",
            "Xe 16 chỗ",
            "Trần Văn Bình",
            16,
            "Scheduled",
            "Tour trong ngày dành cho khách gia đình."
        ),

        (
            "VT-003",
            "Southern Vietnam Highlights",
            guide_id,
            date.today() + timedelta(days=7),
            date.today() + timedelta(days=9),
            time(6, 30),
            "TP. Hồ Chí Minh",
            "Vũng Tàu Resort",
            "Xe 45 chỗ",
            "Lê Hoàng",
            35,
            "Scheduled",
            "Tour kết hợp TP.HCM - Vũng Tàu."
        )
    ]

    for tour in tours_data:

        exists = query_one("""
            SELECT id
            FROM tours
            WHERE code = %s
            LIMIT 1
        """, (tour[0],))

        if not exists:

            execute("""
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
            """, tour)


    # =====================================================
    # 4. LỊCH TRÌNH TOUR VT-001
    # =====================================================

    tour = query_one("""
        SELECT id
        FROM tours
        WHERE code = 'VT-001'
        LIMIT 1
    """)

    if not tour:
        return

    tour_id = tour["id"]

    itinerary_count = query_one("""
        SELECT COUNT(*) AS total
        FROM itinerary
        WHERE tour_id = %s
    """, (tour_id,))

    if itinerary_count["total"] == 0:

        itinerary_data = [

            (
                tour_id,
                date.today(),
                "07:30",
                "Khách sạn Pullman Vũng Tàu",
                "Đón khách và kiểm tra danh sách đoàn",
                "Xe 29 chỗ",
                "Kiểm tra đủ 28 khách trước khi khởi hành."
            ),

            (
                tour_id,
                date.today(),
                "08:30",
                "Tượng Chúa Kitô Vua",
                "Tham quan và nghe thuyết minh",
                "Xe + đi bộ",
                "Nhắc khách mang nước uống."
            ),

            (
                tour_id,
                date.today(),
                "10:30",
                "Hải đăng Vũng Tàu",
                "Tham quan, chụp ảnh",
                "Xe",
                "Tập trung đoàn lúc 11:15."
            ),

            (
                tour_id,
                date.today(),
                "12:00",
                "Nhà hàng Gành Hào",
                "Ăn trưa",
                "Xe",
                "Kiểm tra thực đơn và yêu cầu đặc biệt."
            ),

            (
                tour_id,
                date.today(),
                "14:00",
                "Bãi Sau",
                "Tự do nghỉ ngơi và vui chơi",
                "Xe",
                "Thông báo thời gian tập trung."
            ),

            (
                tour_id,
                date.today(),
                "17:30",
                "Khách sạn",
                "Check-in và nhận phòng",
                "Xe",
                "Phát thông tin phòng cho khách."
            ),

            (
                tour_id,
                date.today() + timedelta(days=1),
                "07:00",
                "Khách sạn",
                "Ăn sáng",
                "Đi bộ",
                "Nhắc khách giờ checkout."
            ),

            (
                tour_id,
                date.today() + timedelta(days=1),
                "09:00",
                "Bạch Dinh",
                "Tham quan di tích",
                "Xe",
                "Chuẩn bị nội dung thuyết minh."
            ),

            (
                tour_id,
                date.today() + timedelta(days=1),
                "11:30",
                "Nhà hàng địa phương",
                "Ăn trưa",
                "Xe",
                "Kiểm tra số lượng khách."
            ),

            (
                tour_id,
                date.today() + timedelta(days=1),
                "14:00",
                "Tháp Tam Thắng",
                "Tham quan và chụp ảnh",
                "Xe",
                "Tổ chức chụp ảnh tập thể."
            ),

            (
                tour_id,
                date.today() + timedelta(days=1),
                "16:00",
                "TP. Hồ Chí Minh",
                "Kết thúc tour",
                "Xe 29 chỗ",
                "Cảm ơn khách và kiểm tra hành lý."
            )
        ]

        for item in itinerary_data:

            execute("""
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
            """, item)


    # =====================================================
    # 5. KHÁCH TOUR
    # =====================================================

    guest_count = query_one("""
        SELECT COUNT(*) AS total
        FROM guests
        WHERE tour_id = %s
    """, (tour_id,))

    if guest_count["total"] == 0:

        guests_data = [

            ("Nguyễn Minh Tuấn", "Male", 35, "Vietnam", "0901111111", "201", "Không", "Present", ""),
            ("Trần Thu Hà", "Female", 31, "Vietnam", "0902222222", "202", "Không", "Present", ""),
            ("John Smith", "Male", 42, "United Kingdom", "", "203", "Vegetarian", "Present", "Ăn chay"),
            ("Emily Johnson", "Female", 29, "United States", "", "204", "Không", "Present", ""),
            ("Park Ji Min", "Female", 27, "South Korea", "", "205", "Không cay", "Present", ""),
            ("Lê Hoàng Nam", "Male", 45, "Vietnam", "0903333333", "206", "Không", "Present", ""),
            ("Phạm Ngọc Anh", "Female", 34, "Vietnam", "0904444444", "207", "Không", "Present", ""),
            ("David Brown", "Male", 38, "Australia", "", "208", "Không", "Present", ""),
            ("Sarah Wilson", "Female", 36, "Australia", "", "209", "Không", "Present", ""),
            ("Nguyễn Thanh Bình", "Male", 41, "Vietnam", "0905555555", "210", "Không", "Not checked")
        ]

        for guest in guests_data:

            execute("""
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
            """, (
                tour_id,
                guest[0],
                guest[1],
                guest[2],
                guest[3],
                guest[4],
                guest[5],
                guest[6],
                guest[7],
                guest[8]
            ))


    # =====================================================
    # 6. CHECKLIST
    # =====================================================

    task_count = query_one("""
        SELECT COUNT(*) AS total
        FROM tasks
        WHERE tour_id = %s
    """, (tour_id,))

    if task_count["total"] == 0:

        tasks_data = [

            (
                tour_id,
                "Kiểm tra danh sách khách",
                "Before Tour",
                date.today(),
                time(6, 45),
                "Nguyễn Minh Anh",
                1,
                "Đã kiểm tra"
            ),

            (
                tour_id,
                "Kiểm tra phương tiện",
                "Before Tour",
                date.today(),
                time(7, 0),
                "Nguyễn Minh Anh",
                1,
                "Xe 29 chỗ"
            ),

            (
                tour_id,
                "Chuẩn bị nước uống",
                "Before Tour",
                date.today(),
                time(7, 10),
                "Nguyễn Minh Anh",
                1,
                "28 chai"
            ),

            (
                tour_id,
                "Điểm danh khách tại Bãi Sau",
                "During Tour",
                date.today(),
                time(14, 0),
                "Nguyễn Minh Anh",
                0,
                ""
            ),

            (
                tour_id,
                "Kiểm tra hành lý",
                "After Tour",
                date.today() + timedelta(days=1),
                time(15, 30),
                "Nguyễn Minh Anh",
                0,
                ""
            ),

            (
                tour_id,
                "Gửi feedback cho công ty",
                "After Tour",
                date.today() + timedelta(days=1),
                time(18, 0),
                "Nguyễn Minh Anh",
                0,
                ""
            )
        ]

        for task in tasks_data:

            execute("""
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
            """, task)


    # =====================================================
    # 7. SỰ CỐ MẪU
    # =====================================================

    incident_count = query_one("""
        SELECT COUNT(*) AS total
        FROM incidents
        WHERE tour_id = %s
    """, (tour_id,))

    if incident_count["total"] == 0:

        execute("""
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
        """, (
            tour_id,
            date.today(),
            time(10, 45),
            "Guest",
            "Khách quên điện thoại trên xe",
            "Một khách phát hiện điện thoại không có trong túi sau khi xuống xe.",
            "Liên hệ tài xế kiểm tra ghế ngồi và tìm thấy điện thoại.",
            "Resolved",
            "Nguyễn Minh Anh"
        ))

        execute("""
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
        """, (
            tour_id,
            date.today(),
            time(13, 30),
            "Schedule",
            "Đoàn đến điểm tham quan trễ",
            "Thời gian ăn trưa kéo dài hơn dự kiến.",
            "Điều chỉnh thời gian tham quan và thông báo cho khách.",
            "Open",
            "Nguyễn Minh Anh"
        ))
