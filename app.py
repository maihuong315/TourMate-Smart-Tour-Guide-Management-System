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

    # -----------------------------------------------------
    # GUIDE
    # -----------------------------------------------------

    guide = query_one("""
        SELECT id
        FROM guides
        WHERE email = %s
        LIMIT 1
    """, ("demo@tourmate.vn",))

    if not guide:

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
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
        """, (
            "Nguyễn Minh Anh",
            "0901234567",
            "demo@tourmate.vn",
            "Vietnamese, English",
            3,
            "Active"
        ))


    # -----------------------------------------------------
    # PLACES
    # -----------------------------------------------------

    place_count = query_one("""
        SELECT COUNT(*) AS total
        FROM places
    """)

    if place_count["total"] == 0:

        places = [

            (
                "Tháp Tam Thắng",
                "Vũng Tàu",
                "Cultural",
                "Một điểm tham quan nổi bật tại Vũng Tàu.",
                "Tháp mang giá trị văn hóa và kiến trúc.",
                "Kiến trúc, không gian tham quan và chụp ảnh.",
                "Nên chuẩn bị thông tin lịch sử ngắn gọn cho khách."
            ),

            (
                "Tượng Chúa Kitô Vua",
                "Vũng Tàu",
                "Religious",
                "Một biểu tượng nổi tiếng của thành phố Vũng Tàu.",
                "Công trình nằm trên Núi Nhỏ.",
                "Tầm nhìn toàn cảnh thành phố và biển.",
                "Nên chuẩn bị nước uống và giày thoải mái."
            ),

            (
                "Bãi Sau",
                "Vũng Tàu",
                "Beach",
                "Bãi biển nổi tiếng phục vụ nghỉ dưỡng và vui chơi.",
                "Khu vực phát triển du lịch biển.",
                "Biển, hoạt động vui chơi và cảnh hoàng hôn.",
                "Kiểm tra thời tiết trước khi tổ chức hoạt động."
            )
        ]

        for place in places:

            execute("""
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
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, place)


# =========================================================
# 9. KHỞI ĐỘNG APP AN TOÀN
# =========================================================

st.title("🧭 TourMate")
st.caption("Smart Tour Guide Management System")

with st.sidebar:

    st.markdown("## 🧭 TourMate")

    st.caption(
        "Hệ thống quản lý công việc dành cho hướng dẫn viên du lịch"
    )


# ---------------------------------------------------------
# DATABASE STARTUP
# ---------------------------------------------------------

try:

    db_info = database_test()

    init_db()

    seed_demo_data()

    db_ok = True

except Exception as e:

    db_ok = False

    st.error("❌ Không thể khởi tạo database.")

    st.code(str(e))

    st.warning(
        "Kiểm tra lại Host, Port, Database, User và Password Aiven."
    )

    st.stop()


# =========================================================
# 10. SIDEBAR MENU
# =========================================================

with st.sidebar:

    st.success("🟢 MySQL đã kết nối")

    st.caption(
        f"Database: {db_info['database_name']}"
    )

    st.divider()

    menu = st.radio(
        "MENU",
        [
            "🏠 Dashboard",
            "🚌 Quản lý Tour",
            "📅 Lịch trình",
            "👥 Khách hàng",
            "✅ Checklist",
            "📍 Điểm tham quan",
            "📖 Thư viện thuyết minh",
            "⚠️ Sự cố",
            "🧑‍💼 Hướng dẫn viên",
            "⚙️ Cài đặt"
        ]
    )


# =========================================================
# 11. DASHBOARD
# =========================================================

