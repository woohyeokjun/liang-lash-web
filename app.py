import os
import uuid
import hashlib
from datetime import datetime
import streamlit as st
from supabase import create_client, Client

# ==========================================
# 기본 설정 및 Supabase 클라우드 연동
# ==========================================
st.set_page_config(page_title="리앙래쉬 고객관리", page_icon="✨", layout="wide")

# Secrets에서 Supabase 정보 불러오기
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error("Supabase 연결 설정(Secrets)을 확인해주세요.")
    st.stop()

# ==========================================
# 로그인 인증 관리 (초기 비밀번호: 1234)
# ==========================================
ADMIN_PASSWORD_HASH = hashlib.sha256("rnflrnfl".encode()).hexdigest()

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def check_password():
    input_hash = hashlib.sha256(st.session_state.get("password_input", "").encode()).hexdigest()
    if input_hash == ADMIN_PASSWORD_HASH:
        st.session_state.authenticated = True
        st.session_state.password_input = ""
    else:
        st.error("비밀번호가 올바르지 않습니다.")

if not st.session_state.authenticated:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("## ✨ LIANG LASH PREMIUM")
        st.text_input("접속 비밀번호", type="password", key="password_input", on_change=check_password)
        if st.button("🔑 로그인", use_container_width=True, type="primary"):
            check_password()
            if st.session_state.authenticated:
                st.rerun()
    st.stop()

# ==========================================
# 데이터 처리 함수 (Supabase DB & Storage)
# ==========================================
def load_data():
    try:
        response = supabase.table("customers").select("*").order("created_at", desc=True).execute()
        return response.data
    except Exception:
        return []

def format_phone(phone_str):
    cleaned = ''.join(filter(str.isdigit, str(phone_str)))[:11]
    if len(cleaned) < 4: return cleaned
    elif len(cleaned) < 8: return f"{cleaned[:3]}-{cleaned[3:]}"
    else: return f"{cleaned[:3]}-{cleaned[3:7]}-{cleaned[7:]}"

# 데이터 초기화
if "customers" not in st.session_state:
    st.session_state.customers = load_data()

# ==========================================
# UI 및 화면 구성
# ==========================================
h_col1, h_col2 = st.columns([5, 1])
with h_col1:
    st.title("✨ LIANG LASH 고객관리 시스템")
with h_col2:
    if st.button("🔒 로그아웃", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

MENU_DATA = {
    "💖 LED연장 패키지 💖": ["LED 클래식연장", "LED 마스카라연장", "포인트 언더 연장 (LED연장)", "LED 연장 후 펌 (포인트연장)"],
    "💖 일반연장 💖": ["클래식 연장", "마스카라 연장", "더블 숱 추가 (100% 채움)", "특수컬 추가금"],
    "💖 디자인 속눈썹펌 💖": ["노글루 수분폭탄 속눈썹펌", "노글루 블랙 틴팅펌", "언더 패키지 펌(듀얼)"],
    "💖 lash care 💖": ["아이돌연장 전용 듀얼 영양제"],
}

col_left, col_right = st.columns([1, 1], gap="large")

# [왼쪽] 등록
with col_left:
    st.markdown("### 📝 고객 및 시술 등록")
    name = st.text_input("고객명 *")
    phone = st.text_input("연락처")
    visit_date = st.date_input("방문 날짜", datetime.now())

    selected_services = []
    with st.popover("💖 시술 메뉴 목록 열기", use_container_width=True):
        for category, items in MENU_DATA.items():
            selected = st.multiselect(category, options=items)
            selected_services.extend(selected)

    memo = st.text_area("시술 메모 및 특이사항", height=100)
    uploaded_files = st.file_uploader("📷 작업 사진 첨부", type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True)

    if st.button("✨ 고객 등록 완료", use_container_width=True, type="primary"):
        if not name.strip():
            st.warning("고객명을 입력해주세요.")
        else:
            photo_urls = []
            if uploaded_files:
                for uf in uploaded_files:
                    file_ext = os.path.splitext(uf.name)[1]
                    file_path = f"{uuid.uuid4().hex}{file_ext}"
                    # Supabase Storage 업로드
                    res = supabase.storage.from_("lash-photos").upload(file_path, uf.getvalue())
                    public_url = supabase.storage.from_("lash-photos").get_public_url(file_path)
                    photo_urls.append(public_url)

            # Supabase DB 저장
            new_data = {
                "name": name.strip(),
                "phone": format_phone(phone),
                "visit_date": visit_date.strftime("%Y-%m-%d"),
                "services": ", ".join(selected_services),
                "memo": memo.strip(),
                "photos": photo_urls
            }
            supabase.table("customers").insert(new_data).execute()
            st.session_state.customers = load_data()
            st.success("성공적으로 저장되었습니다!")
            st.rerun()

# [오른쪽] 기록 및 조회
with col_right:
    st.markdown("### 📋 고객 방문 기록")
    search_query = st.text_input("🔍 검색 (고객명 또는 연락처)")

    filtered = st.session_state.customers
    if search_query.strip():
        q = search_query.strip().lower()
        filtered = [c for c in filtered if q in c["name"].lower() or q in c["phone"].lower()]

    if not filtered:
        st.info("등록된 기록이 없습니다.")
    else:
        for customer in filtered:
            with st.expander(f"📅 {customer['visit_date']} | 👤 {customer['name']} ({customer['phone']})"):
                st.markdown(f"**시술 항목:** {customer.get('services') or '없음'}")
                st.markdown(f"**특이사항:** {customer.get('memo') or '없음'}")
                
                photos = customer.get("photos", [])
                if photos:
                    p_cols = st.columns(3)
                    for idx, url in enumerate(photos):
                        with p_cols[idx % 3]:
                            st.image(url, use_container_width=True)

                if st.button("🗑️ 기록 삭제", key=f"del_{customer['id']}", type="secondary"):
                    supabase.table("customers").delete().eq("id", customer["id"]).execute()
                    st.session_state.customers = load_data()
                    st.warning("삭제되었습니다.")
                    st.rerun()
