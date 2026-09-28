import streamlit as st
import pymysql

# =========================================================
# CẤU HÌNH TRANG
# =========================================================

st.set_page_config(
    page_title="TourMate",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# CẤU HÌNH MYSQL AIVEN
# =========================================================

MYSQL_HOST = "mysql-19728385-npmaihuong-927f.b.aivencloud.com"
MYSQL_PORT = 27942
MYSQL_USER = "avnadmin"
MYSQL_PASSWORD = "AVNS_zBDlzsF9I5fC-EdWcl0"
MYSQL_DATABASE = "defaultdb"


# =========================================================
# CẤU HÌNH GEMINI AI
# =========================================================

GEMINI_API_KEY = "AQ.Ab8RN6Ljwwr1RBJG3necBoHt3PkBlzv2t0jRKxhVqvLc9lY0QA"


# =========================================================
# KẾT NỐI MYSQL
# =========================================================

@st.cache_resource
def get_connection():
    try:
        connection = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=15,
            read_timeout=15,
            write_timeout=15
        )

        return connection

    except Exception as e:
        st.error("❌ Không thể kết nối MySQL Aiven.")
        st.code(str(e))
        return None


# =========================================================
# KIỂM TRA MYSQL
# =========================================================

db = get_connection()

mysql_status = False

if db:
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT 1 AS connected")
            result = cursor.fetchone()

        if result and result["connected"] == 1:
            mysql_status = True

    except Exception:
        mysql_status = False


# =========================================================
# GEMINI AI
# =========================================================

try:
    from google import genai

    if GEMINI_API_KEY and GEMINI_API_KEY != "DÁN_GEMINI_API_KEY_CỦA_EM_VÀO_ĐÂY":

        gemini_client = genai.Client(
            api_key=GEMINI_API_KEY
        )

        GEMINI_AVAILABLE = True

    else:

        gemini_client = None
        GEMINI_AVAILABLE = False

except Exception:

    gemini_client = None
    GEMINI_AVAILABLE = False


# =========================================================
# HÀM GỌI AI
# =========================================================

def ask_tourmate_ai(question, history):

    if not GEMINI_AVAILABLE:
        return (
            "⚠️ Chatbot AI chưa được cấu hình.\n\n"
            "Em hãy thêm Gemini API Key vào biến "
            "`GEMINI_API_KEY` trong app.py."
        )

    try:

        system_instruction = """
Bạn là TourMate AI Assistant.

Bạn là trợ lý AI chuyên hỗ trợ hướng dẫn viên du lịch
và nhân viên công ty lữ hành.

Nhiệm vụ của bạn:

1. Hỗ trợ lập và kiểm tra lịch trình tour.
2. Gợi ý điểm tham quan.
3. Hỗ trợ nghiệp vụ hướng dẫn viên.
4. Hỗ trợ xử lý các tình huống phát sinh trong tour.
5. Viết nội dung thuyết minh điểm tham quan.
6. Gợi ý cách giao tiếp với khách du lịch.
7. Hỗ trợ checklist trước khi khởi hành.
8. Hỗ trợ tổ chức tour.
9. Giải thích các thuật ngữ trong ngành du lịch.
10. Hỗ trợ lên ý tưởng tour.

Quy tắc trả lời:

- Trả lời bằng tiếng Việt.
- Ngắn gọn nhưng hữu ích.
- Ưu tiên các bước thực tế.
- Khi cần, sử dụng danh sách đánh số.
- Không bịa thông tin nếu không chắc chắn.
- Nếu câu hỏi liên quan đến thông tin hiện tại
  như giờ mở cửa, giá vé, thời tiết hoặc quy định mới,
  hãy nói rõ rằng cần kiểm tra nguồn chính thức.
- Luôn giữ phong cách thân thiện, chuyên nghiệp.
- Người sử dụng là hướng dẫn viên du lịch.
"""

        # -----------------------------------------------------
        # Tạo nội dung có lịch sử hội thoại
        # -----------------------------------------------------

        conversation = system_instruction + "\n\n"

        for item in history[-10:]:

            role = item.get("role", "")
            content = item.get("content", "")

            if role == "user":
                conversation += f"HDV: {content}\n"

            elif role == "assistant":
                conversation += f"TourMate AI: {content}\n"

        conversation += f"\nHDV: {question}\nTourMate AI:"

        # -----------------------------------------------------
        # Gọi Gemini
        # -----------------------------------------------------

        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=conversation
        )

        if response and response.text:
            return response.text

        return "⚠️ AI không trả về nội dung."

    except Exception as e:

        return (
            "❌ Chatbot gặp lỗi khi kết nối AI.\n\n"
            f"Chi tiết: `{str(e)}`"
        )


