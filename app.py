# app.py — 두 모드 + 철컥 사운드 + 사이드바 숨기기 + 큰 글씨(고정 220px)
# 1) 가나 보기(자동 넘김, 입력 없음)
# 2) 한국어 보기(한글 발음 + "(히라가나/가타카나)" 라벨만, 자동 넘김)
# Streamlit 1.39: 콜백 내부 st.rerun() 사용하지 않고, 메인 흐름 끝에서만 호출

import time
import random
import base64
from pathlib import Path
import streamlit as st

st.set_page_config(page_title="장태순 여사님 일본어 테스트", page_icon="🇯🇵", layout="centered")

# ────────────────────────────────────────────────────────────────────────────
# 고정 표시 크기/타이밍
# ────────────────────────────────────────────────────────────────────────────
FONT_PX = 220   # 카드 글자 크기 (고정, iPad 가로보기 기준 큼직하게)
TOTAL   = 20    # 카드 개수
LIMIT_SEC = 7   # 카드당 시간(초)

# ────────────────────────────────────────────────────────────────────────────
# 철컥 사운드: 저장소 루트에 click.wav 업로드해 사용 (짧은 효과음 권장)
#   - iPad/Safari는 사용자 상호작용 후에만 자동재생 허용 → 아래 체크박스 한 번 눌러 주세요.
# ────────────────────────────────────────────────────────────────────────────
CLICK_WAV_PATHS = ["click.wav", "assets/click.wav"]  # 선호 경로들

@st.cache_resource(show_spinner=False)
def _load_click_b64():
    for p in CLICK_WAV_PATHS:
        fp = Path(p)
        if fp.exists() and fp.is_file():
            data = fp.read_bytes()
            return base64.b64encode(data).decode("ascii")
    return None  # 파일이 없으면 None

def play_click_if_needed():
    # 다음 카드로 넘어갈 때만 1회 재생
    if st.session_state.get("play_click", False) and st.session_state.get("sound_enabled", False):
        st.session_state.play_click = False
        b64 = _load_click_b64()
        if b64:  # 파일이 있으면 시도
            st.markdown(
                f"""
                <audio autoplay>
                  <source src="data:audio/wav;base64,{b64}" type="audio/wav">
                </audio>
                """,
                unsafe_allow_html=True,
            )

# ────────────────────────────────────────────────────────────────────────────
# 데이터
# ────────────────────────────────────────────────────────────────────────────
HIRAGANA_BASE = {
    "あ":"a","い":"i","う":"u","え":"e","お":"o",
    "か":"ka","き":"ki","く":"ku","け":"ke","こ":"ko",
    "さ":"sa","し":"shi","す":"su","せ":"se","そ":"so",
    "た":"ta","ち":"chi","つ":"tsu","て":"te","と":"to",
    "な":"na","に":"ni","ぬ":"nu","ね":"ne","の":"no",
    "は":"ha","ひ":"hi","ふ":"fu","へ":"he","ほ":"ho",
    "ま":"ma","み":"mi","む":"mu","め":"me","も":"mo",
    "や":"ya","ゆ":"yu","よ":"yo",
    "ら":"ra","り":"ri","る":"ru","れ":"re","ろ":"ro",
    "わ":"wa","를":"o","ん":"n",  # 오타 방지용: 아래 줄에서 '를' 수정
}
HIRAGANA_BASE["を"] = "o"  # 위 라인 오타 정정

KATAKANA_BASE = {
    "ア":"a","イ":"i","ウ":"u","エ":"e","オ":"o",
    "カ":"ka","キ":"ki","ク":"ku","ケ":"ke","コ":"ko",
    "サ":"sa","シ":"shi","ス":"su","セ":"se","ソ":"so",
    "タ":"ta","チ":"chi","ツ":"tsu","テ":"te","ト":"to",
    "ナ":"na","ニ":"ni","ヌ":"nu","ネ":"ne","ノ":"no",
    "ハ":"ha","ヒ":"hi","フ":"fu","ヘ":"he","ホ":"ho",
    "マ":"ma","ミ":"mi","ム":"mu","メ":"me","モ":"mo",
    "ヤ":"ya","ユ":"yu","ヨ":"yo",
    "ラ":"ra","リ":"ri","ル":"ru","レ":"re","ロ":"ro",
    "ワ":"wa","ヲ":"o","ン":"n",
}
HIRAGANA_DAKUTEN = {
    "が":"ga","ぎ":"gi","ぐ":"gu","げ":"ge","ご":"go",
    "ざ":"za","じ":"ji","ず":"zu","ぜ":"ze","ぞ":"zo",
    "だ":"da","ぢ":"ji","づ":"zu","で":"de","ど":"do",
    "ば":"ba","び":"bi","ぶ":"bu","べ":"be","ぼ":"bo",
    "ぱ":"pa","ぴ":"pi","ぷ":"pu","ぺ":"pe","ぽ":"po",
}
KATAKANA_DAKUTEN = {
    "ガ":"ga","ギ":"gi","グ":"gu","ゲ":"ge","ゴ":"go",
    "ザ":"za","ジ":"ji","ズ":"zu","ゼ":"ze","ゾ":"zo",
    "ダ":"da","ヂ":"ji","ヅ":"zu","デ":"de","ド":"do",
    "バ":"ba","ビ":"bi","ブ":"bu","ベ":"be","ボ":"bo",
    "パ":"pa","ピ":"pi","プ":"pu","ペ":"pe","ポ":"po",
}