if menu == "🏠 Dashboard":

    st.header("🏠 Dashboard")

    today = date.today()

    tour_today = query_one("""
        SELECT COUNT(*) AS total
        FROM tours
        WHERE start_date <= %s
        AND end_date >= %s
        AND status <> 'Cancelled'
    """, (today, today))["total"]


    total_tours = query_one("""
        SELECT COUNT(*) AS total
        FROM tours
    """)["total"]


    total_guests = query_one("""
        SELECT COUNT(*) AS total
        FROM guests
    """)["total"]


    total_guides = query_one("""
        SELECT COUNT(*) AS total
        FROM guides
        WHERE status = 'Active'
    """)["total"]


    incidents = query_one("""
        SELECT COUNT(*) AS total
        FROM incidents
        WHERE status = 'Open'
    """)["total"]


    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "🚌 Tour hôm nay",
        tour_today
    )

    c2.metric(
        "📋 Tổng tour",
        total_tours
    )

    c3.metric(
        "👥 Tổng khách",
        total_guests
    )

    c4.metric(
        "🧑‍💼 Hướng dẫn viên",
        total_guides
    )


    st.divider()


    left, right = st.columns(2)


    with left:

        st.subheader("📅 Tour hôm nay")

        tours = query_df("""
            SELECT
                t.code AS 'Mã tour',
                t.name AS 'Tên tour',
                t.start_time AS 'Giờ',
                t.pickup_location AS 'Điểm đón',
                t.total_guests AS 'Khách',
                t.status AS 'Trạng thái'
            FROM tours t
            WHERE t.start_date <= %s
            AND t.end_date >= %s
            ORDER BY t.start_time
        """, (today, today))


        if tours.empty:

            st.info("Hôm nay chưa có tour.")

        else:

            st.dataframe(
                tours,
                use_container_width=True,
                hide_index=True
            )


    with right:

        st.subheader("⚠️ Sự cố đang mở")

        incident_df = query_df("""
            SELECT
                title AS 'Sự cố',
                type AS 'Loại',
                incident_date AS 'Ngày',
                status AS 'Trạng thái'
            FROM incidents
            WHERE status = 'Open'
            ORDER BY incident_date DESC
            LIMIT 10
        """)


        if incident_df.empty:

            st.success("Không có sự cố đang mở.")

        else:

            st.dataframe(
                incident_df,
                use_container_width=True,
                hide_index=True
            )


# =========================================================
# 12. QUẢN LÝ TOUR
# =========================================================

