import random
import time
import streamlit as st

st.set_page_config(page_title="장태순 여사님을 위한 일본어 기초 테스트", page_icon="🀄", layout="centered")

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

EQUIV = {
    "shi": {"si"}, "chi": {"ti"}, "tsu": {"tu"},
    "ji": {"zi"}, "fu": {"hu"}, "o": {"wo"}
}

TOTAL = 20
LIMIT_SEC = 7

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
    st.caption("세션: 무작위 20문항 · 카드당 7초")

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
            st.session_state.cards = [{"kana": k, "romaji": v} for k, v in picked]
            st.session_state.idx = 0
            st.session_state.correct = 0
            st.session_state.revealed = False
            st.session_state.started = True
            st.session_state.start_time = time.time()
            st.session_state.answer = ""
            st.rerun()

st.title("Kana Flashcards (ひらがな・カタカナ)")

if not st.session_state.get("started", False):
    st.info("좌측 사이드바에서 옵션을 선택하고 **새 세션 시작하기**를 눌러주세요.")
    st.stop()

# -----------------------------
# Session helpers
# -----------------------------
def remaining_time():
    elapsed = int(time.time() - st.session_state.start_time)
    return max(0, LIMIT_SEC - elapsed)

def reveal(auto=False):
    if st.session_state.revealed:
        return
    st.session_state.revealed = True
    card = st.session_state.cards[st.session_state.idx]
    user = st.session_state.answer.strip().lower()
    romaji = card["romaji"]
    ok = user == romaji or (romaji in EQUIV and user in EQUIV[romaji])
    card["user_answer"] = user
    card["is_correct"] = ok
    if ok:
        st.session_state.correct += 1

def next_card():
    st.session_state.idx += 1
    st.session_state.revealed = False
    st.session_state.answer = ""
    st.session_state.start_time = time.time()

# -----------------------------
# Main area
# -----------------------------
idx = st.session_state.idx
cards = st.session_state.cards

# Results screen
if idx >= len(cards):
    score = f"{st.session_state.correct}/{TOTAL} 정답 ({round(st.session_state.correct/TOTAL*100)}%)"
    st.subheader("결과")
    st.write(score)
    wrong = [c for c in cards if not c.get("is_correct", False)]
    if wrong:
        with st.expander("틀린 항목 펼치기"):
            for c in wrong:
                st.write(f"{c['kana']} → {c['romaji']}  (입력: {c.get('user_answer','')})")
    st.success("새 세션을 시작하려면 사이드바에서 설정 후 버튼을 눌러주세요.")
    st.stop()

card = cards[idx]

# Timer / Progress
col1, col2 = st.columns([1,1])
with col1:
    st.markdown(f"**문항 {idx+1}/{TOTAL}**")
with col2:
    st.markdown(f"**남은 시간: {remaining_time()}s**")

# Auto-refresh countdown
if not st.session_state.revealed and remaining_time() > 0:
    st.rerun()

# Auto reveal when time expires
if remaining_time() <= 0 and not st.session_state.revealed:
    reveal(auto=True)

st.markdown("---")
st.markdown(f"<div style='text-align:center;font-size:120px;font-weight:700'>{card['kana']}</div>", unsafe_allow_html=True)

# Answer form
if not st.session_state.revealed:
    st.session_state.answer = st.text_input("로마자 입력 후 Enter", value=st.session_state.answer, key="answer_box")
    submit = st.button("제출", on_click=reveal)
else:
    romaji = card["romaji"]
    user = st.session_state.answer.strip().lower()
    ok = user == romaji or (romaji in EQUIV and user in EQUIV[romaji])
    if ok:
        st.success(f"정답! → {romaji}")
    else:
        st.error(f"오답  정답: {romaji}")
    st.button("다음 문제", on_click=next_card)

st.markdown("---")
st.caption("Tip: Enter 키로 제출할 수 있어요. 시간 종료 시 자동 공개 후 다음 문제 버튼이 활성화됩니다.")
