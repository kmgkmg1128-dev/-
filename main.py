import streamlit as st
import random
import time

# ============================================================
# 페이지 설정
# ============================================================
st.set_page_config(
    page_title="아르카니아: 소환의 서 (Arcania: Book of Summons)",
    page_icon="🔮",
    layout="wide",
)

# ============================================================
# 오리지널 세계관 데이터
# 세계관: '아르카니아' - 다섯 원소(불/물/바람/대지/빛)의 힘을 다루는
# 마법학교 출신 소환사가 동료 모험가들을 '소환의 서'로 불러내는 판타지
# ============================================================

ELEMENT_ICON = {
    "불": "🔥",
    "물": "💧",
    "바람": "🌪️",
    "대지": "🪨",
    "빛": "✨",
    "어둠": "🌑",
}

CLASS_ICON = {
    "마법사": "🪄",
    "전사": "⚔️",
    "궁수": "🏹",
    "힐러": "💚",
    "도적": "🗡️",
    "수호자": "🛡️",
}

RARITY_INFO = {
    3: {"label": "★★★", "color": "#7ea6c9", "glow": "#a9c9e6", "rate": 0.79},
    4: {"label": "★★★★", "color": "#b98ee0", "glow": "#d9b8f7", "rate": 0.18},
    5: {"label": "★★★★★", "color": "#f2c14e", "glow": "#ffe28a", "rate": 0.03},
}

# 캐릭터 풀 (전부 오리지널 이름/설정)
CHARACTERS = [
    # --- 3성 (일반) ---
    {"name": "리엔", "title": "견습 화염술사", "rarity": 3, "element": "불", "class": "마법사"},
    {"name": "노아", "title": "변경의 검병", "rarity": 3, "element": "대지", "class": "전사"},
    {"name": "필리", "title": "숲의 궁수", "rarity": 3, "element": "바람", "class": "궁수"},
    {"name": "세라", "title": "수련 사제", "rarity": 3, "element": "빛", "class": "힐러"},
    {"name": "카이토", "title": "뒷골목의 그림자", "rarity": 3, "element": "어둠", "class": "도적"},
    {"name": "듀란", "title": "성벽의 방패병", "rarity": 3, "element": "물", "class": "수호자"},
    # --- 4성 (레어) ---
    {"name": "이졸데", "title": "빙하의 현자", "rarity": 4, "element": "물", "class": "마법사"},
    {"name": "가레스", "title": "적화의 검성", "rarity": 4, "element": "불", "class": "전사"},
    {"name": "실피드", "title": "질풍의 사수", "rarity": 4, "element": "바람", "class": "궁수"},
    {"name": "루미네", "title": "여명의 신관", "rarity": 4, "element": "빛", "class": "힐러"},
    {"name": "네하", "title": "야음의 자객", "rarity": 4, "element": "어둠", "class": "도적"},
    {"name": "테라스", "title": "대지의 수호자", "rarity": 4, "element": "대지", "class": "수호자"},
    # --- 5성 (전설) ---
    {"name": "아젤리아", "title": "천공을 가르는 대현자", "rarity": 5, "element": "바람", "class": "마법사"},
    {"name": "발두르", "title": "종언의 화염기사", "rarity": 5, "element": "불", "class": "전사"},
    {"name": "세라핌", "title": "구원의 대천사", "rarity": 5, "element": "빛", "class": "힐러"},
    {"name": "모르가나", "title": "심연의 마녀", "rarity": 5, "element": "어둠", "class": "마법사"},
]

FEATURED_CHAR = "아젤리아"  # 이번 배너 픽업 5성
SINGLE_COST = 150
TEN_COST = 1500
PITY_SOFT_START = 70   # 이 횟수부터 5성 확률 상승 (소프트 천장)
PITY_HARD = 80         # 이 횟수에서 무조건 5성 (하드 천장)

