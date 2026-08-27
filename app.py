import os
import json
import uuid
import hashlib
from datetime import datetime
import streamlit as st

# ==========================================
# 기본 설정 및 페이지 구성
# ==========================================
st.set_page_config(
    page_title="리앙래쉬 (LIANG LASH) 고객관리",
    page_icon="✨",
    layout="wide"
)

# ==========================================
# 로그인 인증 관리 (새로고침 유지 보완)
# ==========================================
ADMIN_PASSWORD_HASH = hashlib.sha256("rnflrnfl".encode()).hexdigest()

# 세션 상태 초기화 (한 번 인증되면 세션 동안 유지됨)
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def check_password():
    password_input = st.session_state.get("password_input", "")
    input_hash = hashlib.sha256(password_input.encode()).hexdigest()
    if input_hash == ADMIN_PASSWORD_HASH:
        st.session_state.authenticated = True
        st.session_state.password_input = ""  # 입력창 초기화
    else:
        st.error("비밀번호가 올바르지 않습니다.")

# 로그인되어 있지 않은 경우 로그인 화면 표시
if not st.session_state.authenticated:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
            <div style="background-color: #FFFFFF; padding: 30px; border-radius: 12px; border: 1.5px solid #BAE6FD; text-align: center;">
                <h2 style="color: #0369A1; margin-bottom: 5px;">✨ LIANG LASH</h2>
                <p style="color: #0284C7; font-size: 13px; font-weight: bold;">PREMIUM MANAGEMENT SYSTEM</p>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 엔터 키 입력 시 자동 로그인 처리
        st.text_input("접속 비밀번호를 입력하세요", type="password", key="password_input", on_change=check_password)
        if st.button("🔑 로그인", use_container_width=True, type="primary"):
            check_password()
            if st.session_state.authenticated:
                st.rerun()
    st.stop()

# ==========================================
# 메인 시스템 시작 (로그인 성공 시 접근)
# ==========================================

