import streamlit as st

# ---- ヘルパー関数 ----
def text_to_numbers(text):
    # A→00, B→01, …, Z→25 に対応
    return ''.join(f"{ord(c)-65:02d}" for c in text)

def numbers_to_text(num_str):
    # 2桁ずつ分割して逆変換
    return ''.join(chr(int(num_str[i:i+2]) + 65)
                   for i in range(0, len(num_str), 2))

def mod_inverse(e, phi):
    # Python 3.8+ の組み込み pow で逆元を計算
    return pow(e, -1, phi)

# ---- セッションステートの初期化 ----
if 'n' not in st.session_state:
    st.session_state.n = 0
    st.session_state.e = 0
    st.session_state.d = 0

st.title("RSA 暗号シミュレータ（一人二役）")

# 1. 鍵作成パネル
st.header("1. 鍵の作成")
colp, colq, cole = st.columns(3)
with colp:
    p = st.number_input("素数 p", min_value=3, step=2, value=17)
with colq:
    q = st.number_input("素数 q", min_value=3, step=2, value=19)
with cole:
    e = st.number_input("公開鍵指数 e", min_value=3, step=2, value=5)

if st.button("鍵を作成"):
    n = p * q
    phi = (p - 1) * (q - 1)
    if phi % e == 0:
        st.error("e と φ(n) が互いに素ではありません。別の e を選んでください。")
    else:
        d = mod_inverse(e, phi)
        # セッションステートに保存
        st.session_state.n = n
        st.session_state.e = e
        st.session_state.d = d
        st.success(f"公開鍵 (n, e) = ({n}, {e})")
        st.success(f"秘密鍵 d = {d}")

# 2. 暗号化パネル
st.header("2. 暗号化")
n_enc = st.number_input(
    "公開鍵 n", value=st.session_state.n, step=1, key="n_enc"
)
e_enc = st.number_input(
    "公開鍵 e", value=st.session_state.e, step=1, key="e_enc"
)
plain = st.text_input(
    "平文（大文字5文字以内）", max_chars=5, key="plain"
)

if st.button("暗号化", key="enc"):
    if not plain.isupper() or len(plain) == 0:
        st.error("大文字の英字を５文字以内で入力してください。")
    else:
        m = int(text_to_numbers(plain))
        c = pow(m, e_enc, n_enc)
        st.write("平文 → 数値変換：", m)
        st.write("暗号文（数値） ：", c)

# 3. 復号パネル
st.header("3. 復号")
n_dec = st.number_input(
    "公開鍵 n", value=st.session_state.n, step=1, key="n_dec"
)
d_dec = st.number_input(
    "秘密鍵 d", value=st.session_state.d, step=1, key="d_dec"
)
cipher = st.text_input("暗号文（数値）", key="cipher")

if st.button("復号", key="dec"):
    try:
        m2 = pow(int(cipher), d_dec, n_dec)
        # 数値列の桁数を平文の文字数×2に合わせる
        num_str = str(m2).zfill(len(cipher))
        pt = numbers_to_text(num_str)
        st.write("復元した数値：", m2)
        st.write("復号結果（平文）：", pt)
    except:
        st.error("暗号文は数値で入力してください。")