# ============================================================
# 세션 상태 초기화
# ============================================================
def init_state():
    if "crystals" not in st.session_state:
        st.session_state.crystals = 15000
    if "pity_5" not in st.session_state:
        st.session_state.pity_5 = 0
    if "pull_count" not in st.session_state:
        st.session_state.pull_count = 0
    if "inventory" not in st.session_state:
        st.session_state.inventory = {}  # name -> count
    if "history" not in st.session_state:
        st.session_state.history = []
    if "last_results" not in st.session_state:
        st.session_state.last_results = []

init_state()

# ============================================================
# 가챠 로직
# ============================================================
def roll_rarity():
    """천장 시스템을 반영한 등급 추첨"""
    pity = st.session_state.pity_5

    if pity >= PITY_HARD - 1:
        return 5

    # 소프트 천장: 70회부터 5성 확률 점점 상승
    if pity >= PITY_SOFT_START:
        boost = (pity - PITY_SOFT_START + 1) * 0.06
        rate_5 = min(RARITY_INFO[5]["rate"] + boost, 1.0)
    else:
        rate_5 = RARITY_INFO[5]["rate"]

    rate_4 = RARITY_INFO[4]["rate"]
    roll = random.random()
    if roll < rate_5:
        return 5
    elif roll < rate_5 + rate_4:
        return 4
    else:
        return 3


def pick_character(rarity):
    pool = [c for c in CHARACTERS if c["rarity"] == rarity]
    # 픽업 캐릭터 확률 50% (5성 한정)
    if rarity == 5 and random.random() < 0.5:
        for c in pool:
            if c["name"] == FEATURED_CHAR:
                return c
    return random.choice(pool)


def do_pull(n):
    results = []
    for _ in range(n):
        rarity = roll_rarity()
        if rarity == 5:
            st.session_state.pity_5 = 0
        else:
            st.session_state.pity_5 += 1

        char = pick_character(rarity)
        results.append(char)

        name = char["name"]
        st.session_state.inventory[name] = st.session_state.inventory.get(name, 0) + 1
        st.session_state.pull_count += 1

    st.session_state.last_results = results
    st.session_state.history.extend(results)
    return results


