# app.py — 두 모드
# 1) 가나 보기(자동 넘김, 입력 없음)
# 2) 한국어 보기(한글 발음 + "(히라가나/가타카나)" 라벨만 표시, 자동 넘김)
# Streamlit 1.39: 콜백 내부에서 st.rerun() 사용하지 않음

import time
import random
import streamlit as st

st.set_page_config(page_title="장태순 여사님 일본어 테스트", page_icon="🇯🇵", layout="centered")

# -----------------------------
# Kana Data (기본 + 탁/반탁음)
# -----------------------------
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
    "わ":"wa","を":"o","ん":"n",
}
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

# 한국어(한글) 근사 발음 매핑 (학습용 단순화)
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

TOTAL = 20        # 카드 개수
LIMIT_SEC = 7     # 카드당 시간(초)

# -----------------------------
# 역매핑: romaji -> {"hira":kana?, "kata":kana?}
# -----------------------------
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

# -----------------------------
# 덱 구성
# -----------------------------
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
    # 가나 보기 모드: 화면에 '가나'만 표시
    d = build_pool_dict(use_hira, use_kata, use_daku)
    items = list(d.keys())
    random.shuffle(items)
    return [{"kana": k} for k in items[:TOTAL]]

def build_korean_cards(use_hira, use_kata, use_daku):
    # 한국어 보기 모드: 한글 발음 + "(히라가나/가타카나)" 라벨만 표시
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
        target = random.choice(enabled) if len(enabled) > 1 else enabled[0]
        label = "히라가나" if target == "hira" else "가타카나"
        cards.append({
            "kor": kor,         # 크게 보여줄 한글 발음
            "label": label,     # (히라가나/가타카나) 라벨만
            # 참고용으로 실제 표기가 필요하면 아래 두 값을 사용 가능
            "hira": hira,
            "kata": kata,
        })
        if len(cards) >= TOTAL:
            break
    return cards

# -----------------------------
# 사이드바 옵션
# -----------------------------
with st.sidebar:
    st.header("옵션")
    mode = st.radio("모드 선택", ["가나 보기(자동 넘김)", "한국어 보기(라벨만 표시)"], index=0)
    use_hira = st.checkbox("히라가나 포함", value=True)
    use_kata = st.checkbox("가타카나 포함", value=True)
    use_daku = st.checkbox("탁음/반탁음 포함", value=True)
    st.caption(f"세션: 무작위 {TOTAL}문항 · 카드당 {LIMIT_SEC}초")

    if "started" not in st.session_state:
        st.session_state.started = False

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

st.title("장태순 여사님 일본어 테스트")

if not st.session_state.get("started", False):
    st.info("옵션을 선택하고 **새 세션 시작하기**를 눌러주세요.")
    st.stop()

# -----------------------------
# Helper & 진행 제어
# -----------------------------
def remaining_time():
    elapsed = int(time.time() - st.session_state.start_time)
    return max(0, LIMIT_SEC - elapsed)

def go_next():
    st.session_state.idx += 1
    st.session_state.start_time = time.time()

idx = st.session_state.idx
cards = st.session_state.cards
mode = st.session_state.mode

# 종료 화면
if idx >= len(cards):
    st.subheader("끝!")
    st.write(f"총 {TOTAL}개 완료했습니다.")
    st.success("다시 하려면 사이드바에서 **새 세션 시작하기**를 누르세요.")
    st.stop()

# 공통 상단 UI
c1, c2 = st.columns([1,1])
with c1:
    st.markdown(f"**문항 {idx+1}/{TOTAL}**")
with c2:
    st.markdown(f"**남은 시간: {remaining_time()}s**")
st.markdown("---")

# -----------------------------
# 모드 A: 가나 보기(자동 넘김)
# -----------------------------
if mode.startswith("가나"):
    kana = cards[idx]["kana"]

    # 시간 초과 시 자동 다음
    if remaining_time() <= 0:
        go_next()
        st.rerun()

    st.markdown(
        f"<div style='text-align:center;font-size:150px;font-weight:800'>{kana}</div>",
        unsafe_allow_html=True
    )

    st.button("다음 ▶", on_click=go_next)

    st.markdown("---")
    st.caption("입력 없이 7초마다 자동으로 다음 카드로 넘어갑니다. 필요하면 '다음 ▶'으로 스킵하세요.")

    time.sleep(1)
    st.rerun()

# -----------------------------
# 모드 B: 한국어 보기(라벨만 표시)
#   - 한국어(한글) 발음 크게 표시
#   - 그 아래 작은 글씨로 (히라가나) 또는 (가타카나) 라벨만 보여줌
#   - 7초 자동 넘김 + 스킵 버튼
# -----------------------------
else:
    card = cards[idx]
    kor = card["kor"]
    label = card["label"]  # "히라가나" or "가타카나"

    # 시간 초과 시 자동 다음
    if remaining_time() <= 0:
        go_next()
        st.rerun()

    st.markdown(
        f"<div style='text-align:center;font-size:140px;font-weight:800'>{kor}</div>",
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