ROMA2HANGUL = {
    "a":"아","i":"이","u":"우","e":"에","o":"오",
    "ka":"카","ki":"키","ku":"쿠","ke":"케","ko":"코",
    "sa":"사","shi":"시","su":"스","se":"세","so":"소",
    "ta":"타","chi":"치","tsu":"쓰","te":"테","to":"토",
    "na":"나","ni":"니","nu":"누","ne":"네","no":"노",
    "ha":"하","hi":"히","fu":"후","he":"헤","ho":"호",
    "ma":"마","mi":"미","mu":"무","me":"메","mo":"모",
    "ya":"야","yu":"유","yo":"요",
    "ra":"라","ri":"리","ru":"루","re":"레","ro":"로",
    "wa":"와","o":"오","n":"응",
    "ga":"가","gi":"기","gu":"구","ge":"게","go":"고",
    "za":"자","ji":"지","zu":"즈","ze":"제","zo":"조",
    "da":"다","de":"데","do":"도",
    "ba":"바","bi":"비","bu":"부","be":"베","bo":"보",
    "pa":"파","pi":"피","pu":"푸","pe":"페","po":"포",
}

# ────────────────────────────────────────────────────────────────────────────
# 역매핑: romaji -> {"hira":kana?, "kata":kana?}
# ────────────────────────────────────────────────────────────────────────────
def build_roma2kana():
    r2k = {}
    for k, r in HIRAGANA_BASE.items():
        r2k.setdefault(r, {})["hira"] = k
    for k, r in KATAKANA_BASE.items():
        r2k.setdefault(r, {})["kata"] = k
    for k, r in HIRAGANA_DAKUTEN.items():
        r2k.setdefault(r, {})["hira"] = k
    for k, r in KATAKANA_DAKUTEN.items():
        r2k.setdefault(r, {})["kata"] = k
    return r2k
ROMA2KANA = build_roma2kana()

# ────────────────────────────────────────────────────────────────────────────
# 덱 구성
# ────────────────────────────────────────────────────────────────────────────
def build_pool_dict(use_hira, use_kata, use_daku):
    pool = {}
    if use_hira:
        pool.update(HIRAGANA_BASE)
        if use_daku:
            pool.update(HIRAGANA_DAKUTEN)
    if use_kata:
        pool.update(KATAKANA_BASE)
        if use_daku:
            pool.update(KATAKANA_DAKUTEN)
    return pool  # kana->romaji

def build_kana_cards(use_hira, use_kata, use_daku):
    d = build_pool_dict(use_hira, use_kata, use_daku)
    items = list(d.keys())
    random.shuffle(items)
    return [{"kana": k} for k in items[:TOTAL]]

def build_korean_cards(use_hira, use_kata, use_daku):
    d = build_pool_dict(use_hira, use_kata, use_daku)  # kana->romaji
    romas = list(set(d.values()))
    random.shuffle(romas)
    cards = []
    for r in romas:
        kor = ROMA2HANGUL.get(r, r)
        hira = ROMA2KANA.get(r, {}).get("hira", "")
        kata = ROMA2KANA.get(r, {}).get("kata", "")
        enabled = []
        if use_hira and hira:
            enabled.append("hira")
        if use_kata and kata:
            enabled.append("kata")
        if not enabled:
            continue
        target_label = "히라가나" if "hira" in enabled and (len(enabled) == 1) else (
            "가타카나" if "kata" in enabled and (len(enabled) == 1) else random.choice(["히라가나","가타카나"])
        )
        cards.append({"kor": kor, "label": target_label, "hira": hira, "kata": kata})
        if len(cards) >= TOTAL:
            break
    return cards

# ────────────────────────────────────────────────────────────────────────────
# 초기 상태
# ────────────────────────────────────────────────────────────────────────────
if "started" not in st.session_state:
    st.session_state.started = False
if "fullscreen" not in st.session_state:
    st.session_state.fullscreen = False
if "sound_enabled" not in st.session_state:
    st.session_state.sound_enabled = False
if "play_click" not in st.session_state:
    st.session_state.play_click = False

