import time
import random
from io import BytesIO

import streamlit as st
from gtts import gTTS

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

# 한국어 근사 발음 (오디오용) — 단음 기준 간략 매핑
# (학습용 단순화: tsu=쓰, fu=후, wo=오, ん=응)
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
    return pool  # dict: kana -> romaji

def get_korean_pron(romaji: str) -> str:
    # 단순화 매핑 (없으면 로마자 그대로 읽기)
    return ROMA2HANGUL.get(romaji, romaji)

def tts_bytes_korean(text: str) -> bytes:
    # 캐시 사용 (중복 생성 방지)
    cache = st.session_state.setdefault("audio_cache", {})
    if text in cache:
        return cache[text]
    fp = BytesIO()
    gTTS(text=text, lang="ko").write_to_fp(fp)
    fp.seek(0)
    data = fp.read()
    cache[text] = data
    return data

# -----------------------------
# Sidebar (Options)
# -----------------------------
with st.sidebar:
    st.header("옵션")
    mode = st.radio(
        "모드 선택",
        ["보기 모드 (자동 넘김)", "듣고-쓰기 모드 (한국어→가나)"],
        index=0
    )
    use_hira = st.checkbox("히라가나", value=True)
    use_kata = st.checkbox("가타카나", value=True)
    use_daku = st.checkbox("탁음/반탁음 포함", value=True)
    st.caption(f"세션: 무작위 {TOTAL}문항 · 카드당 {LIMIT_SEC}초")

    if "started" not in st.session_state:
        st.session_state.started = False

    # 시작 버튼
    if st.button("새 세션 시작하기", type="primary"):
        pool = build_pool(use_hira, use_kata, use_daku)
        if not pool:
            st.error("히라가나 또는 가타카나를 선택하세요.")
        else:
            items = list(pool.items())  # (kana, romaji)
            random.shuffle(items)
            picked = items[:TOTAL]
            if mode.startswith("보기"):
                # 보기 모드: 표시 글자만
                st.session_state.cards = [{"kana": k} for k, _ in picked]
            else:
                # 듣고-쓰기 모드: kana/romaji/kor_text 준비
                st.session_state.cards = [
                    {
                        "kana": k,
                        "romaji": v,
                        "kor": get_korean_pron(v)  # 한국어 발음 텍스트
                    }
                    for k, v in picked
                ]
            st.session_state.idx = 0
            st.session_state.started = True
            st.session_state.mode = mode
            st.session_state.start_time = time.time()
            # 듣고-쓰기 입력 상태 초기화
            st.session_state.answer = ""
            st.session_state.revealed = False  # 정답 공개 여부(듣고-쓰기만 사용)

st.title("장태순 여사님 전용 테스트")

if not st.session_state.get("started", False):
    st.info("좌측 옵션 선택 후 **새 세션 시작하기**를 눌러주세요.")
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
    st.session_state.answer = ""
    st.session_state.revealed = False

# -----------------------------
# Main area
# -----------------------------
idx = st.session_state.idx
cards = st.session_state.cards
mode = st.session_state.mode

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

# -----------------------------
# MODE A: 보기 모드 (자동 넘김)
# -----------------------------
if mode.startswith("보기"):
    # 7초가 지나면 자동 다음
    if remaining_time() <= 0:
        go_next()
        st.rerun()

    # 크게 표시
    st.markdown(
        f"<div style='text-align:center;font-size:140px;font-weight:800'>{card['kana']}</div>",
        unsafe_allow_html=True
    )

    # 스킵 버튼 (콜백에서 rerun 사용 안 함)
    st.button("다음 ▶", on_click=go_next)

    st.markdown("---")
    st.caption("입력 없이 7초마다 자동으로 다음 글자가 표시됩니다. 필요하면 '다음' 버튼으로 스킵하세요.")

    # 초 단위 갱신
    time.sleep(1)
    st.rerun()

# -----------------------------
# MODE B: 듣고-쓰기 모드 (한국어→가나)
# -----------------------------
else:
    # 현재 카드용 한국어 음성 생성/재생
    kor_text = card["kor"]  # 예: '카', '시', '쓰' 등
    audio_bytes = tts_bytes_korean(kor_text)
    st.audio(audio_bytes, format="audio/mp3", start_time=0)
    st.caption(f"한국어 발음: **{kor_text}**")

    # 입력창 (가나로 입력)
    st.session_state.answer = st.text_input("가나로 적기 (예: か / カ)", value=st.session_state.answer)

    # 제출 버튼: 판정만, rerun은 메인에서
    def check_answer():
        user = (st.session_state.answer or "").strip()
        correct = card["kana"]
        st.session_state.revealed = True
        st.session_state.is_correct = (user == correct)

    cols = st.columns([1,1,1])
    with cols[0]:
        st.button("재생", on_click=lambda: None)  # 플레이어는 위에 이미 있음(수동 컨트롤 가능)
    with cols[1]:
        st.button("제출", on_click=check_answer)
    with cols[2]:
        st.button("스킵 ▶", on_click=go_next)

    # 판정/정답 표시
    if st.session_state.revealed:
        if st.session_state.is_correct:
            st.success(f"정답!  {card['kana']}")
        else:
            st.error(f"오답!  정답: {card['kana']}")
        # 1초 후 자동 다음
        time.sleep(1)
        go_next()
        st.rerun()
    else:
        # 타임아웃 시 자동 다음 (정답 공개 없이)
        if remaining_time() <= 0:
            go_next()
            st.rerun()
        # 초 단위 UI 갱신
        time.sleep(1)
        st.rerun()