elif menu == "🚌 Quản lý Tour":

    st.header("🚌 Quản lý Tour")

    tab1, tab2 = st.tabs([
        "📋 Danh sách tour",
        "➕ Tạo tour"
    ])


    with tab1:

        tours = query_df("""
            SELECT
                t.id,
                t.code AS 'Mã tour',
                t.name AS 'Tên tour',
                g.name AS 'Hướng dẫn viên',
                t.start_date AS 'Ngày bắt đầu',
                t.end_date AS 'Ngày kết thúc',
                t.start_time AS 'Giờ',
                t.pickup_location AS 'Điểm đón',
                t.total_guests AS 'Số khách',
                t.status AS 'Trạng thái'
            FROM tours t
            LEFT JOIN guides g
                ON t.guide_id = g.id
            ORDER BY t.start_date DESC, t.start_time DESC
        """)


        if tours.empty:

            st.info("Chưa có tour.")

        else:

            st.dataframe(
                tours.drop(columns=["id"]),
                use_container_width=True,
                hide_index=True
            )


            st.divider()

            st.subheader("🗑️ Xóa tour")

            tour_options = query("""
                SELECT id, code, name
                FROM tours
                ORDER BY start_date DESC
            """)

            if tour_options:

                selected = st.selectbox(
                    "Chọn tour",
                    tour_options,
                    format_func=lambda x:
                    f"{x['code']} - {x['name']}"
                )


                if st.button(
                    "🗑️ Xóa tour",
                    type="secondary"
                ):

                    execute(
                        "DELETE FROM tours WHERE id = %s",
                        (selected["id"],)
                    )

                    st.success("Đã xóa tour.")

                    st.rerun()


    with tab2:

        guides = query("""
            SELECT id, name
            FROM guides
            WHERE status = 'Active'
            ORDER BY name
        """)


        with st.form("create_tour"):

            col1, col2 = st.columns(2)


            with col1:

                code = st.text_input(
                    "Mã tour *",
                    placeholder="VT-001"
                )

                name = st.text_input(
                    "Tên tour *",
                    placeholder="Vũng Tàu 2N1Đ"
                )

                start_date = st.date_input(
                    "Ngày bắt đầu",
                    date.today()
                )

                end_date = st.date_input(
                    "Ngày kết thúc",
                    date.today()
                )


            with col2:

                start_time = st.time_input(
                    "Giờ bắt đầu",
                    time(8, 0)
                )

                pickup = st.text_input(
                    "Điểm đón",
                    placeholder="Khách sạn..."
                )

                hotel = st.text_input(
                    "Khách sạn"
                )

                vehicle = st.text_input(
                    "Phương tiện",
                    placeholder="Xe 29 chỗ"
                )


            driver = st.text_input(
                "Tài xế"
            )


            total_guests = st.number_input(
                "Số khách",
                min_value=0,
                max_value=500,
                value=20
            )


            guide_id = None

            if guides:

                guide_names = [
                    g["name"]
                    for g in guides
                ]

                selected_guide = st.selectbox(
                    "Hướng dẫn viên",
                    guide_names
                )

                guide_id = next(
                    g["id"]
                    for g in guides
                    if g["name"] == selected_guide
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
                "➕ Tạo tour",
                type="primary"
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
                            (
                                %s,%s,%s,%s,%s,%s,
                                %s,%s,%s,%s,%s,%s,%s
                            )
                        """, (
                            code,
                            name,
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
                            notes
                        ))

                        st.success(
                            "🎉 Đã tạo tour thành công!"
                        )

                        st.rerun()

                    except Exception as e:

                        st.error(str(e))


# =========================================================
# 13. LỊCH TRÌNH
# =========================================================

elif menu == "📅 Lịch trình":

    st.header("📅 Lịch trình tour")


    tours = query("""
        SELECT id, code, name
        FROM tours
        ORDER BY start_date DESC
    """)


    if not tours:

        st.info(
            "Hãy tạo tour trước."
        )

    else:

        selected_tour = st.selectbox(
            "Chọn tour",
            tours,
            format_func=lambda x:
            f"{x['code']} - {x['name']}"
        )


        tour_id = selected_tour["id"]


        itinerary_df = query_df("""
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
        """, (tour_id,))


        if itinerary_df.empty:

            st.info(
                "Tour này chưa có lịch trình."
            )

        else:

            st.dataframe(
                itinerary_df.drop(
                    columns=["id"]
                ),
                use_container_width=True,
                hide_index=True
            )


        st.divider()

        st.subheader(
            "➕ Thêm hoạt động"
        )


        with st.form("add_itinerary"):

            c1, c2 = st.columns(2)

            with c1:

                itinerary_date = st.date_input(
                    "Ngày",
                    date.today()
                )

                itinerary_time = st.text_input(
                    "Giờ",
                    "08:00"
                )

                place = st.text_input(
                    "Địa điểm"
                )

            with c2:

                activity = st.text_area(
                    "Hoạt động"
                )

                transport = st.text_input(
                    "Phương tiện"
                )

                notes = st.text_area(
                    "Ghi chú"
                )


            submit = st.form_submit_button(
                "➕ Thêm lịch trình"
            )


            if submit:

                if not place:

                    st.error(
                        "Vui lòng nhập địa điểm."
                    )

                else:

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
                        VALUES (%s,%s,%s,%s,%s,%s,%s)
                    """, (
                        tour_id,
                        itinerary_date,
                        itinerary_time,
                        place,
                        activity,
                        transport,
                        notes
                    ))

                    st.success(
                        "Đã thêm hoạt động."
                    )

                    st.rerun()


# =========================================================
# 14. KHÁCH HÀNG
# =========================================================

elif menu == "👥 Khách hàng":

    st.header("👥 Danh sách khách")


    tours = query("""
        SELECT id, code, name
        FROM tours
        ORDER BY start_date DESC
    """)


    if not tours:

        st.info(
            "Chưa có tour."
        )

    else:

        selected_tour = st.selectbox(
            "Tour",
            tours,
            format_func=lambda x:
            f"{x['code']} - {x['name']}"
        )


        tour_id = selected_tour["id"]


        guests = query_df("""
            SELECT
                id,
                full_name AS 'Họ tên',
                gender AS 'Giới tính',
                age AS 'Tuổi',
                nationality AS 'Quốc tịch',
                phone AS 'Điện thoại',
                room_number AS 'Phòng',
                special_request AS 'Yêu cầu đặc biệt',
                attendance AS 'Điểm danh',
                notes AS 'Ghi chú'
            FROM guests
            WHERE tour_id = %s
            ORDER BY full_name
        """, (tour_id,))


        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Tổng khách",
            len(guests)
        )


        if not guests.empty:

            present = (
                guests["Điểm danh"] == "Present"
            ).sum()

            absent = (
                guests["Điểm danh"] == "Absent"
            ).sum()

        else:

            present = 0
            absent = 0


        c2.metric(
            "Có mặt",
            present
        )

        c3.metric(
            "Vắng",
            absent
        )


        if not guests.empty:

            st.dataframe(
                guests.drop(
                    columns=["id"]
                ),
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info(
                "Chưa có khách trong tour."
            )


        st.divider()

        st.subheader(
            "➕ Thêm khách"
        )


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
                        "Other"
                    ]
                )

                age = st.number_input(
                    "Tuổi",
                    min_value=0,
                    max_value=120,
                    value=25
                )

                nationality = st.text_input(
                    "Quốc tịch",
                    "Vietnam"
                )


            with c2:

                phone = st.text_input(
                    "Điện thoại"
                )

                room = st.text_input(
                    "Số phòng"
                )

                special = st.text_area(
                    "Yêu cầu đặc biệt"
                )

                notes = st.text_area(
                    "Ghi chú"
                )


            attendance = st.selectbox(
                "Điểm danh",
                [
                    "Present",
                    "Absent",
                    "Not checked"
                ]
            )


            submit = st.form_submit_button(
                "➕ Thêm khách"
            )


            if submit:

                if not full_name:

                    st.error(
                        "Vui lòng nhập họ tên."
                    )

                else:

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
                        full_name,
                        gender,
                        age,
                        nationality,
                        phone,
                        room,
                        special,
                        attendance,
                        notes
                    ))

                    st.success(
                        "Đã thêm khách."
                    )

                    st.rerun()