# =========================================================
# CSS
# =========================================================

st.markdown("""
<style>

.main {
    background-color: #f5f7fb;
}

.block-container {
    padding-top: 1.5rem;
    padding-bottom: 3rem;
}

.hero {
    background: linear-gradient(135deg, #0f766e, #0ea5a4);
    padding: 30px;
    border-radius: 20px;
    color: white;
    margin-bottom: 25px;
}

.hero h1 {
    font-size: 38px;
    margin-bottom: 8px;
}

.hero p {
    font-size: 17px;
    opacity: 0.95;
}

.card {
    background: white;
    padding: 22px;
    border-radius: 16px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 3px 12px rgba(0,0,0,0.05);
    margin-bottom: 15px;
}

.success {
    background: #ecfdf5;
    border-left: 5px solid #10b981;
    padding: 15px;
    border-radius: 10px;
}

.warning {
    background: #fffbeb;
    border-left: 5px solid #f59e0b;
    padding: 15px;
    border-radius: 10px;
}

.chat-title {
    background: linear-gradient(135deg, #0f766e, #0ea5a4);
    color: white;
    padding: 20px;
    border-radius: 15px;
    margin-bottom: 20px;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# HEADER
# =========================================================

st.markdown("""
<div class="hero">

    <h1>🧭 TourMate</h1>

    <p>Smart Tour Guide Management System</p>

    <p>
        Quản lý tour • Lịch trình • Khách hàng •
        Hướng dẫn viên • Checklist • AI Assistant
    </p>

</div>
""", unsafe_allow_html=True)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown("## 🧭 TOURMATE")

    st.caption("Smart Tour Guide Management System")

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
            "🎤 Thư viện thuyết minh",
            "⚠️ Sự cố",
            "👨‍✈️ Hướng dẫn viên",
            "🤖 TourMate AI",
            "⚙️ Cài đặt"
        ]
    )

    st.divider()

    if mysql_status:
        st.success("🟢 MySQL Aiven đã kết nối")
    else:
        st.error("🔴 MySQL chưa kết nối")

    if GEMINI_AVAILABLE:
        st.success("🤖 AI đã sẵn sàng")
    else:
        st.warning("⚠️ AI chưa cấu hình")


# =========================================================
# DASHBOARD
# =========================================================

if menu == "🏠 Dashboard":

    st.subheader("👋 Chào mừng đến với TourMate")

    st.write(
        "Hệ thống hỗ trợ hướng dẫn viên quản lý toàn bộ công việc "
        "trong quá trình dẫn tour."
    )

    st.divider()

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "🚌 Tour hôm nay",
            "2",
            "+1"
        )

    with col2:

        st.metric(
            "👥 Khách hàng",
            "38",
            "+8"
        )

    with col3:

        st.metric(
            "📍 Điểm tham quan",
            "12"
        )

    with col4:

        st.metric(
            "⚠️ Sự cố",
            "1"
        )

    st.divider()

    col1, col2 = st.columns([1.4, 1])

    with col1:

        st.markdown("### 🚌 Tour sắp diễn ra")

        st.markdown("""
        <div class="card">

        <b>VT001 – Vũng Tàu 2N1Đ</b><br>
        📅 28/09/2026<br>
        🕐 07:30<br>
        📍 Vũng Tàu<br>
        👥 20 khách<br>
        👨‍✈️ HDV: Nguyễn Minh Anh

        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="card">

        <b>DL002 – Đà Lạt 3N2Đ</b><br>
        📅 30/09/2026<br>
        🕐 06:00<br>
        📍 Đà Lạt<br>
        👥 18 khách<br>
        👨‍✈️ HDV: Trần Ngọc Mai

        </div>
        """, unsafe_allow_html=True)

    with col2:

        st.markdown("### ✅ Checklist hôm nay")

        st.checkbox("Kiểm tra danh sách khách")
        st.checkbox("Kiểm tra xe")
        st.checkbox("Kiểm tra phòng khách sạn")
        st.checkbox("Chuẩn bị nước uống")
        st.checkbox("Chuẩn bị micro")
        st.checkbox("Kiểm tra vé tham quan")

    st.divider()

    st.markdown("### 📊 Tình trạng hoạt động")

    data = {
        "Hạng mục": [
            "Tour",
            "Khách hàng",
            "Checklist",
            "Điểm tham quan",
            "Sự cố"
        ],
        "Trạng thái": [
            "Đang hoạt động",
            "Đang hoạt động",
            "80% hoàn thành",
            "12 điểm",
            "1 cần xử lý"
        ]
    }

    st.dataframe(
        data,
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# QUẢN LÝ TOUR
# =========================================================

elif menu == "🚌 Quản lý Tour":

    st.subheader("🚌 Quản lý Tour")

    tab1, tab2 = st.tabs([
        "📋 Danh sách tour",
        "➕ Tạo tour"
    ])

    with tab1:

        st.markdown("### Danh sách tour")

        tours = [
            {
                "Mã tour": "VT001",
                "Tên tour": "Vũng Tàu 2N1Đ",
                "Ngày đi": "28/09/2026",
                "Ngày về": "29/09/2026",
                "Khách": 20,
                "HDV": "Nguyễn Minh Anh",
                "Trạng thái": "Đang chạy"
            },
            {
                "Mã tour": "DL002",
                "Tên tour": "Đà Lạt 3N2Đ",
                "Ngày đi": "30/09/2026",
                "Ngày về": "02/10/2026",
                "Khách": 18,
                "HDV": "Trần Ngọc Mai",
                "Trạng thái": "Sắp khởi hành"
            },
            {
                "Mã tour": "PQ003",
                "Tên tour": "Phú Quốc 4N3Đ",
                "Ngày đi": "05/10/2026",
                "Ngày về": "08/10/2026",
                "Khách": 25,
                "HDV": "Lê Hoàng Nam",
                "Trạng thái": "Đã lên lịch"
            }
        ]

        st.dataframe(
            tours,
            use_container_width=True,
            hide_index=True
        )

    with tab2:

        st.markdown("### ➕ Tạo tour mới")

        with st.form("create_tour"):

            col1, col2 = st.columns(2)

            with col1:

                code = st.text_input("Mã tour")

                name = st.text_input("Tên tour")

                start = st.date_input(
                    "Ngày bắt đầu"
                )

            with col2:

                end = st.date_input(
                    "Ngày kết thúc"
                )

                guests = st.number_input(
                    "Số lượng khách",
                    min_value=1,
                    value=10
                )

                guide = st.text_input(
                    "Hướng dẫn viên"
                )

            notes = st.text_area(
                "Ghi chú"
            )

            submit = st.form_submit_button(
                "💾 Lưu tour",
                use_container_width=True
            )

            if submit:

                st.success(
                    f"Đã tạo tour **{code} - {name}**"
                )


# =========================================================
# LỊCH TRÌNH
# =========================================================

elif menu == "📅 Lịch trình":

    st.subheader("📅 Lịch trình tour")

    schedule = [
        ["07:00", "Tập trung", "Bãi Sau Vũng Tàu"],
        ["08:00", "Khởi hành", "Bãi Sau"],
        ["09:00", "Tham quan", "Tượng Chúa Kitô"],
        ["11:00", "Tham quan", "Hải đăng Vũng Tàu"],
        ["12:00", "Ăn trưa", "Nhà hàng địa phương"],
        ["14:00", "Nghỉ ngơi", "Khách sạn"],
        ["16:00", "Tham quan", "Bạch Dinh"],
        ["18:30", "Ăn tối", "Nhà hàng"],
    ]

    st.dataframe(
        schedule,
        column_config={
            0: "Thời gian",
            1: "Hoạt động",
            2: "Địa điểm"
        },
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# KHÁCH HÀNG
# =========================================================

elif menu == "👥 Khách hàng":

    st.subheader("👥 Quản lý khách hàng")

    guests = [
        ["KH001", "Nguyễn Văn An", "0901234567", "VT001"],
        ["KH002", "Trần Thị Bình", "0912345678", "VT001"],
        ["KH003", "Lê Minh Đức", "0923456789", "VT001"],
        ["KH004", "Phạm Ngọc Anh", "0934567890", "DL002"],
        ["KH005", "Hoàng Văn Nam", "0945678901", "DL002"],
    ]

    st.dataframe(
        guests,
        column_config={
            0: "Mã khách",
            1: "Họ tên",
            2: "Số điện thoại",
            3: "Mã tour"
        },
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# CHECKLIST
# =========================================================

elif menu == "✅ Checklist":

    st.subheader("✅ Checklist hướng dẫn viên")

    st.progress(70)

    st.write("7 / 10 nhiệm vụ đã hoàn thành")

    tasks = [
        "Kiểm tra danh sách khách",
        "Kiểm tra giấy tờ",
        "Kiểm tra xe",
        "Kiểm tra tài xế",
        "Kiểm tra khách sạn",
        "Kiểm tra nhà hàng",
        "Chuẩn bị nước uống",
        "Chuẩn bị micro",
        "Kiểm tra vé",
        "Kiểm tra lịch trình"
    ]

    for i, task in enumerate(tasks):

        if i < 7:

            st.checkbox(
                f"✅ {task}",
                value=True,
                key=f"task_{i}"
            )

        else:

            st.checkbox(
                f"⬜ {task}",
                key=f"task_{i}"
            )


# =========================================================
# ĐIỂM THAM QUAN
# =========================================================

elif menu == "📍 Điểm tham quan":

    st.subheader("📍 Thư viện điểm tham quan")

    col1, col2, col3 = st.columns(3)

    places = [
        ("🏔️", "Tượng Chúa Kitô", "Vũng Tàu"),
        ("🏛️", "Bạch Dinh", "Vũng Tàu"),
        ("🌊", "Bãi Sau", "Vũng Tàu"),
    ]

    for col, place in zip(
        [col1, col2, col3],
        places
    ):

        with col:

            st.markdown(
                f"""
                <div class="card">

                    <h2>{place[0]}</h2>

                    <h3>{place[1]}</h3>

                    <p>📍 {place[2]}</p>

                    <p>⭐ Điểm tham quan nổi bật</p>

                </div>
                """,
                unsafe_allow_html=True
            )


# =========================================================
# THUYẾT MINH
# =========================================================

elif menu == "🎤 Thư viện thuyết minh":

    st.subheader("🎤 Thư viện thuyết minh")

    place = st.selectbox(
        "Chọn điểm tham quan",
        [
            "Tượng Chúa Kitô",
            "Bạch Dinh",
            "Hải đăng Vũng Tàu",
            "Bãi Sau"
        ]
    )

    scripts = {

        "Tượng Chúa Kitô":
            """
            Tượng Chúa Kitô Vua là một trong những biểu tượng
            nổi tiếng của thành phố Vũng Tàu.
            Công trình nằm trên núi Nhỏ và hướng ra biển.
            """,

        "Bạch Dinh":
            """
            Bạch Dinh là công trình kiến trúc mang dấu ấn
            châu Âu nằm trên sườn núi Lớn tại Vũng Tàu.
            """,

        "Hải đăng Vũng Tàu":
            """
            Hải đăng Vũng Tàu là một trong những ngọn hải đăng
            lâu đời và là điểm ngắm cảnh nổi tiếng của thành phố.
            """,

        "Bãi Sau":
            """
            Bãi Sau là một trong những bãi biển nổi tiếng nhất
            tại Vũng Tàu, thu hút đông đảo khách du lịch.
            """
    }

    st.info(scripts[place])

    st.text_area(
        "🎙️ Nội dung thuyết minh",
        scripts[place],
        height=200
    )


# =========================================================
# SỰ CỐ
# =========================================================

elif menu == "⚠️ Sự cố":

    st.subheader("⚠️ Quản lý sự cố")

    incidents = [
        [
            "INC001",
            "Khách làm mất hành lý",
            "VT001",
            "Đang xử lý"
        ],
        [
            "INC002",
            "Xe đến trễ 15 phút",
            "DL002",
            "Đã xử lý"
        ]
    ]

    st.dataframe(
        incidents,
        column_config={
            0: "Mã sự cố",
            1: "Nội dung",
            2: "Tour",
            3: "Trạng thái"
        },
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    st.markdown("### ➕ Báo cáo sự cố")

    with st.form("incident_form"):

        title = st.text_input("Tên sự cố")

        tour = st.text_input("Tour")

        description = st.text_area("Mô tả")

        submit = st.form_submit_button(
            "🚨 Báo cáo sự cố"
        )

        if submit:

            st.success(
                "Đã ghi nhận sự cố."
            )


# =========================================================
# HƯỚNG DẪN VIÊN
# =========================================================

elif menu == "👨‍✈️ Hướng dẫn viên":

    st.subheader("👨‍✈️ Quản lý hướng dẫn viên")

    guides = [
        [
            "HDV001",
            "Nguyễn Minh Anh",
            "0901111111",
            3
        ],
        [
            "HDV002",
            "Trần Ngọc Mai",
            "0902222222",
            2
        ],
        [
            "HDV003",
            "Lê Hoàng Nam",
            "0903333333",
            4
        ],
    ]

    st.dataframe(
        guides,
        column_config={
            0: "Mã HDV",
            1: "Họ tên",
            2: "Điện thoại",
            3: "Tour đang phụ trách"
        },
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# 🤖 TOURMATE AI
# =========================================================

elif menu == "🤖 TourMate AI":

    st.markdown("""
    <div class="chat-title">

        <h2>🤖 TourMate AI Assistant</h2>

        <p>
        Trợ lý AI dành cho hướng dẫn viên du lịch
        </p>

    </div>
    """, unsafe_allow_html=True)

    # -----------------------------------------------------
    # Thông tin chatbot
    # -----------------------------------------------------

    if GEMINI_AVAILABLE:

        st.success(
            "🟢 TourMate AI đang hoạt động"
        )

    else:

        st.warning(
            "⚠️ Chưa cấu hình Gemini API Key."
        )

    # -----------------------------------------------------
    # Khởi tạo lịch sử chat
    # -----------------------------------------------------

    if "tourmate_messages" not in st.session_state:

        st.session_state.tourmate_messages = []

    # -----------------------------------------------------
    # Nút xóa hội thoại
    # -----------------------------------------------------

    col1, col2 = st.columns([5, 1])

    with col2:

        if st.button(
            "🗑️ Xóa chat",
            use_container_width=True
        ):

            st.session_state.tourmate_messages = []

            st.rerun()

    # -----------------------------------------------------
    # Hiển thị lịch sử
    # -----------------------------------------------------

    for message in st.session_state.tourmate_messages:

        with st.chat_message(
            message["role"]
        ):

            st.markdown(
                message["content"]
            )

    # -----------------------------------------------------
    # Gợi ý câu hỏi
    # -----------------------------------------------------

    st.markdown("### 💡 Bạn có thể hỏi")

    suggestion1, suggestion2, suggestion3 = st.columns(3)

    with suggestion1:

        if st.button(
            "📅 Lập lịch trình Vũng Tàu",
            use_container_width=True
        ):

            st.session_state["ai_question"] = (
                "Hãy lập lịch trình tour Vũng Tàu "
                "2 ngày 1 đêm cho đoàn 20 khách."
            )

    with suggestion2:

        if st.button(
            "🎤 Viết bài thuyết minh",
            use_container_width=True
        ):

            st.session_state["ai_question"] = (
                "Hãy viết bài thuyết minh khoảng 2 phút "
                "về Tượng Chúa Kitô Vũng Tàu."
            )

    with suggestion3:

        if st.button(
            "⚠️ Xử lý tình huống",
            use_container_width=True
        ):

            st.session_state["ai_question"] = (
                "Nếu một khách bị mất hành lý trong tour "
                "thì hướng dẫn viên nên xử lý như thế nào?"
            )

    # -----------------------------------------------------
    # Nhận câu hỏi
    # -----------------------------------------------------

    question = st.chat_input(
        "💬 Nhập câu hỏi cho TourMate AI..."
    )

    # Nếu bấm câu hỏi gợi ý
    if "ai_question" in st.session_state:

        question = st.session_state.pop(
            "ai_question"
        )

    # -----------------------------------------------------
    # Xử lý câu hỏi
    # -----------------------------------------------------

    if question:

        # Lưu câu hỏi
        st.session_state.tourmate_messages.append(
            {
                "role": "user",
                "content": question
            }
        )

        # Hiển thị câu hỏi
        with st.chat_message("user"):

            st.markdown(question)

        # Gọi AI
        with st.chat_message("assistant"):

            with st.spinner(
                "🤖 TourMate AI đang suy nghĩ..."
            ):

                answer = ask_tourmate_ai(
                    question,
                    st.session_state.tourmate_messages[:-1]
                )

            st.markdown(answer)

        # Lưu câu trả lời
        st.session_state.tourmate_messages.append(
            {
                "role": "assistant",
                "content": answer
            }
        )


# =========================================================
# CÀI ĐẶT
# =========================================================

elif menu == "⚙️ Cài đặt":

    st.subheader("⚙️ Cài đặt hệ thống")

    if mysql_status:

        st.markdown("""
        <div class="success">

        🟢 MySQL Aiven đang hoạt động bình thường.

        </div>
        """, unsafe_allow_html=True)

    else:

        st.markdown("""
        <div class="warning">

        🔴 Không thể kết nối MySQL Aiven.

        </div>
        """, unsafe_allow_html=True)

    st.divider()

    st.write("### 🗄️ Database")

    st.write(
        f"**Host:** {MYSQL_HOST}"
    )

    st.write(
        f"**Port:** {MYSQL_PORT}"
    )

    st.write(
        f"**Database:** {MYSQL_DATABASE}"
    )

    st.write(
        f"**User:** {MYSQL_USER}"
    )

    st.divider()

    st.write("### 🤖 AI Assistant")

    if GEMINI_AVAILABLE:

        st.success(
            "🟢 Gemini AI đã được kết nối."
        )

    else:

        st.warning(
            "🟡 Gemini AI chưa được cấu hình."
        )

    st.divider()

    st.write("### 📱 Thông tin hệ thống")

    st.write(
        "**Ứng dụng:** TourMate"
    )

    st.write(
        "**Phiên bản:** 1.1"
    )

    st.write(
        "**Framework:** Streamlit"
    )

    st.write(
        "**Database:** MySQL Aiven"
    )

    st.write(
        "**AI:** Gemini"
    )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "🧭 TourMate – Smart Tour Guide Management System | "
    "BVU Tourism & Travel Management"
)
