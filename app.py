import streamlit as st
import pymysql
import pandas as pd

from pymysql.cursors import DictCursor
from datetime import datetime, date, time, timedelta


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

MYSQL_CONFIG = {
    "host": "mysql-19728385-npmaihuong-927f.b.aivencloud.com",
    "port": 27942,
    "user": "avnadmin",
    "password": "AVNS_zBDlzsF9I5fC-EdWcl0",
    "database": "defaultdb",
}


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_conn():
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
        read_timeout=20,
        write_timeout=20
    )


def execute(sql, params=()):
    conn = None

    try:
        conn = get_conn()

        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.lastrowid

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

    finally:
        if conn:
            conn.close()


def query_df(sql, params=()):
    rows = query(sql, params)
    return pd.DataFrame(rows)


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_db():

    statements = [

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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            CONSTRAINT fk_tour_guide
            FOREIGN KEY (guide_id)
            REFERENCES guides(id)
            ON DELETE SET NULL
        )
        """,

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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            CONSTRAINT fk_itinerary_tour
            FOREIGN KEY (tour_id)
            REFERENCES tours(id)
            ON DELETE CASCADE
        )
        """,

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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            CONSTRAINT fk_guest_tour
            FOREIGN KEY (tour_id)
            REFERENCES tours(id)
            ON DELETE CASCADE
        )
        """,

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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            CONSTRAINT fk_task_tour
            FOREIGN KEY (tour_id)
            REFERENCES tours(id)
            ON DELETE CASCADE
        )
        """,

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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            CONSTRAINT fk_incident_tour
            FOREIGN KEY (tour_id)
            REFERENCES tours(id)
            ON DELETE CASCADE
        )
        """
    ]

    for sql in statements:
        execute(sql)

    # --------------------------------------------------------
    # DEMO GUIDE
    # --------------------------------------------------------

    guide_count = query(
        "SELECT COUNT(*) AS total FROM guides"
    )[0]["total"]

    if guide_count == 0:
        execute(
            """
            INSERT INTO guides
            (name, phone, email, language, experience_years, status)
            VALUES
            (%s, %s, %s, %s, %s, %s)
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

    # --------------------------------------------------------
    # DEMO PLACES
    # --------------------------------------------------------

    place_count = query(
        "SELECT COUNT(*) AS total FROM places"
    )[0]["total"]

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

        for p in demo_places:
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
                p
            )


# ============================================================
# CONNECTION CHECK
# ============================================================

def check_database():

    try:

        conn = get_conn()

        with conn.cursor() as cursor:
            cursor.execute("SELECT VERSION() AS version")
            result = cursor.fetchone()

        conn.close()

        return True, result["version"]

    except Exception as e:

        return False, str(e)


# ============================================================
# INITIALIZE
# ============================================================

if MYSQL_CONFIG["password"] == "PASTE_PASSWORD_HERE":

    st.error(
        "🔐 Chưa nhập mật khẩu Aiven MySQL. "
        "Hãy mở app.py và thay PASTE_PASSWORD_HERE bằng mật khẩu Aiven của em."
    )

    st.stop()


db_ok, db_message = check_database()

if not db_ok:

    st.error("🔴 Không thể kết nối Aiven MySQL")

    st.code(db_message)

    st.warning(
        "Nếu lỗi là 1045 Access denied → kiểm tra lại password/user. "
        "Nếu lỗi timeout → kiểm tra host/port."
    )

    st.stop()


try:
    init_db()
except Exception as e:

    st.error("Không thể khởi tạo database.")

    st.code(str(e))

    st.stop()


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def format_date(value):

    if not value:
        return ""

    try:
        return pd.to_datetime(value).strftime("%d/%m/%Y")
    except:
        return str(value)


def status_badge(status):

    badges = {
        "Scheduled": "🟡 Đã lên lịch",
        "Confirmed": "🟢 Đã xác nhận",
        "Completed": "🔵 Hoàn thành",
        "Cancelled": "🔴 Đã hủy",
        "Open": "🔴 Đang xử lý",
        "Processing": "🟡 Đang xử lý",
        "Resolved": "🟢 Đã xử lý",
    }

    return badges.get(status, status)