# =========================================================
# 15. CHECKLIST
# =========================================================

elif menu == "✅ Checklist":

    st.header("✅ Checklist hướng dẫn viên")


    tours = query("""
        SELECT id, code, name
        FROM tours
        ORDER BY start_date DESC
    """)


    selected_tour_id = None


    if tours:

        selected_tour = st.selectbox(
            "Tour",
            tours,
            format_func=lambda x:
            f"{x['code']} - {x['name']}"
        )

        selected_tour_id = selected_tour["id"]


    st.subheader(
        "➕ Thêm công việc"
    )


    with st.form("task_form"):

        task_name = st.text_input(
            "Tên công việc",
            placeholder="Kiểm tra danh sách khách"
        )

        task_type = st.selectbox(
            "Loại",
            [
                "Before Tour",
                "During Tour",
                "After Tour"
            ]
        )

        due_date = st.date_input(
            "Ngày thực hiện",
            date.today()
        )

        due_time = st.time_input(
            "Giờ",
            time(7, 30)
        )

        assigned = st.text_input(
            "Người phụ trách"
        )

        notes = st.text_area(
            "Ghi chú"
        )


        submit = st.form_submit_button(
            "➕ Thêm công việc"
        )


        if submit:

            if not task_name:

                st.error(
                    "Vui lòng nhập tên công việc."
                )

            else:

                execute("""
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
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                """, (
                    selected_tour_id,
                    task_name,
                    task_type,
                    due_date,
                    due_time,
                    assigned,
                    notes
                ))

                st.success(
                    "Đã thêm công việc."
                )

                st.rerun()


    st.divider()

    tasks = query_df("""
        SELECT
            id,
            task_name AS 'Công việc',
            task_type AS 'Loại',
            due_date AS 'Ngày',
            due_time AS 'Giờ',
            assigned_to AS 'Phụ trách',
            done AS 'Hoàn thành',
            notes AS 'Ghi chú'
        FROM tasks
        ORDER BY due_date, due_time
    """)


    if tasks.empty:

        st.info(
            "Chưa có công việc."
        )

    else:

        for _, row in tasks.iterrows():

            task_id = int(row["id"])

            done = bool(row["Hoàn thành"])


            col1, col2, col3 = st.columns(
                [0.08, 0.75, 0.17]
            )


            with col1:

                checked = st.checkbox(
                    "",
                    value=done,
                    key=f"task_{task_id}"
                )


            with col2:

                if checked:

                    st.markdown(
                        f"~~{row['Công việc']}~~"
                    )

                else:

                    st.write(
                        f"**{row['Công việc']}**"
                    )

                st.caption(
                    f"{row['Loại']} • "
                    f"{row['Ngày']} • "
                    f"{row['Giờ']}"
                )


            with col3:

                if checked != done:

                    execute("""
                        UPDATE tasks
                        SET done = %s
                        WHERE id = %s
                    """, (
                        1 if checked else 0,
                        task_id
                    ))

                    st.rerun()


# =========================================================
# 16. ĐIỂM THAM QUAN
# =========================================================