# ============================================================
# 스타일
# ============================================================
st.markdown(
    """
    <style>
    .card {
        border-radius: 14px;
        padding: 14px 10px;
        text-align: center;
        margin-bottom: 10px;
        box-shadow: 0 0 14px var(--glow);
        background: linear-gradient(160deg, var(--bg1), var(--bg2));
        border: 2px solid var(--border);
    }
    .card .name { font-weight: 700; font-size: 1.05rem; margin-top: 4px; }
    .card .title { font-size: 0.78rem; opacity: 0.85; }
    .card .rarity { font-size: 0.95rem; letter-spacing: 1px; }
    .pity-box {
        padding: 10px 14px; border-radius: 10px;
        background: #2b2b3d; text-align: center;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def render_card(char, new=False):
    info = RARITY_INFO[char["rarity"]]
    bg1 = info["color"] + "33"
    bg2 = info["color"] + "11"
    badge = "🆕" if new else ""
    st.markdown(
        f"""
        <div class="card" style="--glow:{info['glow']}66; --bg1:{bg1}; --bg2:{bg2}; --border:{info['color']};">
            <div style="font-size:2.2rem;">{ELEMENT_ICON[char['element']]}{CLASS_ICON[char['class']]}</div>
            <div class="rarity" style="color:{info['color']};">{info['label']}</div>
            <div class="name">{char['name']} {badge}</div>
            <div class="title">{char['title']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# 사이드바
# ============================================================
with st.sidebar:
    st.header("🔮 소환사 정보")
    st.metric("마력 결정", f"{st.session_state.crystals:,} 💎")
    st.metric("누적 소환 횟수", st.session_state.pull_count)
    pity_left = max(PITY_HARD - st.session_state.pity_5, 0)
    st.markdown(
        f"""<div class="pity-box">천장까지 <b>{pity_left}</b>회 남음<br>
        (현재 {st.session_state.pity_5}/{PITY_HARD})</div>""",
        unsafe_allow_html=True,
    )
    st.divider()
    if st.button("💎 마력 결정 충전 (테스트용 +5000)"):
        st.session_state.crystals += 5000
        st.rerun()
    if st.button("🗑️ 데이터 초기화"):
        for k in ["crystals", "pity_5", "pull_count", "inventory", "history", "last_results"]:
            del st.session_state[k]
        st.rerun()

# ============================================================
# 메인 화면
# ============================================================
st.title("🔮 아르카니아: 소환의 서")
st.caption("오리지널 판타지 육성 시뮬레이션 — 다섯 원소의 힘을 지닌 동료를 소환하세요")

tab1, tab2, tab3 = st.tabs(["✨ 소환", "🎒 보유 동료", "📜 소환 기록"])

# ---------------- 소환 탭 ----------------
with tab1:
    feat = next(c for c in CHARACTERS if c["name"] == FEATURED_CHAR)
    col_banner, col_info = st.columns([2, 1])
    with col_banner:
        st.subheader(f"픽업 배너: 「{feat['title']} {feat['name']}」")
        render_card(feat)
        st.caption("이번 배너 5성 등장 시 50% 확률로 픽업 캐릭터 확정")
    with col_info:
        st.markdown("**등급별 확률**")
        for r in (5, 4, 3):
            info = RARITY_INFO[r]
            st.write(f"{info['label']}  —  {info['rate']*100:.1f}%")
        st.markdown(f"- 70회부터 5성 확률 점차 상승 (소프트 천장)\n- {PITY_HARD}회 소환 시 5성 확정 (하드 천장)")

    st.divider()
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        pull1 = st.button(f"1회 소환 ({SINGLE_COST} 💎)", use_container_width=True)
    with c2:
        pull10 = st.button(f"10회 소환 ({TEN_COST} 💎)", use_container_width=True, type="primary")

    if pull1:
        if st.session_state.crystals < SINGLE_COST:
            st.error("마력 결정이 부족합니다!")
        else:
            st.session_state.crystals -= SINGLE_COST
            with st.spinner("소환진이 빛나고 있습니다..."):
                time.sleep(0.6)
            do_pull(1)

    if pull10:
        if st.session_state.crystals < TEN_COST:
            st.error("마력 결정이 부족합니다!")
        else:
            st.session_state.crystals -= TEN_COST
            with st.spinner("열 개의 소환진이 공명합니다..."):
                time.sleep(0.8)
            do_pull(10)

    if st.session_state.last_results:
        st.divider()
        st.subheader("소환 결과")
        results = st.session_state.last_results
        best = max(r["rarity"] for r in results)
        if best == 5:
            st.balloons()
        cols = st.columns(5)
        for i, char in enumerate(results):
            with cols[i % 5]:
                render_card(char)

# ---------------- 보유 동료 탭 ----------------
with tab2:
    if not st.session_state.inventory:
        st.info("아직 소환한 동료가 없습니다. 소환 탭에서 첫 동료를 만나보세요!")
    else:
        st.subheader(f"보유 동료 ({len(st.session_state.inventory)} / {len(CHARACTERS)} 종류)")
        owned_sorted = sorted(
            st.session_state.inventory.items(),
            key=lambda x: -next(c["rarity"] for c in CHARACTERS if c["name"] == x[0]),
        )
        cols = st.columns(5)
        for i, (name, count) in enumerate(owned_sorted):
            char = next(c for c in CHARACTERS if c["name"] == name)
            with cols[i % 5]:
                render_card(char)
                st.caption(f"보유 수: {count}개 (중복 시 '공명석'으로 각성 강화 예정)")

# ---------------- 소환 기록 탭 ----------------
with tab3:
    if not st.session_state.history:
        st.info("소환 기록이 없습니다.")
    else:
        st.subheader("최근 소환 기록 (최신순)")
        for char in reversed(st.session_state.history[-50:]):
            info = RARITY_INFO[char["rarity"]]
            st.markdown(
                f"- <span style='color:{info['color']}'>{info['label']}</span> "
                f"{ELEMENT_ICON[char['element']]}{CLASS_ICON[char['class']]} "
                f"**{char['name']}** ({char['title']})",
                unsafe_allow_html=True,
            )
