import streamlit as st
import pymysql
from pymysql.cursors import DictCursor
from datetime import datetime, date
import pandas as pd


# =========================================================
# TOURMATE – SMART TOUR GUIDE MANAGEMENT SYSTEM
# Streamlit + MySQL
# =========================================================

st.set_page_config(
    page_title="TourMate",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# MYSQL CONFIGURATION
# =========================================================
#
# KHÔNG ghi password trực tiếp vào code.
#
# Tạo file:
#
# .streamlit/secrets.toml
#
# với:
#
# [mysql]
# host = "your-aiven-host"
# port = 27942
# user = "avnadmin"
# password = "YOUR_PASSWORD"
# database = "defaultdb"
#
# =========================================================


# =========================================================
# MYSQL CONFIGURATION
# =========================================================

MYSQL_CONFIG = {
    "host": "mysql-19728385-npmaihuong-927f.b.aivencloud.com",
    "port": 27942,
    "user": "avnadmin",
    "password": "AVNS_zBDlzsF9I5fC-EdWcl0",
    "database": "defaultdb",
}


def get_db_config():
    return MYSQL_CONFIG


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_conn():
    config = get_db_config()

    return pymysql.connect(
        host=config["host"],
        port=config["port"],
        user=config["user"],
        password=config["password"],
        database=config["database"],
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=False,
        connect_timeout=15,
    )


# =========================================================
# EXECUTE SQL
# =========================================================

def execute(sql, params=(), fetch=False, many=False):
    """
    Thực hiện INSERT / UPDATE / DELETE / SELECT.
    """

    conn = None

    try:
        conn = get_conn()

        with conn.cursor() as cur:

            if many:
                cur.executemany(sql, params)
            else:
                cur.execute(sql, params)

            if fetch:
                result = cur.fetchall()
                conn.close()
                return result

            conn.commit()

            last_id = cur.lastrowid

            conn.close()

            return last_id

    except Exception as e:

        if conn:
            conn.rollback()
            conn.close()

        raise e


# =========================================================
# QUERY DATAFRAME
# =========================================================

def query_df(sql, params=()):
    """
    Chạy SELECT và trả về Pandas DataFrame.
    """

    conn = None

    try:
        conn = get_conn()

        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

        conn.close()

        return pd.DataFrame(rows)

    except Exception as e:

        if conn:
            conn.close()

        raise e


# =========================================================
# INITIALIZE DATABASE
# =========================================================

def init_db():

    conn = None

    try:
        conn = get_conn()

        with conn.cursor() as c:

            # -------------------------------------------------
            # GUIDES
            # -------------------------------------------------

            c.execute("""
                CREATE TABLE IF NOT EXISTS guides (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    phone VARCHAR(50),
                    email VARCHAR(255),
                    role VARCHAR(100) DEFAULT 'Guide'
                ) ENGINE=InnoDB
                DEFAULT CHARSET=utf8mb4
                COLLATE=utf8mb4_unicode_ci
            """)

            # -------------------------------------------------
            # TOURS
            # -------------------------------------------------

            c.execute("""
                CREATE TABLE IF NOT EXISTS tours (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    code VARCHAR(100) UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    guide_id INT NULL,
                    driver VARCHAR(255),
                    vehicle VARCHAR(255),
                    guests INT DEFAULT 0,
                    pickup VARCHAR(500),
                    hotel VARCHAR(500),
                    status VARCHAR(50) DEFAULT 'Upcoming',
                    notes TEXT,

                    CONSTRAINT fk_tours_guide
                    FOREIGN KEY (guide_id)
                    REFERENCES guides(id)
                    ON DELETE SET NULL
                    ON UPDATE CASCADE
                ) ENGINE=InnoDB
                DEFAULT CHARSET=utf8mb4
                COLLATE=utf8mb4_unicode_ci
            """)

            # -------------------------------------------------
            # ITINERARY
            # -------------------------------------------------

            c.execute("""
                CREATE TABLE IF NOT EXISTS itinerary (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    tour_id INT NOT NULL,
                    tour_date DATE NOT NULL,
                    time VARCHAR(10) NOT NULL,
                    location VARCHAR(500) NOT NULL,
                    activity VARCHAR(500),
                    duration VARCHAR(100),
                    restaurant VARCHAR(500),
                    notes TEXT,

                    CONSTRAINT fk_itinerary_tour
                    FOREIGN KEY (tour_id)
                    REFERENCES tours(id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE
                ) ENGINE=InnoDB
                DEFAULT CHARSET=utf8mb4
                COLLATE=utf8mb4_unicode_ci
            """)

            # -------------------------------------------------
            # GUESTS
            # -------------------------------------------------

            c.execute("""
                CREATE TABLE IF NOT EXISTS guests (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    tour_id INT NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    phone VARCHAR(50),
                    room VARCHAR(100),
                    dietary VARCHAR(500),
                    note TEXT,
                    checked_in TINYINT(1) DEFAULT 0,

                    CONSTRAINT fk_guests_tour
                    FOREIGN KEY (tour_id)
                    REFERENCES tours(id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE
                ) ENGINE=InnoDB
                DEFAULT CHARSET=utf8mb4
                COLLATE=utf8mb4_unicode_ci
            """)

            # -------------------------------------------------
            # TASKS
            # -------------------------------------------------

            c.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    tour_id INT NULL,
                    task VARCHAR(500) NOT NULL,
                    due_date DATE,
                    done TINYINT(1) DEFAULT 0,

                    CONSTRAINT fk_tasks_tour
                    FOREIGN KEY (tour_id)
                    REFERENCES tours(id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE
                ) ENGINE=InnoDB
                DEFAULT CHARSET=utf8mb4
                COLLATE=utf8mb4_unicode_ci
            """)

            # -------------------------------------------------
            # PLACES
            # -------------------------------------------------

            c.execute("""
                CREATE TABLE IF NOT EXISTS places (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    category VARCHAR(255),
                    description TEXT,
                    script TEXT,
                    phone VARCHAR(100),
                    note TEXT
                ) ENGINE=InnoDB
                DEFAULT CHARSET=utf8mb4
                COLLATE=utf8mb4_unicode_ci
            """)

            # -------------------------------------------------
            # INCIDENTS
            # -------------------------------------------------

            c.execute("""
                CREATE TABLE IF NOT EXISTS incidents (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    tour_id INT NULL,
                    incident_date DATE NOT NULL,
                    incident_type VARCHAR(255) NOT NULL,
                    description TEXT NOT NULL,
                    action_taken TEXT,
                    status VARCHAR(50) DEFAULT 'Open',

                    CONSTRAINT fk_incidents_tour
                    FOREIGN KEY (tour_id)
                    REFERENCES tours(id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE
                ) ENGINE=InnoDB
                DEFAULT CHARSET=utf8mb4
                COLLATE=utf8mb4_unicode_ci
            """)

            # =================================================
            # DEMO GUIDE
            # =================================================

            c.execute("SELECT COUNT(*) AS total FROM guides")

            guide_count = c.fetchone()["total"]

            if guide_count == 0:

                c.execute("""
                    INSERT INTO guides
                    (name, phone, email, role)
                    VALUES (%s, %s, %s, %s)
                """, (
                    "Nguyễn Thị Hương",
                    "0900000000",
                    "huong@example.com",
                    "Tour Guide"
                ))

            # =================================================
            # DEMO PLACES
            # =================================================

            c.execute("SELECT COUNT(*) AS total FROM places")

            place_count = c.fetchone()["total"]

            if place_count == 0:

                demo_places = [

                    (
                        "Tháp Tam Thắng",
                        "Điểm tham quan",
                        "Điểm tham quan nổi bật tại Vũng Tàu.",
                        "Xin chào quý khách! Hiện tại đoàn đang có mặt tại Tháp Tam Thắng...",
                        "",
                        "Kiểm tra thời gian tham quan và điểm tập trung."
                    ),

                    (
                        "Bãi Sau Vũng Tàu",
                        "Biển",
                        "Khu vực biển nổi tiếng của Vũng Tàu.",
                        "Kính mời quý khách cùng ngắm biển và tự do chụp ảnh...",
                        "",
                        "Nhắc khách giữ đồ cá nhân."
                    ),

                    (
                        "Chợ Đà Lạt",
                        "Mua sắm",
                        "Khu mua sắm và trải nghiệm ẩm thực.",
                        "Chợ Đà Lạt là một trong những điểm mua sắm quen thuộc...",
                        "",
                        "Quy định giờ tập trung."
                    )
                ]

                c.executemany("""
                    INSERT INTO places
                    (name, category, description, script, phone, note)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, demo_places)

            conn.commit()

        conn.close()

    except Exception as e:

        if conn:
            conn.rollback()
            conn.close()

        st.error("❌ Không thể khởi tạo MySQL database.")
        st.exception(e)
        st.stop()


# =========================================================
# START DATABASE
# =========================================================

init_db()


# =========================================================
# HELPERS
# =========================================================

def today_str():
    return date.today().isoformat()


def fmt_date(value):

    if not value:
        return ""

    if isinstance(value, (datetime, date)):
        return value.strftime("%d/%m/%Y")

    try:
        return datetime.strptime(
            str(value),
            "%Y-%m-%d"
        ).strftime("%d/%m/%Y")

    except Exception:
        return str(value)


def status_badge(status):

    mapping = {
        "Upcoming": "🟡",
        "In Progress": "🟢",
        "Completed": "🔵",
        "Cancelled": "🔴",
        "Open": "🔴",
        "Resolved": "🟢",
    }

    return f"{mapping.get(status, '⚪')} {status}"


# =========================================================
# CSS
# =========================================================

st.markdown("""
<style>

.main-title {
    font-size: 2.4rem;
    font-weight: 800;
    margin-bottom: 0;
}

.subtitle {
    color: #667085;
    margin-top: 0;
}

.metric-card {
    border: 1px solid #e5e7eb;
    border-radius: 16px;
    padding: 18px;
    background: white;
}

.small-muted {
    color: #667085;
    font-size: 0.9rem;
}

.tour-card {
    border: 1px solid #e5e7eb;
    border-radius: 16px;
    padding: 18px;
    margin-bottom: 12px;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.markdown("# 🧭 TourMate")
st.sidebar.caption("Smart Tour Guide Management System")

menu = st.sidebar.radio(
    "MENU",
    [
        "🏠 Dashboard",
        "📅 Lịch tour",
        "🚌 Quản lý tour",
        "🗺️ Lịch trình",
        "👥 Khách du lịch",
        "🎤 Kho thuyết minh",
        "📝 Checklist",
        "🚨 Sự cố",
        "⚙️ Cài đặt dữ liệu",
    ]
)

st.sidebar.markdown("---")
st.sidebar.caption(
    f"📅 Hôm nay: {date.today().strftime('%d/%m/%Y')}"
)
st.sidebar.caption("TourMate v1.0")


# =========================================================
# DASHBOARD
# =========================================================

if menu == "🏠 Dashboard":

    st.markdown(
        '<p class="main-title">🧭 TourMate</p>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<p class="subtitle">Trợ lý số dành cho hướng dẫn viên du lịch</p>',
        unsafe_allow_html=True
    )

    tours = query_df("""
        SELECT
            t.*,
            g.name AS guide_name
        FROM tours t
        LEFT JOIN guides g
            ON t.guide_id = g.id
        ORDER BY t.start_date ASC
    """)

    today = today_str()

    total_tours = len(tours)

    upcoming = (
        len(tours[tours["status"] == "Upcoming"])
        if not tours.empty
        else 0
    )

    active = (
        len(tours[tours["status"] == "In Progress"])
        if not tours.empty
        else 0
    )

    total_guests = (
        int(tours["guests"].sum())
        if not tours.empty
        else 0
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("🚌 Tổng tour", total_tours)
    c2.metric("🟡 Sắp diễn ra", upcoming)
    c3.metric("🟢 Đang chạy", active)
    c4.metric("👥 Tổng khách", total_guests)

    st.markdown("### 📌 Tour hôm nay")

    if not tours.empty:

        today_tours = tours[
            (tours["start_date"].astype(str) <= today) &
            (tours["end_date"].astype(str) >= today) &
            (tours["status"] != "Cancelled")
        ]

    else:
        today_tours = pd.DataFrame()

    if today_tours.empty:

        st.info("Hôm nay chưa có tour đang diễn ra.")

    else:

        for _, row in today_tours.iterrows():

            with st.container(border=True):

                a, b, c = st.columns([2, 2, 1])

                a.markdown(
                    f"### 🚌 {row['name']}"
                )

                a.write(
                    f"**Mã:** {row['code']}"
                )

                b.write(
                    f"📅 {fmt_date(row['start_date'])} → "
                    f"{fmt_date(row['end_date'])}"
                )

                b.write(
                    f"👥 {row['guests']} khách"
                )

                b.write(
                    f"📍 {row['pickup'] or 'Chưa cập nhật'}"
                )

                c.write(
                    status_badge(row["status"])
                )

                c.write(
                    f"👨‍🏫 {row['guide_name'] or 'Chưa phân công'}"
                )

    st.markdown("### 🔔 Việc cần làm")

    tasks = query_df("""
        SELECT
            tasks.*,
            tours.name AS tour_name
        FROM tasks
        LEFT JOIN tours
            ON tasks.tour_id = tours.id
        WHERE tasks.done = 0
        ORDER BY tasks.due_date ASC
        LIMIT 8
    """)

    if tasks.empty:

        st.success(
            "Không có việc chưa hoàn thành 🎉"
        )

    else:

        for _, t in tasks.iterrows():

            label = f"**{t['task']}**"

            if t["due_date"]:
                label += f" — {fmt_date(t['due_date'])}"

            if st.checkbox(
                label,
                key=f"dash_task_{t['id']}"
            ):

                execute(
                    "UPDATE tasks SET done=1 WHERE id=%s",
                    (int(t["id"]),)
                )

                st.rerun()


# =========================================================
# LỊCH TOUR
# =========================================================

elif menu == "📅 Lịch tour":

    st.title("📅 Lịch tour")

    tours = query_df("""
        SELECT
            t.id,
            t.code,
            t.name,
            t.start_date,
            t.end_date,
            t.guests,
            t.status,
            g.name AS guide_name
        FROM tours t
        LEFT JOIN guides g
            ON t.guide_id = g.id
        ORDER BY t.start_date
    """)

    if tours.empty:

        st.info("Chưa có tour.")

    else:

        selected_month = st.date_input(
            "Chọn tháng",
            value=date.today()
        )

        month_prefix = selected_month.strftime("%Y-%m")

        month_tours = tours[
            tours["start_date"]
            .astype(str)
            .str.startswith(month_prefix)
        ]

        if month_tours.empty:

            st.info("Tháng này chưa có tour.")

        else:

            for _, row in month_tours.iterrows():

                with st.container(border=True):

                    st.markdown(
                        f"### 🚌 {row['name']}"
                    )

                    c1, c2, c3, c4 = st.columns(4)

                    c1.write(
                        f"**Mã:** {row['code']}"
                    )

                    c2.write(
                        f"📅 {fmt_date(row['start_date'])} → "
                        f"{fmt_date(row['end_date'])}"
                    )

                    c3.write(
                        f"👥 {row['guests']} khách"
                    )

                    c4.write(
                        status_badge(row["status"])
                    )

                    st.caption(
                        f"HDV: {row['guide_name'] or 'Chưa phân công'}"
                    )


# =========================================================
# QUẢN LÝ TOUR
# =========================================================

elif menu == "🚌 Quản lý tour":

    st.title("🚌 Quản lý tour")

    tab1, tab2 = st.tabs(
        ["📋 Danh sách", "➕ Tạo tour"]
    )

    # -----------------------------------------------------
    # DANH SÁCH
    # -----------------------------------------------------

    with tab1:

        tours = query_df("""
            SELECT
                t.id,
                t.code,
                t.name,
                t.start_date,
                t.end_date,
                t.guests,
                t.pickup,
                t.hotel,
                t.status,
                g.name AS guide_name
            FROM tours t
            LEFT JOIN guides g
                ON t.guide_id = g.id
            ORDER BY t.start_date DESC
        """)

        if tours.empty:

            st.info("Chưa có tour.")

        else:

            st.dataframe(
                tours.rename(
                    columns={
                        "id": "ID",
                        "code": "Mã tour",
                        "name": "Tên tour",
                        "start_date": "Ngày đi",
                        "end_date": "Ngày về",
                        "guests": "Số khách",
                        "pickup": "Điểm đón",
                        "hotel": "Khách sạn",
                        "status": "Trạng thái",
                        "guide_name": "HDV",
                    }
                ),
                use_container_width=True,
                hide_index=True
            )

            st.markdown("#### 🗑️ Xóa tour")

            options = {
                f"{r['code']} — {r['name']}":
                    r["id"]
                for _, r in tours.iterrows()
            }

            selected = st.selectbox(
                "Chọn tour",
                list(options.keys())
            )

            if st.button(
                "🗑️ Xóa tour",
                type="secondary"
            ):

                execute(
                    "DELETE FROM tours WHERE id=%s",
                    (int(options[selected]),)
                )

                st.success("Đã xóa tour.")

                st.rerun()

    # -----------------------------------------------------
    # TẠO TOUR
    # -----------------------------------------------------

    with tab2:

        guides = query_df(
            "SELECT * FROM guides ORDER BY name"
        )

        with st.form("create_tour"):

            code = st.text_input(
                "Mã tour *",
                placeholder="VT2N1D01"
            )

            name = st.text_input(
                "Tên tour *",
                placeholder="Vũng Tàu 2N1Đ"
            )

            c1, c2 = st.columns(2)

            start = c1.date_input(
                "Ngày bắt đầu",
                date.today()
            )

            end = c2.date_input(
                "Ngày kết thúc",
                date.today()
            )

            c3, c4 = st.columns(2)

            guests = c3.number_input(
                "Số khách",
                min_value=0,
                value=20
            )

            guide_options = (
                ["-- Chưa phân công --"] +
                guides["name"].tolist()
                if not guides.empty
                else ["-- Chưa phân công --"]
            )

            guide_name = c4.selectbox(
                "Hướng dẫn viên",
                guide_options
            )

            pickup = st.text_input(
                "Điểm đón"
            )

            hotel = st.text_input(
                "Khách sạn"
            )

            driver = st.text_input(
                "Tài xế"
            )

            vehicle = st.text_input(
                "Xe"
            )

            status = st.selectbox(
                "Trạng thái",
                [
                    "Upcoming",
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
                type="primary"
            )

            if submitted:

                if not code.strip() or not name.strip():

                    st.error(
                        "Vui lòng nhập mã tour và tên tour."
                    )

                elif end < start:

                    st.error(
                        "Ngày kết thúc không được trước ngày bắt đầu."
                    )

                else:

                    guide_id = None

                    if (
                        guide_name !=
                        "-- Chưa phân công --"
                    ):

                        guide_id = int(
                            guides.loc[
                                guides["name"] == guide_name,
                                "id"
                            ].iloc[0]
                        )

                    try:

                        execute("""
                            INSERT INTO tours
                            (
                                code,
                                name,
                                start_date,
                                end_date,
                                guide_id,
                                driver,
                                vehicle,
                                guests,
                                pickup,
                                hotel,
                                status,
                                notes
                            )
                            VALUES
                            (
                                %s, %s, %s, %s,
                                %s, %s, %s, %s,
                                %s, %s, %s, %s
                            )
                        """, (
                            code.strip(),
                            name.strip(),
                            start,
                            end,
                            guide_id,
                            driver,
                            vehicle,
                            guests,
                            pickup,
                            hotel,
                            status,
                            notes
                        ))

                        st.success(
                            "Tạo tour thành công!"
                        )

                        st.rerun()

                    except pymysql.err.IntegrityError:

                        st.error(
                            "Mã tour đã tồn tại."
                        )


# =========================================================
# LỊCH TRÌNH
# =========================================================

elif menu == "🗺️ Lịch trình":

    st.title("🗺️ Lịch trình tour")

    tours = query_df("""
        SELECT id, code, name
        FROM tours
        ORDER BY start_date DESC
    """)

    if tours.empty:

        st.info(
            "Hãy tạo tour trước."
        )

    else:

        labels = {
            f"{r['code']} — {r['name']}":
                int(r["id"])
            for _, r in tours.iterrows()
        }

        selected = st.selectbox(
            "Chọn tour",
            list(labels.keys())
        )

        tour_id = labels[selected]

        itinerary = query_df("""
            SELECT
                id,
                tour_date,
                time,
                location,
                activity,
                duration,
                restaurant,
                notes
            FROM itinerary
            WHERE tour_id=%s
            ORDER BY tour_date, time
        """, (tour_id,))

        if not itinerary.empty:

            st.dataframe(
                itinerary.rename(
                    columns={
                        "id": "ID",
                        "tour_date": "Ngày",
                        "time": "Giờ",
                        "location": "Địa điểm",
                        "activity": "Hoạt động",
                        "duration": "Thời lượng",
                        "restaurant": "Nhà hàng",
                        "notes": "Ghi chú",
                    }
                ),
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info(
                "Tour này chưa có lịch trình."
            )

        st.markdown("---")

        st.subheader(
            "➕ Thêm điểm trong lịch trình"
        )

        with st.form("add_itinerary"):

            c1, c2 = st.columns(2)

            tour_date = c1.date_input(
                "Ngày",
                date.today()
            )

            time_value = c2.time_input(
                "Giờ",
                datetime.now().time().replace(
                    second=0,
                    microsecond=0
                )
            )

            location = st.text_input(
                "📍 Địa điểm *"
            )

            activity = st.text_input(
                "Hoạt động"
            )

            c3, c4 = st.columns(2)

            duration = c3.text_input(
                "Thời lượng",
                placeholder="90 phút"
            )

            restaurant = c4.text_input(
                "Nhà hàng"
            )

            notes = st.text_area(
                "Ghi chú"
            )

            submit = st.form_submit_button(
                "➕ Thêm vào lịch trình",
                type="primary"
            )

            if submit:

                if not location.strip():

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
                            location,
                            activity,
                            duration,
                            restaurant,
                            notes
                        )
                        VALUES
                        (
                            %s, %s, %s, %s,
                            %s, %s, %s, %s
                        )
                    """, (
                        tour_id,
                        tour_date,
                        time_value.strftime("%H:%M"),
                        location.strip(),
                        activity,
                        duration,
                        restaurant,
                        notes
                    ))

                    st.success(
                        "Đã thêm lịch trình."
                    )

                    st.rerun()


# =========================================================
# KHÁCH DU LỊCH
# =========================================================

elif menu == "👥 Khách du lịch":

    st.title("👥 Danh sách khách")

    tours = query_df("""
        SELECT id, code, name
        FROM tours
        ORDER BY start_date DESC
    """)

    if tours.empty:

        st.info("Chưa có tour.")

    else:

        labels = {
            f"{r['code']} — {r['name']}":
                int(r["id"])
            for _, r in tours.iterrows()
        }

        selected = st.selectbox(
            "Chọn tour",
            list(labels.keys())
        )

        tour_id = labels[selected]

        guests = query_df("""
            SELECT
                id,
                name,
                phone,
                room,
                dietary,
                note,
                checked_in
            FROM guests
            WHERE tour_id=%s
            ORDER BY name
        """, (tour_id,))

        total = len(guests)

        checked = (
            int(guests["checked_in"].sum())
            if not guests.empty
            else 0
        )

        c1, c2 = st.columns(2)

        c1.metric(
            "👥 Tổng khách",
            total
        )

        c2.metric(
            "✅ Đã điểm danh",
            checked
        )

        if not guests.empty:

            display_guests = guests.copy()

            display_guests["checked_in"] = (
                display_guests["checked_in"]
                .map({
                    0: "❌",
                    1: "✅"
                })
            )

            st.dataframe(
                display_guests.rename(
                    columns={
                        "id": "ID",
                        "name": "Họ tên",
                        "phone": "Điện thoại",
                        "room": "Phòng",
                        "dietary": "Ăn uống",
                        "note": "Ghi chú",
                        "checked_in": "Có mặt"
                    }
                ),
                use_container_width=True,
                hide_index=True
            )

        st.markdown("---")

        st.subheader("➕ Thêm khách")

        with st.form("add_guest"):

            name = st.text_input(
                "Họ tên *"
            )

            c1, c2 = st.columns(2)

            phone = c1.text_input(
                "Số điện thoại"
            )

            room = c2.text_input(
                "Phòng"
            )

            dietary = st.text_input(
                "Yêu cầu ăn uống / dị ứng"
            )

            note = st.text_area(
                "Ghi chú"
            )

            submit = st.form_submit_button(
                "➕ Thêm khách",
                type="primary"
            )

            if submit:

                if not name.strip():

                    st.error(
                        "Vui lòng nhập họ tên."
                    )

                else:

                    execute("""
                        INSERT INTO guests
                        (
                            tour_id,
                            name,
                            phone,
                            room,
                            dietary,
                            note
                        )
                        VALUES
                        (
                            %s, %s, %s,
                            %s, %s, %s
                        )
                    """, (
                        tour_id,
                        name.strip(),
                        phone,
                        room,
                        dietary,
                        note
                    ))

                    st.success(
                        "Đã thêm khách."
                    )

                    st.rerun()


# =========================================================
# KHO THUYẾT MINH
# =========================================================

elif menu == "🎤 Kho thuyết minh":

    st.title(
        "🎤 Kho nội dung thuyết minh"
    )

    places = query_df("""
        SELECT
            id,
            name,
            category,
            description,
            script,
            phone,
            note
        FROM places
        ORDER BY name
    """)

    if places.empty:

        st.info(
            "Chưa có điểm tham quan."
        )

    else:

        selected_name = st.selectbox(
            "📍 Chọn điểm tham quan",
            places["name"].tolist()
        )

        p = places[
            places["name"] == selected_name
        ].iloc[0]

        st.subheader(
            f"📍 {p['name']}"
        )

        st.caption(
            p["category"] or
            "Chưa phân loại"
        )

        c1, c2 = st.columns(2)

        with c1:

            st.markdown(
                "### ℹ️ Thông tin"
            )

            st.write(
                p["description"] or
                "Chưa có mô tả."
            )

            if p["phone"]:

                st.write(
                    f"📞 {p['phone']}"
                )

            st.info(
                p["note"] or
                "Không có lưu ý."
            )

        with c2:

            st.markdown(
                "### 🎤 Bài thuyết minh"
            )

            st.write(
                p["script"] or
                "Chưa có nội dung."
            )

    st.markdown("---")

    st.subheader(
        "➕ Thêm điểm tham quan"
    )

    with st.form("add_place"):

        name = st.text_input(
            "Tên điểm *"
        )

        category = st.text_input(
            "Loại điểm"
        )

        description = st.text_area(
            "Mô tả"
        )

        script = st.text_area(
            "Nội dung thuyết minh"
        )

        phone = st.text_input(
            "Số điện thoại liên hệ"
        )

        note = st.text_area(
            "Lưu ý"
        )

        submit = st.form_submit_button(
            "💾 Lưu điểm tham quan",
            type="primary"
        )

        if submit:

            if not name.strip():

                st.error(
                    "Vui lòng nhập tên điểm."
                )

            else:

                execute("""
                    INSERT INTO places
                    (
                        name,
                        category,
                        description,
                        script,
                        phone,
                        note
                    )
                    VALUES
                    (
                        %s, %s, %s,
                        %s, %s, %s
                    )
                """, (
                    name.strip(),
                    category,
                    description,
                    script,
                    phone,
                    note
                ))

                st.success(
                    "Đã thêm điểm tham quan."
                )

                st.rerun()


# =========================================================
# CHECKLIST
# =========================================================

elif menu == "📝 Checklist":

    st.title(
        "📝 Checklist tour"
    )

    tours = query_df("""
        SELECT id, code, name
        FROM tours
        ORDER BY start_date DESC
    """)

    if tours.empty:

        st.info(
            "Chưa có tour."
        )

    else:

        labels = {
            f"{r['code']} — {r['name']}":
                int(r["id"])
            for _, r in tours.iterrows()
        }

        selected = st.selectbox(
            "Chọn tour",
            list(labels.keys())
        )

        tour_id = labels[selected]

        tasks = query_df("""
            SELECT
                id,
                task,
                due_date,
                done
            FROM tasks
            WHERE tour_id=%s
            ORDER BY done, due_date
        """, (tour_id,))

        if tasks.empty:

            st.info(
                "Chưa có checklist cho tour này."
            )

        else:

            for _, task in tasks.iterrows():

                checked = bool(
                    task["done"]
                )

                new_value = st.checkbox(
                    f"{'✅' if checked else '⬜'} "
                    f"{task['task']}",
                    value=checked,
                    key=f"task_{task['id']}"
                )

                if new_value != checked:

                    execute(
                        """
                        UPDATE tasks
                        SET done=%s
                        WHERE id=%s
                        """,
                        (
                            1 if new_value else 0,
                            int(task["id"])
                        )
                    )

                    st.rerun()

        st.markdown("---")

        with st.form("add_task"):

            task_name = st.text_input(
                "Việc cần làm *"
            )

            due = st.date_input(
                "Hạn hoàn thành",
                date.today()
            )

            submit = st.form_submit_button(
                "➕ Thêm checklist",
                type="primary"
            )

            if submit:

                if not task_name.strip():

                    st.error(
                        "Vui lòng nhập công việc."
                    )

                else:

                    execute("""
                        INSERT INTO tasks
                        (
                            tour_id,
                            task,
                            due_date
                        )
                        VALUES
                        (
                            %s, %s, %s
                        )
                    """, (
                        tour_id,
                        task_name.strip(),
                        due
                    ))

                    st.success(
                        "Đã thêm checklist."
                    )

                    st.rerun()


# =========================================================
# SỰ CỐ
# =========================================================

elif menu == "🚨 Sự cố":

    st.title(
        "🚨 Báo cáo sự cố"
    )

    tours = query_df("""
        SELECT id, code, name
        FROM tours
        ORDER BY start_date DESC
    """)

    if tours.empty:

        st.info(
            "Chưa có tour."
        )

    else:

        labels = {
            f"{r['code']} — {r['name']}":
                int(r["id"])
            for _, r in tours.iterrows()
        }

        selected = st.selectbox(
            "Tour",
            list(labels.keys())
        )

        tour_id = labels[selected]

        incidents = query_df("""
            SELECT
                incident_date,
                incident_type,
                description,
                action_taken,
                status
            FROM incidents
            WHERE tour_id=%s
            ORDER BY incident_date DESC
        """, (tour_id,))

        if not incidents.empty:

            st.dataframe(
                incidents.rename(
                    columns={
                        "incident_date": "Ngày",
                        "incident_type": "Loại sự cố",
                        "description": "Mô tả",
                        "action_taken": "Xử lý",
                        "status": "Trạng thái"
                    }
                ),
                use_container_width=True,
                hide_index=True
            )

        else:

            st.success(
                "Chưa có sự cố nào."
            )

        st.markdown("---")

        st.subheader(
            "➕ Tạo báo cáo sự cố"
        )

        with st.form("incident"):

            incident_date = st.date_input(
                "Ngày",
                date.today()
            )

            incident_type = st.selectbox(
                "Loại sự cố",
                [
                    "Khách bị lạc",
                    "Khách bị bệnh",
                    "Tai nạn",
                    "Mất đồ",
                    "Xe hỏng",
                    "Trễ lịch trình",
                    "Khác"
                ]
            )

            description = st.text_area(
                "Mô tả sự cố *"
            )

            action = st.text_area(
                "Cách xử lý"
            )

            submit = st.form_submit_button(
                "🚨 Gửi báo cáo",
                type="primary"
            )

            if submit:

                if not description.strip():

                    st.error(
                        "Vui lòng mô tả sự cố."
                    )

                else:

                    execute("""
                        INSERT INTO incidents
                        (
                            tour_id,
                            incident_date,
                            incident_type,
                            description,
                            action_taken
                        )
                        VALUES
                        (
                            %s, %s, %s,
                            %s, %s
                        )
                    """, (
                        tour_id,
                        incident_date,
                        incident_type,
                        description,
                        action
                    ))

                    st.success(
                        "Đã ghi nhận sự cố."
                    )

                    st.rerun()


# =========================================================
# CÀI ĐẶT DỮ LIỆU
# =========================================================

elif menu == "⚙️ Cài đặt dữ liệu":

    st.title(
        "⚙️ Cài đặt dữ liệu"
    )

    st.subheader(
        "👨‍🏫 Quản lý hướng dẫn viên"
    )

    guides = query_df(
        "SELECT * FROM guides ORDER BY name"
    )

    if not guides.empty:

        st.dataframe(
            guides.rename(
                columns={
                    "id": "ID",
                    "name": "Họ tên",
                    "phone": "Điện thoại",
                    "email": "Email",
                    "role": "Vai trò"
                }
            ),
            use_container_width=True,
            hide_index=True
        )

    with st.form("add_guide"):

        name = st.text_input(
            "Họ tên *"
        )

        phone = st.text_input(
            "Điện thoại"
        )

        email = st.text_input(
            "Email"
        )

        role = st.selectbox(
            "Vai trò",
            [
                "Tour Guide",
                "Senior Guide",
                "Guide Leader"
            ]
        )

        submit = st.form_submit_button(
            "➕ Thêm HDV",
            type="primary"
        )

        if submit:

            if not name.strip():

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
                        role
                    )
                    VALUES
                    (
                        %s, %s, %s, %s
                    )
                """, (
                    name.strip(),
                    phone,
                    email,
                    role
                ))

                st.success(
                    "Đã thêm HDV."
                )

                st.rerun()

    st.markdown("---")

    st.subheader(
        "💾 Trạng thái database"
    )

    try:

        test = query_df(
            "SELECT DATABASE() AS db"
        )

        if not test.empty:

            st.success(
                f"🟢 Đã kết nối MySQL: "
                f"`{test.iloc[0]['db']}`"
            )

    except Exception as e:

        st.error(
            "🔴 Không thể kết nối MySQL."
        )

        st.exception(e)

    st.info(
        "Database hiện tại là MySQL trên Aiven."
    )


# =========================================================
# FOOTER
# =========================================================

st.sidebar.markdown("---")
st.sidebar.caption("© 2026 TourMate")