# ────────────────────────────────────────────────────────────────────────────
# 상단 간단 컨트롤: 사운드 토글 / 사이드바 토글
# ────────────────────────────────────────────────────────────────────────────
top_c1, top_c2 = st.columns([1,1])
with top_c1:
    st.checkbox("🔊 사운드 활성화 (iPad는 한 번 눌러주세요)", key="sound_enabled")
with top_c2:
    def toggle_sidebar():
        st.session_state.fullscreen = not st.session_state.fullscreen
    label = "사이드바 숨기기" if not st.session_state.fullscreen else "사이드바 보이기"
    st.button(label, on_click=toggle_sidebar)

# 사이드바 숨김 CSS
if st.session_state.fullscreen:
    st.markdown("""
        <style>
        [data-testid="stSidebar"] {display: none;}
        .block-container {padding-top: 0.5rem;}
        </style>
    """, unsafe_allow_html=True)

# ────────────────────────────────────────────────────────────────────────────
# 사이드바 (모드/덱 선택)
# ────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("옵션")
    mode = st.radio("모드 선택", ["가나 보기(자동 넘김)", "한국어 보기(라벨만 표시)"], index=0)
    use_hira = st.checkbox("히라가나 포함", value=True)
    use_kata = st.checkbox("가타카나 포함", value=True)
    use_daku = st.checkbox("탁음/반탁음 포함", value=True)
    st.caption(f"세션: 무작위 {TOTAL}문항 · 카드당 {LIMIT_SEC}초")

    if st.button("새 세션 시작하기", type="primary"):
        if mode.startswith("가나"):
            cards = build_kana_cards(use_hira, use_kata, use_daku)
        else:
            cards = build_korean_cards(use_hira, use_kata, use_daku)

        if not cards:
            st.error("사용 가능한 카드가 없습니다. 스크립트 옵션을 조정해 보세요.")
        else:
            st.session_state.cards = cards
            st.session_state.idx = 0
            st.session_state.started = True
            st.session_state.mode = mode
            st.session_state.start_time = time.time()

# 제목
st.title("장태순 여사님 일본어 테스트")

if not st.session_state.get("started", False):
    st.info("옵션을 선택하고 **새 세션 시작하기**를 눌러주세요.")
    st.stop()

# 공통 헬퍼
def remaining_time():
    elapsed = int(time.time() - st.session_state.start_time)
    return max(0, LIMIT_SEC - elapsed)

def go_next():
    st.session_state.idx += 1
    st.session_state.start_time = time.time()
    st.session_state.play_click = True  # 다음 렌더에서 철컥 재생

# 상태 단축
idx = st.session_state.idx
cards = st.session_state.cards
mode = st.session_state.mode

# 종료 화면
if idx >= len(cards):
    play_click_if_needed()
    st.subheader("끝!")
    st.write(f"총 {TOTAL}개 완료했습니다.")
    st.success("다시 하려면 사이드바에서 **새 세션 시작하기**를 누르세요.")
    st.stop()

# 상단 진행/타이머
c1, c2 = st.columns([1,1])
with c1:
    st.markdown(f"**문항 {idx+1}/{TOTAL}**")
with c2:
    st.markdown(f"**남은 시간: {remaining_time()}s**")
st.markdown("---")

# 사운드 재생(필요 시)
play_click_if_needed()

# 모드 A: 가나 보기
if mode.startswith("가나"):
    kana = cards[idx]["kana"]

    if remaining_time() <= 0:
        go_next()
        st.rerun()

    st.markdown(
        f"<div style='text-align:center;font-size:{FONT_PX}px;font-weight:900'>{kana}</div>",
        unsafe_allow_html=True
    )

    st.button("다음 ▶", on_click=go_next)

    st.markdown("---")
    st.caption("입력 없이 7초마다 자동으로 다음 카드로 넘어갑니다. 필요하면 '다음 ▶'으로 스킵하세요.")

    time.sleep(1)
    st.rerun()

# 모드 B: 한국어 보기(라벨만)
else:
    card = cards[idx]
    kor = card["kor"]
    label = card["label"]

    if remaining_time() <= 0:
        go_next()
        st.rerun()

    st.markdown(
        f"<div style='text-align:center;font-size:{FONT_PX}px;font-weight:900'>{kor}</div>",
        unsafe_allow_html=True
    )
    st.markdown(
        f"<div style='text-align:center;font-size:22px;color:#666'>( {label} )</div>",
        unsafe_allow_html=True
    )

    st.button("다음 ▶", on_click=go_next)

    st.markdown("---")
    st.caption("7초마다 자동으로 다음 카드로 넘어갑니다. 필요하면 '다음 ▶'으로 스킵하세요.")

    time.sleep(1)
    st.rerun()
