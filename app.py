import time
import random
import streamlit as st

st.set_page_config(page_title="장태순 여사님 전용 테스트", page_icon="🇯🇵", layout="centered")

# -----------------------------
# Data
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

TOTAL = 20           # 세션 길이
LIMIT_SEC = 7        # 글자당 표시 시간(초)

def build_pool(use_hira, use_kata, use_daku):
    decks = []
    if use_hira:
        decks.append(HIRAGANA_BASE)
        if use_daku:
            decks.append(HIRAGANA_DAKUTEN)
    if use_kata:
        decks.append(KATAKANA_BASE)
        if use_daku:
            decks.append(KATAKANA_DAKUTEN)
    pool = {}
    for d in decks:
        pool.update(d)
    return pool

# -----------------------------
# Sidebar (Options)
# -----------------------------
with st.sidebar:
    st.header("옵션")
    use_hira = st.checkbox("히라가나", value=True)
    use_kata = st.checkbox("가타카나", value=True)
    use_daku = st.checkbox("탁음/반탁음 포함", value=True)
    st.caption(f"세션: 무작위 {TOTAL}문항 · 글자당 {LIMIT_SEC}초")

    if "started" not in st.session_state:
        st.session_state.started = False

    if st.button("새 세션 시작하기", type="primary"):
        pool = build_pool(use_hira, use_kata, use_daku)
        if not pool:
            st.error("히라가나 또는 가타카나를 선택하세요.")
        else:
            items = list(pool.items())
            random.shuffle(items)
            picked = items[:TOTAL]
            st.session_state.cards = [{"kana": k} for k, _ in picked]  # 표시할 글자만 저장
            st.session_state.idx = 0
            st.session_state.started = True
            st.session_state.start_time = time.time()  # 현재 카드 시작시간
            # 콜백에서는 rerun 호출하지 않음 (no-op)

st.title("장태순 여사님 전용 테스트")

if not st.session_state.get("started", False):
    st.info("좌측 사이드바에서 옵션을 선택하고 **새 세션 시작하기**를 눌러주세요.")
    st.stop()

# -----------------------------
# Helpers
# -----------------------------
def remaining_time():
    elapsed = int(time.time() - st.session_state.start_time)
    return max(0, LIMIT_SEC - elapsed)

def go_next():
    st.session_state.idx += 1
    st.session_state.start_time = time.time()

# -----------------------------
# Main area
# -----------------------------
idx = st.session_state.idx
cards = st.session_state.cards

# 종료 화면
if idx >= len(cards):
    st.subheader("끝!")
    st.write(f"총 {TOTAL}개 완료했습니다.")
    st.success("다시 하려면 사이드바에서 **새 세션 시작하기**를 눌러주세요.")
    st.stop()

card = cards[idx]

# 상단: 진행/타이머
c1, c2 = st.columns([1,1])
with c1:
    st.markdown(f"**문항 {idx+1}/{TOTAL}**")
with c2:
    st.markdown(f"**남은 시간: {remaining_time()}s**")

st.markdown("---")
st.markdown(
    f"<div style='text-align:center;font-size:140px;font-weight:800'>{card['kana']}</div>",
    unsafe_allow_html=True,
)

# 즉시 넘기기: 상태만 변경 (콜백 내 rerun 금지)
st.button("다음 ▶", on_click=go_next)

st.markdown("---")
st.caption("입력 없이 7초마다 자동으로 다음 글자가 표시됩니다. 필요하면 '다음' 버튼으로 스킵하세요.")

# ----- 자동 카운트다운 처리 -----
# 1) 시간이 끝났으면 다음 카드로 진행
if remaining_time() <= 0:
    go_next()
    st.rerun()

# 2) 아직 시간이 남아있으면 1초 후 자동 갱신 (메인 흐름에서만 rerun)
time.sleep(1)
st.rerun()