# 파일 및 디렉토리 설정
DATA_FILE = "customers.json"
UPLOAD_DIR = "uploaded_photos"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Custom CSS 적용 (메모 박스 크기 고정 및 뷰어 스타일)
st.markdown("""
    <style>
    .main { background-color: #F0F9FF; }
    .header-card {
        background-color: #FFFFFF;
        padding: 20px 30px;
        border-radius: 12px;
        border: 1.5px solid #BAE6FD;
        margin-bottom: 20px;
    }
    .main-title { color: #0369A1; font-weight: bold; font-size: 28px; margin: 0; }
    .sub-title { color: #0284C7; font-size: 13px; font-weight: bold; margin-top: 4px; }
    .stButton>button { border-radius: 8px; font-weight: bold; }
    
    /* 메모 입력창 드래그 크기 조절 금지 (고정) */
    textarea {
        resize: none !important;
    }

    /* 메모 보기 전용 스타일 박스 */
    .memo-display-box {
        background-color: #FFFFFF;
        border: 1px solid #BAE6FD;
        border-radius: 8px;
        padding: 15px;
        min-height: 160px;
        white-space: pre-wrap;
        color: #333333;
        font-size: 14px;
        line-height: 1.6;
        margin-bottom: 10px;
    }
    
    /* 방문 회차 카드 스타일 */
    .visit-card {
        background-color: #F8FAFC;
        border: 1.5px solid #E2E8F0;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# 데이터 처리 함수
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for c in data:
                    if "visits" not in c:
                        c["visits"] = [{
                            "visit_id": str(uuid.uuid4().hex),
                            "date": c.get("date", "2026-01-01"),
                            "services": c.get("services", ""),
                            "memo": c.get("memo", ""),
                            "photos": c.get("photos", [])
                        }]
                return data
        except Exception:
            return []
    return []

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def format_phone(phone_str):
    cleaned = ''.join(filter(str.isdigit, str(phone_str)))[:11]
    if len(cleaned) < 4:
        return cleaned
    elif len(cleaned) < 8:
        return f"{cleaned[:3]}-{cleaned[3:]}"
    else:
        return f"{cleaned[:3]}-{cleaned[3:7]}-{cleaned[7:]}"

# 데이터 및 세션 상태 초기화
if "customers" not in st.session_state:
    st.session_state.customers = load_data()

if "reg_key_version" not in st.session_state:
    st.session_state.reg_key_version = 0

def auto_format_phone_callback():
    key = f"reg_phone_{st.session_state.reg_key_version}"
    if key in st.session_state:
        st.session_state[key] = format_phone(st.session_state[key])

# 특정 방문 회차 메모 수정 모달 (Dialog)
@st.dialog("📝 방문 기록 메모 수정", width="large")
def edit_visit_memo_dialog(customer_name, visit):
    st.caption(f"👤 **{customer_name}** 님의 ({visit['date']}) 방문 특이사항 메모를 수정합니다.")
    
    edited_memo = st.text_area(
        "메모 내용", 
        value=visit.get("memo", ""), 
        height=350, 
        key=f"dialog_visit_memo_{visit['visit_id']}"
    )
    
    col_save, col_close = st.columns([1, 1])
    with col_save:
        if st.button("💾 수정 내용 저장", type="primary", use_container_width=True):
            visit["memo"] = edited_memo.strip()
            save_data(st.session_state.customers)
            st.rerun()
    with col_close:
        if st.button("❌ 취소", use_container_width=True):
            st.rerun()

# 상단 헤더 및 로그아웃 버튼
h_col1, h_col2 = st.columns([5, 1])
with h_col1:
    st.markdown("""
    <div class="header-card">
        <div>
            <div class="main-title">✨ LIANG LASH</div>
            <div class="sub-title">PREMIUM EYELASH MANAGEMENT SYSTEM (WEB)</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
with h_col2:
    if st.button("🔒 로그아웃", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

# 시술 메뉴 데이터
MENU_DATA = {
    "💖 LED연장 패키지 💖": ["LED 클래식연장", "LED 마스카라연장", "포인트 언더 연장 (LED연장)", "LED 연장 후 펌 (포인트연장)"],
    "💖 일반연장 💖": ["클래식 연장", "마스카라 연장", "더블 숱 추가 (100% 채움)", "특수컬 추가금"],
    "💖 디자인 속눈썹펌 💖": ["노글루 수분폭탄 속눈썹펌", "노글루 블랙 틴팅펌", "언더 패키지 펌(듀얼)"],
    "💖 lash care 💖": ["아이돌연장 전용 듀얼 영양제"],
}

# 메인 화면 레이아웃
col_left, col_right = st.columns([1, 1], gap="large")
reg_v = st.session_state.reg_key_version

# [왼쪽] 고객 및 시술 등록
with col_left:
    st.markdown("### 📝 고객 및 시술 등록")
    
    with st.container():
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("고객명 *", placeholder="이름 입력", key=f"reg_name_{reg_v}")
        with c2:
            phone = st.text_input(
                "연락처", 
                placeholder="01012345678", 
                key=f"reg_phone_{reg_v}",
                on_change=auto_format_phone_callback
            )

        visit_date = st.date_input("방문 날짜", datetime.now(), key=f"reg_date_{reg_v}")

        st.markdown("**시술 항목 선택**")
        selected_services = []
        with st.popover("💖 시술 메뉴 목록 열기", use_container_width=True):
            for category, items in MENU_DATA.items():
                selected = st.multiselect(category, options=items, key=f"reg_menu_{category}_{reg_v}")
                selected_services.extend(selected)

        if selected_services:
            st.info(f"📌 **선택된 시술:** {', '.join(selected_services)}")
        else:
            st.caption("선택된 시술 항목이 없습니다.")

        memo = st.text_area("시술 메모 및 특이사항", placeholder="특이사항을 입력하세요", height=200, key=f"reg_memo_{reg_v}")

        uploaded_files = st.file_uploader(
            "📷 작업 사진 첨부", 
            type=["jpg", "jpeg", "png", "webp"], 
            accept_multiple_files=True,
            key=f"reg_files_{reg_v}"
        )

        if st.button("✨ 고객 등록 완료", use_container_width=True, type="primary"):
            if not name.strip():
                st.warning("고객명을 입력해주세요.")
            else:
                photo_paths = []
                if uploaded_files:
                    for uf in uploaded_files:
                        file_ext = os.path.splitext(uf.name)[1]
                        filename = f"{uuid.uuid4().hex}{file_ext}"
                        filepath = os.path.join(UPLOAD_DIR, filename)
                        with open(filepath, "wb") as f:
                            f.write(uf.getbuffer())
                        photo_paths.append(filepath)

                # 새로운 방문 기록 객체 생성
                new_visit = {
                    "visit_id": str(uuid.uuid4().hex),
                    "date": visit_date.strftime("%Y-%m-%d"),
                    "services": ", ".join(selected_services),
                    "memo": memo.strip(),
                    "photos": photo_paths
                }

                cleaned_phone = format_phone(phone)
                
                # 동일한 고객(이름 + 연락처 기준)이 이미 존재하는지 확인
                existing_customer = None
                for c in st.session_state.customers:
                    if c["name"].strip() == name.strip() and c["phone"] == cleaned_phone:
                        existing_customer = c
                        break

                if existing_customer:
                    existing_customer["visits"].insert(0, new_visit)
                else:
                    new_customer = {
                        "id": int(datetime.now().timestamp() * 1000),
                        "name": name.strip(),
                        "phone": cleaned_phone,
                        "visits": [new_visit]
                    }
                    st.session_state.customers.insert(0, new_customer)

                save_data(st.session_state.customers)
                st.session_state.reg_key_version += 1
                st.success("고객 방문 기록이 저장되었습니다!")
                st.rerun()

# [오른쪽] 고객 방문 기록 및 관리
with col_right:
    st.markdown("### 📋 고객 방문 기록")
    search_query = st.text_input("🔍 검색 (고객명 또는 연락처)", placeholder="검색어 입력")

    filtered_customers = st.session_state.customers
    if search_query.strip():
        q = search_query.strip().lower()
        filtered_customers = [
            c for c in st.session_state.customers
            if q in c["name"].lower() or q in c["phone"].lower()
        ]

    if not filtered_customers:
        st.info("등록된 기록이 없습니다.")
    else:
        for customer in filtered_customers:
            total_visits = len(customer.get("visits", []))
            header_label = f"👤 {customer['name']} ({customer['phone']}) — 총 방문 {total_visits}회"
            
            with st.expander(header_label):
                visits = customer.get("visits", [])
                visits_sorted = sorted(visits, key=lambda x: x["date"], reverse=True)
                
                for v_idx, visit in enumerate(visits_sorted):
                    st.markdown(f"#### 📅 방문 날짜: {visit['date']}")
                    st.markdown(f"**📌 시술 항목:** {visit.get('services') or '선택 항목 없음'}")
                    
                    memo_content = visit.get("memo", "").strip()
                    display_memo = memo_content if memo_content else "작성된 특이사항이 없습니다."
                    st.markdown(f'<div class="memo-display-box">{display_memo}</div>', unsafe_allow_html=True)

                    if st.button(f"✏️ [{visit['date']}] 메모 수정", key=f"edit_v_{visit['visit_id']}", use_container_width=True):
                        edit_visit_memo_dialog(customer["name"], visit)

                    photos = visit.get("photos", [])
                    if photos:
                        st.markdown(f"**📷 [{visit['date']}] 작업 사진**")
                        p_cols = st.columns(3)
                        for idx, ppath in enumerate(photos):
                            if os.path.exists(ppath):
                                with p_cols[idx % 3]:
                                    st.image(ppath, use_container_width=True)

                    add_files = st.file_uploader(f"➕ [{visit['date']}] 사진 추가", type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True, key=f"add_p_{visit['visit_id']}")

                    v_btn1, v_btn2 = st.columns([1, 1])
                    with v_btn1:
                        if st.button(f"📷 사진 저장", key=f"save_p_{visit['visit_id']}", use_container_width=True):
                            if add_files:
                                for uf in add_files:
                                    file_ext = os.path.splitext(uf.name)[1]
                                    filename = f"{uuid.uuid4().hex}{file_ext}"
                                    filepath = os.path.join(UPLOAD_DIR, filename)
                                    with open(filepath, "wb") as f:
                                        f.write(uf.getbuffer())
                                    visit["photos"].append(filepath)
                                save_data(st.session_state.customers)
                                st.success("사진이 추가되었습니다!")
                                st.rerun()
                            else:
                                st.info("추가할 사진을 올려주세요.")

                    with v_btn2:
                        if st.button(f"🗑️ 이 방문 기록 삭제", key=f"del_v_{visit['visit_id']}", type="secondary", use_container_width=True):
                            customer["visits"] = [v for v in customer["visits"] if v["visit_id"] != visit["visit_id"]]
                            if not customer["visits"]:
                                st.session_state.customers = [c for c in st.session_state.customers if c["id"] != customer["id"]]
                            save_data(st.session_state.customers)
                            st.warning("선택한 방문 기록이 삭제되었습니다.")
                            st.rerun()

                    if v_idx < len(visits_sorted) - 1:
                        st.markdown("---")

                st.markdown("<br>", unsafe_allow_html=True)
                
                if st.button(f"🚨 고객 전체 정보 삭제 ({customer['name']})", key=f"del_all_{customer['id']}", type="secondary", use_container_width=True):
                    st.session_state.customers = [c for c in st.session_state.customers if c["id"] != customer["id"]]
                    save_data(st.session_state.customers)
                    st.warning("고객의 모든 정보가 삭제되었습니다.")
                    st.rerun()
