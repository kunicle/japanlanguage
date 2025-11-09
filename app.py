import time
import random
import streamlit as st

st.set_page_config(page_title="한국어 발음 플래시카드", page_icon="🇯🇵", layout="centered")

# -----------------------------
# Kana Data (기존 베이스 + 탁/반탁음)
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
    "バ":"ba","비":"bi","ブ":"bu","ベ":"be","ボ":"bo",
    "パ":"pa","ピ":"pi","プ":"pu","ペ":"pe","ポ":"po",
}
# 오타 수정: KATAKANA_DAKUTEN의 '비' -> 'ビ'
KATAKANA_DAKUTEN["ビ"] = KATAKANA_DAKUTEN.pop("비")

# -----------------------------
# 한국어(한글) 근사 발음 매핑 (단음 기반)
#   - 학습을 돕기 위한 단순화 버전입니다.
# -----------------------------
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

# -----------------------------
# 설정값
# -----------------------------
TOTAL = 20        # 카드 개수
LIMIT_SEC = 7     # 카드당 표시 시간(초)

# -----------------------------
# 유틸: 로마자→(히라, 가타) 역매핑 테이블 만들기
# -----------------------------
def build_roma2kana():
    r2k = {}
    # 우선 히라/가타 기본 → 탁/반탁 순서로 채워 넣습니다.
    for k, r in HIRAGANA_BASE.items():
        r2k.setdefault(r, {})["hira"] = k
    for k, r in KATAKANA_BASE.items():
        r2k.setdefault(r, {})["kata"] = k
    for k, r in HIRAGANA_DAKUTEN.items():
        r2k.setdefault(r, {})["hira"] = k
    for k, r in KATAKANA_DAKUTEN.items():
        r2k.setdefault(r, {})["kata"] = k
    # 일부 중복(예: 'o')은 최초 매핑을 우선합니다.
    return r2k

ROMA2KANA = build_roma2kana()

# -----------------------------
# 덱 구성: 한국어(한글) 발음 카드
#   - 풀(히라/가타/탁음 포함 여부)에 따라 로마자 집합 선택
#   - 카드 = { "kor": "아/카/시...", "hira": "か", "kata": "カ" }
# -----------------------------
def build_korean_cards(use_hira, use_kata, use_daku):
    # 사용할 로마자 키 집합 만들기
    pool = {}
    if use_hira:
        pool.update(HIRAGANA_BASE)
        if use_daku:
            pool.update(HIRAGANA_DAKUTEN)
    if use_kata:
        pool.update(KATAKANA_BASE)
        if use_daku:
            pool.update(KATAKANA_DAKUTEN)

    # 로마자 목록(중복 제거)
    romas = list(set(pool.values()))
    random.shuffle(romas)

    cards = []
    for r in romas:
        # 한국어 한글 표기 (없으면 로마자 그대로)
        kor = ROMA2HANGUL.get(r, r)
        hira = ROMA2KANA.get(r, {}).get("hira", "")
        kata = ROMA2KANA.get(r, {}).get("kata", "")
        cards.append({"kor": kor, "hira": hira, "kata": kata})

    # 원하는 개수만큼 잘라서 리턴
    return cards[:TOTAL]

# -----------------------------
# 사이드바 옵션
# -----------------------------
with st.sidebar:
    st.header("옵션")
    use_hira = st.checkbox("히라가나 포함", value=True)
    use_kata = st.checkbox("가타카나 포함", value=True)
    use_daku = st.checkbox("탁음/반탁음 포함", value=True)

    show_answer = st.checkbox("정답(가나) 보기", value=False)
    answer_script = st.selectbox("정답 표기 스크립트", ["히라가나", "가타카나", "둘 다"], index=0, disabled=not show_answer)

    st.caption(f"세션: 무작위 {TOTAL}문항 · 카드당 {LIMIT_SEC}초")

    if "started" not in st.session_state:
        st.session_state.started = False

    if st.button("새 세션 시작하기", type="primary"):
        # 카드 생성 (한국어 발음 중심)
        cards = build_korean_cards(use_hira, use_kata, use_daku)
        if not cards:
            st.error("사용할 스크립트를 하나 이상 선택하세요.")
        else:
            st.session_state.cards = cards
            st.session_state.idx = 0
            st.session_state.started = True
            st.session_state.start_time = time.time()
            st.session_state.show_answer = show_answer
            st.session_state.answer_script = answer_script
            # 콜백에서는 rerun 호출하지 않음

st.title("한국어 발음 플래시카드")

if not st.session_state.get("started", False):
    st.info("사이드바에서 옵션을 설정하고 **새 세션 시작하기**를 눌러주세요.")
    st.stop()

# -----------------------------
# 타이머/진행 유틸
# -----------------------------
def remaining_time():
    elapsed = int(time.time() - st.session_state.start_time)
    return max(0, LIMIT_SEC - elapsed)

def go_next():
    st.session_state.idx += 1
    st.session_state.start_time = time.time()

# -----------------------------
# 메인
# -----------------------------
idx = st.session_state.idx
cards = st.session_state.cards
show_answer = st.session_state.get("show_answer", False)
answer_script = st.session_state.get("answer_script", "히라가나")

# 종료 화면
if idx >= len(cards):
    st.subheader("끝!")
    st.write(f"총 {TOTAL}개 완료했습니다.")
    st.success("다시 하려면 사이드바에서 **새 세션 시작하기**를 누르세요.")
    st.stop()

card = cards[idx]

# 상단: 진행/타이머
c1, c2 = st.columns([1,1])
with c1:
    st.markdown(f"**문항 {idx+1}/{TOTAL}**")
with c2:
    st.markdown(f"**남은 시간: {remaining_time()}s**")

st.markdown("---")

# 7초가 지나면 자동 다음
if remaining_time() <= 0:
    go_next()
    st.rerun()

# 한국어 발음(한글) 크게 표시
st.markdown(
    f"<div style='text-align:center;font-size:140px;font-weight:800'>{card['kor']}</div>",
    unsafe_allow_html=True
)

# (선택) 정답 가나 표시
if show_answer:
    ans = ""
    if answer_script == "히라가나":
        ans = card["hira"] or "(히라가나 없음)"
    elif answer_script == "가타카나":
        ans = card["kata"] or "(가타카나 없음)"
    else:
        hira = card["hira"] or "—"
        kata = card["kata"] or "—"
        ans = f"{hira} / {kata}"
    st.info(f"정답: {ans}")

# 즉시 스킵 버튼 (콜백에서 rerun 사용 안 함)
st.button("다음 ▶", on_click=go_next)

st.markdown("---")
st.caption("입력 없이 7초마다 자동으로 다음 카드로 넘어갑니다. 필요하면 '다음 ▶'으로 스킵하세요.")

# 초 단위 자동 갱신 (메인 플로우에서만 호출)
time.sleep(1)
st.rerun()
