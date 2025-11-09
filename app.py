# app.py — Chrome 우선 / 예전 방식 복귀본
# - 1초마다 time.sleep → st.rerun() (메인 흐름에서만)
# - 자동 넘김: 남은 시간이 0이 되면 다음 카드로
# - 모드 1) 가나 보기(자동)  2) 한국어 보기(라벨만 표시)
# - 콜백 내부에는 st.rerun() 호출하지 않음
# - 카드 넘김 시 click.wav 사운드 재생

import time
import random
import base64
from pathlib import Path
import streamlit as st

st.set_page_config(page_title="장태순 여사님 일본어 테스트", page_icon="🇯🇵", layout="centered")

# ===== 데이터 =====
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

TOTAL = 20
LIMIT_SEC = 7

# ===== 유틸 =====
def build_pool_dict(use_hira, use_kata, use_daku):
    pool = {}
    if use_hira:
        pool.update(HIRAGANA_BASE)
        if use_daku: pool.update(HIRAGANA_DAKUTEN)
    if use_kata:
        pool.update(KATAKANA_BASE)
        if use_daku: pool.update(KATAKANA_DAKUTEN)
    return pool

def build_kana_cards(use_hira, use_kata, use_daku):
    d = build_pool_dict(use_hira, use_kata, use_daku)
    items = list(d.keys())
    random.shuffle(items)
    return [{"kana": k} for k in items[:TOTAL]]

def build_korean_cards(use_hira, use_kata, use_daku):
    d = build_pool_dict(use_hira, use_kata, use_daku)  # kana->romaji
    romas = list(set(d.values()))
    random.shuffle(romas)
    # 역매핑
    r2hira, r2kata = {}, {}
    for k, r in HIRAGANA_BASE.items(): r2hira[r] = k
    for k, r in HIRAGANA_DAKUTEN.items(): r2hira[r] = k
    for k, r in KATAKANA_BASE.items(): r2kata[r] = k
    for k, r in KATAKANA_DAKUTEN.items(): r2kata[r] = k

    cards = []
    for r in romas:
        kor = ROMA2HANGUL.get(r, r)
        enabled = []
        if use_hira and r in r2hira: enabled.append("히라가나")
        if use_kata and r in r2kata: enabled.append("가타카나")
        if not enabled: continue
        label = random.choice(enabled) if len(enabled) > 1 else enabled[0]
        cards.append({"kor": kor, "label": label})
        if len(cards) >= TOTAL: break
    return cards

def remaining_time():
    return max(0, LIMIT_SEC - int(time.time() - st.session_state.start_time))

def play_sound_if_needed():
    """카드 넘김 시 사운드 재생"""
    if st.session_state.get("play_sound", False):
        st.session_state.play_sound = False
        sound_file = Path("click.wav")
        if sound_file.exists():
            audio_bytes = sound_file.read_bytes()
            audio_b64 = base64.b64encode(audio_bytes).decode()
            audio_html = f"""
                <audio autoplay>
                    <source src="data:audio/wav;base64,{audio_b64}" type="audio/wav">
                </audio>
            """
            st.markdown(audio_html, unsafe_allow_html=True)

def go_next():
    st.session_state.idx += 1
    st.session_state.start_time = time.time()
    st.session_state.play_sound = True

# ===== 사이드바 =====
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
            st.error("사용 가능한 카드가 없습니다. 옵션을 조정해 보세요.")
        else:
            st.session_state.cards = cards
            st.session_state.idx = 0
            st.session_state.started = True
            st.session_state.mode = mode
            st.session_state.start_time = time.time()
            st.session_state.skip = False
            st.rerun()

st.markdown(
    "<div style='text-align:center;font-size:28px;font-weight:800;'>장태순 여사님 일본어 테스트</div>",
    unsafe_allow_html=True,
)

if not st.session_state.get("started", False):
    # 홈 이미지가 있으면 보여주기 (선택)
    for p in ["home.png","home.jpg","assets/home.png","assets/home.jpg"]:
        fp = Path(p)
        if fp.exists():
            b64 = base64.b64encode(fp.read_bytes()).decode("ascii")
            mime = "image/png" if fp.suffix.lower()==".png" else "image/jpeg"
            st.markdown(
                f"<div style='display:flex;justify-content:center'><img src='data:{mime};base64,{b64}' style='max-width:66%;border-radius:16px;box-shadow:0 6px 24px rgba(0,0,0,0.12)'/></div>",
                unsafe_allow_html=True,
            )
            break
    else:
        st.info("좌측 옵션을 선택하고 **새 세션 시작하기**를 눌러주세요.")
    st.stop()

# ===== 진행 영역 =====
idx = st.session_state.idx
cards = st.session_state.cards
mode = st.session_state.mode

# 종료 화면
if idx >= len(cards):
    st.subheader("끝!")
    st.write(f"총 {TOTAL}개 완료했습니다.")
    st.stop()

# 상단: 진행/타이머
c1, c2 = st.columns([1,1])
with c1: st.markdown(f"**문항 {idx+1}/{TOTAL}**")
with c2: st.markdown(f"**남은 시간: {remaining_time()}s**")
st.markdown("---")

# 사운드 재생
play_sound_if_needed()

# 시간 만료 시 자동 다음
if remaining_time() <= 0:
    go_next()
    st.rerun()

# 카드 표시
if mode.startswith("가나"):
    kana = cards[idx]["kana"]
    st.markdown(f"<div style='text-align:center;font-size:220px;font-weight:900'>{kana}</div>", unsafe_allow_html=True)
else:
    card = cards[idx]
    st.markdown(f"<div style='text-align:center;font-size:220px;font-weight:900'>{card['kor']}</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='text-align:center;color:#666'>( {card['label']} )</div>", unsafe_allow_html=True)

# 스킵 버튼 (콜백 내부 rerun 없음)
def _skip():
    st.session_state.skip = True
st.button("다음 ▶", on_click=_skip, use_container_width=True)

# 스킵 처리는 메인 흐름에서
if st.session_state.get("skip"):
    st.session_state.skip = False
    go_next()
    st.rerun()

st.markdown("---")
st.caption("7초마다 자동으로 다음 카드로 넘어갑니다. 필요하면 '다음 ▶'으로 스킵하세요.")

# 1초마다 화면 갱신 (콜백 바깥에서만 호출)
time.sleep(1)
st.rerun()