def get_tours():

    return query(
        """
        SELECT
            t.*,
            g.name AS guide_name
        FROM tours t
        LEFT JOIN guides g
            ON t.guide_id = g.id
        ORDER BY t.start_date DESC, t.start_time ASC
        """
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
        ORDER BY t.start_time ASC
        """
    )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("🧭 TourMate")

    st.caption("Smart Tour Guide Management System")

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
            "⚙️ Cài đặt dữ liệu",
        ]
    )

    st.divider()

    st.success("🟢 MySQL Connected")

    st.caption(
        f"MySQL: {db_message}"
    )


# ============================================================
# DASHBOARD
# ============================================================

if menu == "🏠 Dashboard":

    st.title("🏠 Dashboard")

    st.markdown(
        "### Xin chào 👋 Chào mừng đến với **TourMate**"
    )

    st.caption(
        "Hệ thống quản lý công việc dành cho hướng dẫn viên du lịch."
    )

    today = date.today()

    # --------------------------------------------------------
    # METRICS
    # --------------------------------------------------------

    tour_today = query(
        """
        SELECT COUNT(*) AS total
        FROM tours
        WHERE start_date <= %s
        AND end_date >= %s
        """,
        (today, today)
    )[0]["total"]

    guests_today = query(
        """
        SELECT COUNT(*) AS total
        FROM guests g
        INNER JOIN tours t
            ON g.tour_id = t.id
        WHERE t.start_date <= %s
        AND t.end_date >= %s
        """,
        (today, today)
    )[0]["total"]

    tasks_today = query(
        """
        SELECT COUNT(*) AS total
        FROM tasks
        WHERE due_date = %s
        """,
        (today,)
    )[0]["total"]

    open_incidents = query(
        """
        SELECT COUNT(*) AS total
        FROM incidents
        WHERE status != 'Resolved'
        """
    )[0]["total"]

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
        "🚨 Sự cố đang xử lý",
        open_incidents
    )

    st.divider()

    # --------------------------------------------------------
    # TODAY TOURS
    # --------------------------------------------------------

    st.subheader("📅 Công việc hôm nay")

    today_tours = get_today_tours()

    if len(today_tours) == 0:

        st.info(
            "🎉 Hôm nay chưa có tour nào được phân công."
        )

    else:

        for tour in today_tours:

            with st.container(border=True):

                col1, col2, col3 = st.columns([2, 2, 1])

                with col1:

                    st.markdown(
                        f"### 🚌 {tour['name']}"
                    )

                    st.write(
                        f"**Mã tour:** {tour['code']}"
                    )

                    st.write(
                        f"👨‍✈️ HDV: {tour['guide_name'] or 'Chưa phân công'}"
                    )

                with col2:

                    st.write(
                        f"🕐 **Giờ đón:** {tour['start_time'] or '--'}"
                    )

                    st.write(
                        f"📍 **Điểm đón:** {tour['pickup_location'] or '--'}"
                    )

                    st.write(
                        f"🏨 **Khách sạn:** {tour['hotel'] or '--'}"
                    )

                with col3:

                    st.metric(
                        "👥 Khách",
                        tour["total_guests"] or 0
                    )

                    st.write(
                        status_badge(tour["status"])
                    )

    st.divider()

    # --------------------------------------------------------
    # TODAY TASKS
    # --------------------------------------------------------

    st.subheader("✅ Checklist hôm nay")

    tasks = query(
        """
        SELECT *
        FROM tasks
        WHERE due_date = %s
        ORDER BY done ASC, due_time ASC
        """,
        (today,)
    )

    if not tasks:

        st.info("Không có checklist cho hôm nay.")

    else:

        for task in tasks:

            checked = st.checkbox(
                task["task_name"],
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
                    (1 if checked else 0, task["id"])
                )

                st.rerun()


# ============================================================
# TOUR CALENDAR
# ============================================================

elif menu == "📅 Lịch tour":

    st.title("📅 Lịch tour")

    col1, col2 = st.columns(2)

    with col1:

        selected_month = st.date_input(
            "Chọn tháng",
            value=date.today().replace(day=1)
        )

    with col2:

        guide_filter = st.selectbox(
            "Lọc hướng dẫn viên",
            ["Tất cả"]
            + [
                g["name"]
                for g in query(
                    "SELECT name FROM guides ORDER BY name"
                )
            ]
        )

    month_string = selected_month.strftime("%Y-%m")

    sql = """
        SELECT
            t.code,
            t.name,
            t.start_date,
            t.end_date,
            t.start_time,
            t.pickup_location,
            t.total_guests,
            t.status,
            g.name AS guide_name
        FROM tours t
        LEFT JOIN guides g
            ON t.guide_id = g.id
        WHERE DATE_FORMAT(t.start_date, '%%Y-%%m') = %s
    """

    params = [month_string]

    if guide_filter != "Tất cả":

        sql += " AND g.name = %s"
        params.append(guide_filter)

    sql += """
        ORDER BY t.start_date, t.start_time
    """

    df = query_df(sql, tuple(params))

    if df.empty:

        st.info("Chưa có tour trong tháng này.")

    else:

        df["start_date"] = df["start_date"].apply(format_date)
        df["end_date"] = df["end_date"].apply(format_date)

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

    # --------------------------------------------------------
    # TOUR LIST
    # --------------------------------------------------------

    with tab1:

        tours = query(
            """
            SELECT
                t.*,
                g.name AS guide_name
            FROM tours t
            LEFT JOIN guides g
                ON t.guide_id = g.id
            ORDER BY t.start_date DESC
            """
        )

        if not tours:

            st.info("Chưa có tour.")

        else:

            for tour in tours:

                with st.expander(
                    f"🚌 {tour['code']} - {tour['name']}"
                ):

                    c1, c2, c3 = st.columns(3)

                    c1.write(
                        f"📅 {format_date(tour['start_date'])} → "
                        f"{format_date(tour['end_date'])}"
                    )

                    c2.write(
                        f"👨‍✈️ HDV: "
                        f"{tour['guide_name'] or 'Chưa phân công'}"
                    )

                    c3.write(
                        f"👥 {tour['total_guests'] or 0} khách"
                    )

                    st.write(
                        f"🕐 Giờ đón: {tour['start_time'] or '--'}"
                    )

                    st.write(
                        f"📍 Điểm đón: {tour['pickup_location'] or '--'}"
                    )

                    st.write(
                        f"🏨 Khách sạn: {tour['hotel'] or '--'}"
                    )

                    st.write(
                        f"🚌 Phương tiện: {tour['vehicle'] or '--'}"
                    )

                    st.write(
                        f"👨‍✈️ Tài xế: {tour['driver'] or '--'}"
                    )

                    st.write(
                        status_badge(tour["status"])
                    )

                    if tour["notes"]:

                        st.info(
                            f"📝 {tour['notes']}"
                        )

                    if st.button(
                        "🗑️ Xóa tour",
                        key=f"delete_tour_{tour['id']}"
                    ):

                        execute(
                            "DELETE FROM tours WHERE id=%s",
                            (tour["id"],)
                        )

                        st.success("Đã xóa tour.")

                        st.rerun()

    # --------------------------------------------------------
    # CREATE TOUR
    # --------------------------------------------------------

    with tab2:

        st.subheader("➕ Tạo tour mới")

        guides = query(
            """
            SELECT id, name
            FROM guides
            WHERE status='Active'
            ORDER BY name
            """
        )

        with st.form("create_tour_form"):

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

                guide_options = {
                    "Chưa phân công": None
                }

                for g in guides:
                    guide_options[
                        g["name"]
                    ] = g["id"]

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

                if not code.strip():

                    st.error("Vui lòng nhập mã tour.")

                elif not name.strip():

                    st.error("Vui lòng nhập tên tour.")

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
                                code.strip(),
                                name.strip(),
                                guide_options[guide_name],
                                start_date,
                                end_date,
                                start_time.strftime("%H:%M"),
                                pickup,
                                hotel,
                                vehicle,
                                driver,
                                total_guests,
                                status,
                                notes
                            )
                        )

                        st.success(
                            "🎉 Tạo tour thành công!"
                        )

                        st.rerun()

                    except pymysql.err.IntegrityError:

                        st.error(
                            "Mã tour đã tồn tại. Hãy sử dụng mã khác."
                        )


# ============================================================
# ITINERARY
# ============================================================

elif menu == "🗺️ Lịch trình":

    st.title("🗺️ Lịch trình tour")

    tours = query(
        """
        SELECT id, code, name, start_date, end_date
        FROM tours
        ORDER BY start_date DESC
        """
    )

    if not tours:

        st.info(
            "Chưa có tour. Hãy tạo tour trước."
        )

    else:

        tour_map = {
            f"{t['code']} - {t['name']}": t["id"]
            for t in tours
        }

        selected_tour_name = st.selectbox(
            "Chọn tour",
            list(tour_map.keys())
        )

        selected_tour_id = tour_map[selected_tour_name]

        st.divider()

        itinerary = query(
            """
            SELECT *
            FROM itinerary
            WHERE tour_id=%s
            ORDER BY tour_date, time, id
            """,
            (selected_tour_id,)
        )

        st.subheader("📍 Lịch trình hiện tại")

        if not itinerary:

            st.info(
                "Tour này chưa có lịch trình."
            )

        else:

            for item in itinerary:

                with st.container(border=True):

                    c1, c2, c3 = st.columns([1, 2, 1])

                    c1.write(
                        f"📅 {format_date(item['tour_date'])}"
                    )

                    c2.markdown(
                        f"### {item['place']}"
                    )

                    c2.write(
                        item["activity"] or ""
                    )

                    c3.write(
                        f"🕐 {item['time'] or '--'}"
                    )

                    if item["transport"]:

                        st.write(
                            f"🚌 Phương tiện: {item['transport']}"
                        )

                    if item["notes"]:

                        st.write(
                            f"📝 {item['notes']}"
                        )

                    if st.button(
                        "🗑️ Xóa",
                        key=f"delete_itinerary_{item['id']}"
                    ):

                        execute(
                            "DELETE FROM itinerary WHERE id=%s",
                            (item["id"],)
                        )

                        st.rerun()

        st.divider()

        st.subheader("➕ Thêm điểm vào lịch trình")

        with st.form("add_itinerary"):

            c1, c2 = st.columns(2)

            with c1:

                itinerary_date = st.date_input(
                    "Ngày",
                    value=date.today()
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
                        "Vui lòng nhập điểm đến."
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
                        VALUES (%s,%s,%s,%s,%s,%s,%s)
                        """,
                        (
                            selected_tour_id,
                            itinerary_date,
                            itinerary_time.strftime("%H:%M"),
                            place,
                            activity,
                            transport,
                            notes
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

        tour_map = {
            f"{t['code']} - {t['name']}": t["id"]
            for t in tours
        }

        selected = st.selectbox(
            "Chọn tour",
            list(tour_map.keys())
        )

        tour_id = tour_map[selected]

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

            # ------------------------------------------------
            # ATTENDANCE
            # ------------------------------------------------

            st.subheader("📋 Điểm danh")

            for guest in guests:

                status_options = [
                    "Chưa điểm danh",
                    "Có mặt",
                    "Vắng",
                    "Đã xác nhận"
                ]

                current = guest["attendance"]

                if current not in status_options:
                    current = "Chưa điểm danh"

                new_status = st.selectbox(
                    guest["full_name"],
                    status_options,
                    index=status_options.index(current),
                    key=f"attendance_{guest['id']}"
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

        else:

            st.info(
                "Chưa có khách trong tour này."
            )

        st.divider()

        st.subheader("➕ Thêm khách")

        with st.form("add_guest"):

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
                        "Vui lòng nhập họ tên khách."
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
                            full_name,
                            gender,
                            age,
                            nationality,
                            phone,
                            room_number,
                            special_request,
                            guest_notes
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
                f"%{search}%",
                f"%{search}%",
                f"%{search}%"
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

    for place in places:

        with st.expander(
            f"📍 {place['name']} - {place['location'] or ''}"
        ):

            if place["image_url"]:

                try:
                    st.image(
                        place["image_url"],
                        use_container_width=True
                    )
                except:
                    pass

            st.markdown(
                "### 🎤 Giới thiệu"
            )

            st.write(
                place["introduction"] or "Chưa có nội dung."
            )

            st.markdown(
                "### 📚 Lịch sử"
            )

            st.write(
                place["history"] or "Chưa có nội dung."
            )

            st.markdown(
                "### ⭐ Điểm nổi bật"
            )

            st.write(
                place["highlights"] or "Chưa có nội dung."
            )

            st.markdown(
                "### 💡 Lưu ý cho HDV"
            )

            st.write(
                place["tips"] or "Chưa có nội dung."
            )

            if st.button(
                "🗑️ Xóa điểm",
                key=f"delete_place_{place['id']}"
            ):

                execute(
                    "DELETE FROM places WHERE id=%s",
                    (place["id"],)
                )

                st.rerun()

    st.divider()

    st.subheader(
        "➕ Thêm điểm thuyết minh"
    )

    with st.form("add_place"):

        name = st.text_input(
            "Tên điểm đến *"
        )

        location = st.text_input(
            "Địa điểm"
        )

        category = st.text_input(
            "Loại điểm"
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

        image_url = st.text_input(
            "URL hình ảnh"
        )

        submit = st.form_submit_button(
            "💾 LƯU ĐIỂM ĐẾN",
            type="primary"
        )

        if submit:

            if not name.strip():

                st.error(
                    "Vui lòng nhập tên điểm đến."
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
                        image_url
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

    st.title("✅ Checklist hướng dẫn viên")

    tours = query(
        """
        SELECT id, code, name
        FROM tours
        ORDER BY start_date DESC
        """
    )

    tour_map = {
        "Không gắn với tour": None
    }

    for t in tours:

        tour_map[
            f"{t['code']} - {t['name']}"
        ] = t["id"]

    selected_tour = st.selectbox(
        "Tour",
        list(tour_map.keys())
    )

    selected_tour_id = tour_map[selected_tour]

    tasks = query(
        """
        SELECT
            t.*,
            tr.code AS tour_code
        FROM tasks t
        LEFT JOIN tours tr
            ON t.tour_id = tr.id
        ORDER BY t.done ASC, t.due_date, t.due_time
        """
    )

    st.subheader("📋 Danh sách checklist")

    if not tasks:

        st.info(
            "Chưa có checklist."
        )

    else:

        for task in tasks:

            col1, col2, col3 = st.columns([5, 2, 1])

            with col1:

                checked = st.checkbox(
                    task["task_name"],
                    value=bool(task["done"]),
                    key=f"task_{task['id']}"
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

            with col2:

                st.caption(
                    f"{task['due_date'] or ''} "
                    f"{task['due_time'] or ''}"
                )

            with col3:

                if st.button(
                    "🗑️",
                    key=f"delete_task_{task['id']}"
                ):

                    execute(
                        "DELETE FROM tasks WHERE id=%s",
                        (task["id"],)
                    )

                    st.rerun()

    st.divider()

    st.subheader(
        "➕ Thêm checklist"
    )

    with st.form("add_task"):

        task_name = st.text_input(
            "Tên công việc *",
            placeholder="VD: Kiểm tra danh sách khách"
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
                        selected_tour_id,
                        task_name,
                        task_type,
                        due_date,
                        due_time.strftime("%H:%M"),
                        assigned_to,
                        task_notes
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

    st.title("🚨 Quản lý sự cố")

    tours = query(
        """
        SELECT id, code, name
        FROM tours
        ORDER BY start_date DESC
        """
    )

    tour_map = {
        "Không gắn với tour": None
    }

    for t in tours:

        tour_map[
            f"{t['code']} - {t['name']}"
        ] = t["id"]

    selected_tour = st.selectbox(
        "Tour liên quan",
        list(tour_map.keys())
    )

    selected_tour_id = tour_map[selected_tour]

    st.subheader("📋 Sự cố")

    incidents = query(
        """
        SELECT
            i.*,
            t.code AS tour_code,
            t.name AS tour_name
        FROM incidents i
        LEFT JOIN tours t
            ON i.tour_id=t.id
        ORDER BY i.incident_date DESC, i.id DESC
        """
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
                f"{status_icon} {incident['title']}"
            ):

                st.write(
                    f"📅 {format_date(incident['incident_date'])}"
                )

                st.write(
                    f"🕐 {incident['incident_time'] or '--'}"
                )

                st.write(
                    f"🏷️ Loại: {incident['type'] or '--'}"
                )

                st.write(
                    f"🚌 Tour: {incident['tour_code'] or '--'}"
                )

                st.write(
                    f"📋 Mô tả: {incident['description'] or '--'}"
                )

                st.write(
                    f"🔧 Xử lý: {incident['solution'] or '--'}"
                )

                new_status = st.selectbox(
                    "Trạng thái",
                    [
                        "Open",
                        "Processing",
                        "Resolved"
                    ],
                    index=[
                        "Open",
                        "Processing",
                        "Resolved"
                    ].index(
                        incident["status"]
                    )
                    if incident["status"] in [
                        "Open",
                        "Processing",
                        "Resolved"
                    ]
                    else 0,
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
                        "DELETE FROM incidents WHERE id=%s",
                        (incident["id"],)
                    )

                    st.rerun()

    st.divider()

    st.subheader(
        "➕ Báo cáo sự cố"
    )

    with st.form("add_incident"):

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
                    "Vui lòng nhập tên sự cố."
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
                        incident_time.strftime("%H:%M"),
                        incident_type,
                        title,
                        description,
                        solution,
                        created_by
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

    st.title("👨‍✈️ Quản lý hướng dẫn viên")

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
            "name",
            "phone",
            "email",
            "language",
            "experience_years",
            "status"
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

    with st.form("add_guide"):

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
            "➕ THÊM HDV",
            type="primary"
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

    st.title("⚙️ Cài đặt dữ liệu")

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
        ("🚨 Sự cố", "incidents"),
    ]

    cols = st.columns(4)

    for index, (label, table) in enumerate(tables):

        count = query(
            f"SELECT COUNT(*) AS total FROM {table}"
        )[0]["total"]

        cols[index % 4].metric(
            label,
            count
        )

    st.divider()

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
                f"🟢 MySQL hoạt động. Version: {result}"
            )

        else:

            st.error(
                "🔴 Không kết nối được MySQL"
            )

            st.code(result)

    st.divider()

    st.caption(
        "TourMate – Smart Tour Guide Management System"
    )

    st.caption(
        "Designed for tourism & travel guide operations."
    )
