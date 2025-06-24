import streamlit as st

# ---- ヘルパー関数 ----
def generate_primes(n):
    sieve = [True] * (n + 1)
    sieve[0:2] = [False, False]
    for i in range(2, int(n**0.5) + 1):
        if sieve[i]:
            for j in range(i*i, n + 1, i):
                sieve[j] = False
    return [i for i, ok in enumerate(sieve) if ok]

def gcd(a, b):
    while b:
        a, b = b, a % b
    return a

def mod_inverse(a, m):
    def egcd(x, y):
        if y == 0:
            return (1, 0, x)
        u, v, g = egcd(y, x % y)
        return (v, u - (x // y) * v, g)
    x, _, g = egcd(a, m)
    return x % m if g == 1 else None

def text_to_numbers(text):
    return ''.join(f"{ord(c)-65:02d}" for c in text)

def numbers_to_text(num_str):
    return ''.join(
        chr(int(num_str[i:i+2]) + 65)
        for i in range(0, len(num_str), 2)
    )

# ---- prime リスト ----
primes = generate_primes(10000)
primes_small = [p for p in primes if p <= 1000]

# ---- セッションステート初期化 ----
if 'n' not in st.session_state:
    st.session_state.update({
        'n': 0, 'e': 0, 'd': 0,
        'plain_len': 0
    })

st.title("RSA 暗号シミュレータ（一人二役）")

# ---- 鍵の説明 ----
st.markdown("""
**公開鍵 (n, e)**…暗号化に使う（みんなに公開）  
**秘密鍵 d**…復号に使う（自分だけ）
""")

# 1. 鍵作成
st.header("1. 鍵の作成")
colp, colq, cole = st.columns(3)
with colp:
    p = st.selectbox("素数 p", primes, index=primes.index(17))
with colq:
    q = st.selectbox("素数 q", primes, index=primes.index(19))
with cole:
    e = st.selectbox("公開鍵指数 e", primes_small, index=primes_small.index(5))

if st.button("鍵を作成"):
    phi = (p-1)*(q-1)
    if gcd(e, phi) != 1:
        st.error("e と φ(n) が互いに素ではありません。")
    else:
        d = mod_inverse(e, phi)
        st.session_state.n = p*q
        st.session_state.e = e
        st.session_state.d = d
        st.success(f"公開鍵 (n, e)=({st.session_state.n}, {e})")
        st.success(f"秘密鍵 d={d}")

# 2. 暗号化
st.header("2. 暗号化")
n_enc = st.number_input("公開鍵 n", value=st.session_state.n, step=1, key="n_enc")
e_enc = st.number_input("公開鍵 e", value=st.session_state.e, step=1, key="e_enc")
plain = st.text_input("平文（大文字5文字以内）", max_chars=5, key="plain")

if st.button("暗号化", key="enc"):
    if not plain.isupper() or len(plain)==0:
        st.error("大文字5文字以内で入力してください。")
    else:
        st.session_state.plain_len = len(plain)
        m = int(text_to_numbers(plain))
        c = pow(m, e_enc, n_enc)
        st.write("平文→数値：", m)
        st.write("暗号文：", c)

# 3. 復号
st.header("3. 復号")
n_dec = st.number_input("公開鍵 n", value=st.session_state.n, step=1, key="n_dec")
d_dec = st.number_input("秘密鍵 d", value=st.session_state.d, step=1, key="d_dec")
cipher = st.text_input("暗号文（数値）", key="cipher")

if st.button("復号", key="dec"):
    try:
        m2 = pow(int(cipher), d_dec, n_dec)
        # 平文文字数×2 桁でゼロ埋め
        num_str = str(m2).zfill(st.session_state.plain_len * 2)
        pt = numbers_to_text(num_str)
        st.write("復号結果：", pt)
    except:
        st.error("暗号文は数値で入力してください。")