elif menu == "📍 Điểm tham quan":

    st.header("📍 Điểm tham quan")


    places = query_df("""
        SELECT
            id,
            name AS 'Tên',
            location AS 'Địa điểm',
            category AS 'Loại',
            introduction AS 'Giới thiệu',
            history AS 'Lịch sử',
            highlights AS 'Điểm nổi bật',
            tips AS 'Lưu ý'
        FROM places
        ORDER BY name
    """)


    if places.empty:

        st.info(
            "Chưa có điểm tham quan."
        )

    else:

        for _, place in places.iterrows():

            with st.expander(
                f"📍 {place['Tên']} — {place['Địa điểm']}"
            ):

                st.write(
                    f"**Loại:** {place['Loại']}"
                )

                st.write(
                    f"**Giới thiệu:** "
                    f"{place['Giới thiệu'] or ''}"
                )

                st.write(
                    f"**Lịch sử:** "
                    f"{place['Lịch sử'] or ''}"
                )

                st.write(
                    f"**Điểm nổi bật:** "
                    f"{place['Điểm nổi bật'] or ''}"
                )

                st.info(
                    f"💡 **Lưu ý hướng dẫn:** "
                    f"{place['Lưu ý'] or ''}"
                )


    st.divider()

    st.subheader(
        "➕ Thêm điểm tham quan"
    )


    with st.form("place_form"):

        name = st.text_input(
            "Tên điểm tham quan"
        )

        location = st.text_input(
            "Địa điểm"
        )

        category = st.selectbox(
            "Loại",
            [
                "Cultural",
                "Historical",
                "Beach",
                "Religious",
                "Nature",
                "Entertainment",
                "Shopping",
                "Other"
            ]
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
            "Lưu ý cho hướng dẫn viên"
        )


        submit = st.form_submit_button(
            "➕ Thêm địa điểm"
        )


        if submit:

            if not name:

                st.error(
                    "Vui lòng nhập tên."
                )

            else:

                execute("""
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
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                """, (
                    name,
                    location,
                    category,
                    introduction,
                    history,
                    highlights,
                    tips
                ))

                st.success(
                    "Đã thêm điểm tham quan."
                )

                st.rerun()


# =========================================================
# 17. THƯ VIỆN THUYẾT MINH
# =========================================================

elif menu == "📖 Thư viện thuyết minh":

    st.header("📖 Thư viện thuyết minh")


    places = query("""
        SELECT
            id,
            name,
            location,
            introduction,
            history,
            highlights,
            tips
        FROM places
        ORDER BY name
    """)


    if not places:

        st.info(
            "Chưa có dữ liệu."
        )

    else:

        selected = st.selectbox(
            "Chọn điểm tham quan",
            places,
            format_func=lambda x:
            f"{x['name']} — {x['location']}"
        )


        st.subheader(
            f"🎤 Kịch bản: {selected['name']}"
        )


        st.markdown(
            "### 🎬 Mở đầu"
        )

        st.info(
            "Xin chào quý khách! "
            "Sau đây chúng ta sẽ cùng khám phá "
            f"{selected['name']}."
        )


        st.markdown(
            "### 📖 Giới thiệu"
        )

        st.write(
            selected["introduction"] or
            "Chưa có nội dung."
        )


        st.markdown(
            "### 🏛️ Lịch sử"
        )

        st.write(
            selected["history"] or
            "Chưa có nội dung."
        )


        st.markdown(
            "### ⭐ Điểm nổi bật"
        )

        st.write(
            selected["highlights"] or
            "Chưa có nội dung."
        )


        st.markdown(
            "### 💡 Lưu ý"
        )

        st.warning(
            selected["tips"] or
            "Chưa có lưu ý."
        )


# =========================================================
# 18. SỰ CỐ
# =========================================================

elif menu == "⚠️ Sự cố":

    st.header("⚠️ Nhật ký sự cố")


    tours = query("""
        SELECT id, code, name
        FROM tours
        ORDER BY start_date DESC
    """)


    tour_id = None


    if tours:

        selected_tour = st.selectbox(
            "Tour liên quan",
            tours,
            format_func=lambda x:
            f"{x['code']} - {x['name']}"
        )

        tour_id = selected_tour["id"]


    with st.form("incident_form"):

        incident_date = st.date_input(
            "Ngày",
            date.today()
        )

        incident_time = st.time_input(
            "Giờ",
            datetime.now().time()
        )

        incident_type = st.selectbox(
            "Loại sự cố",
            [
                "Guest",
                "Transport",
                "Hotel",
                "Health",
                "Weather",
                "Schedule",
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
            "Người ghi nhận"
        )


        submit = st.form_submit_button(
            "⚠️ Ghi nhận sự cố"
        )


        if submit:

            if not title:

                st.error(
                    "Vui lòng nhập tiêu đề."
                )

            else:

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
                    incident_date,
                    incident_time,
                    incident_type,
                    title,
                    description,
                    solution,
                    "Open",
                    created_by
                ))

                st.success(
                    "Đã ghi nhận sự cố."
                )

                st.rerun()


    st.divider()

    incidents = query_df("""
        SELECT
            i.id,
            i.title AS 'Tiêu đề',
            i.type AS 'Loại',
            i.incident_date AS 'Ngày',
            i.incident_time AS 'Giờ',
            t.code AS 'Tour',
            i.status AS 'Trạng thái',
            i.description AS 'Mô tả',
            i.solution AS 'Xử lý',
            i.created_by AS 'Người ghi nhận'
        FROM incidents i
        LEFT JOIN tours t
            ON i.tour_id = t.id
        ORDER BY i.incident_date DESC
    """)


    if incidents.empty:

        st.info(
            "Chưa có sự cố."
        )

    else:

        st.dataframe(
            incidents.drop(
                columns=["id"]
            ),
            use_container_width=True,
            hide_index=True
        )


# =========================================================
# 19. HƯỚNG DẪN VIÊN
# =========================================================

elif menu == "🧑‍💼 Hướng dẫn viên":

    st.header("🧑‍💼 Quản lý hướng dẫn viên")


    guides = query_df("""
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
    """)


    if not guides.empty:

        st.dataframe(
            guides.drop(
                columns=["id"]
            ),
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


    with st.form("guide_form"):

        name = st.text_input(
            "Họ tên *"
        )

        phone = st.text_input(
            "Điện thoại"
        )

        email = st.text_input(
            "Email"
        )

        language = st.text_input(
            "Ngôn ngữ",
            "Vietnamese, English"
        )

        experience = st.number_input(
            "Số năm kinh nghiệm",
            min_value=0,
            max_value=50,
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
            "➕ Thêm hướng dẫn viên"
        )


        if submit:

            if not name:

                st.error(
                    "Vui lòng nhập họ tên."
                )

            else:

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
                    VALUES (%s,%s,%s,%s,%s,%s)
                """, (
                    name,
                    phone,
                    email,
                    language,
                    experience,
                    status
                ))

                st.success(
                    "Đã thêm hướng dẫn viên."
                )

                st.rerun()


# =========================================================
# 20. CÀI ĐẶT
# =========================================================

elif menu == "⚙️ Cài đặt":

    st.header("⚙️ Cài đặt hệ thống")


    st.subheader(
        "🗄️ Thông tin MySQL"
    )


    try:

        info = database_test()

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Database",
            info["database_name"]
        )

        c2.metric(
            "User",
            info["db_user"]
        )

        c3.metric(
            "MySQL",
            str(info["version"]).split("-")[0]
        )


    except Exception as e:

        st.error(
            str(e)
        )


    st.divider()


    st.subheader(
        "📊 Thống kê database"
    )


    tables = [
        "guides",
        "tours",
        "itinerary",
        "guests",
        "tasks",
        "places",
        "incidents"
    ]


    stats = []


    for table in tables:

        try:

            row = query_one(
                f"SELECT COUNT(*) AS total FROM `{table}`"
            )

            stats.append({
                "Bảng": table,
                "Số bản ghi": row["total"]
            })

        except:

            stats.append({
                "Bảng": table,
                "Số bản ghi": "Error"
            })


    st.dataframe(
        pd.DataFrame(stats),
        use_container_width=True,
        hide_index=True
    )


    st.divider()


    st.subheader(
        "🔧 Kiểm tra kết nối"
    )


    if st.button(
        "🔄 Test MySQL"
    ):

        try:

            info = database_test()

            st.success(
                "🟢 Kết nối MySQL hoạt động bình thường."
            )

            st.json(info)

        except Exception as e:

            st.error(
                str(e)
            )


# =========================================================
# FOOTER
# =========================================================

st.sidebar.divider()

st.sidebar.caption(
    "TourMate © 2026"
)

st.sidebar.caption(
    "Smart Tour Guide Management System"
)
