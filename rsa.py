import streamlit as st
import base64

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
        return (v, u - (x//y)*v, g)
    x, _, g = egcd(a, m)
    return x % m if g == 1 else None

# ---- 素数リスト（5000～6000） ----
all_primes = generate_primes(6000)
primes = [p for p in all_primes if 5000 <= p <= 6000]

# ---- セッションステート初期化 ----
if 'n' not in st.session_state:
    st.session_state['n'] = 0
if 'e' not in st.session_state:
    st.session_state['e'] = 0
if 'd' not in st.session_state:
    st.session_state['d'] = 0
if 'cipher_str' not in st.session_state:
    st.session_state['cipher_str'] = ''

st.title("RSA 暗号シミュレータ（一文字ずつ暗号化）")

# ---- 鍵の説明 ----
st.markdown("""
**公開鍵 (n, e)**…平文を暗号化する鍵（みんなに公開）  
**秘密鍵 d**…暗号文を復号する鍵（自分だけ）
""")

# 1. 鍵作成
st.header("1. 鍵の作成（素数 p, q, e は 5000～6000）")
col1, col2, col3 = st.columns(3)
with col1:
    p = st.selectbox("素数 p", primes, index=0)
with col2:
    q = st.selectbox("素数 q", primes, index=1)
with col3:
    e = st.selectbox("公開鍵指数 e", primes, index=4)
if st.button("鍵生成"):
    phi = (p - 1) * (q - 1)
    if gcd(e, phi) != 1:
        st.error("公開指数 e が φ(n) と互いに素ではありません。別の e を選んでください。")
    else:
        d = mod_inverse(e, phi)
        st.session_state['n'] = p * q
        st.session_state['e'] = e
        st.session_state['d'] = d
        st.success(f"公開鍵 (n, e) = ({st.session_state['n']}, {st.session_state['e']})")
        st.success(f"秘密鍵 d = {st.session_state['d']}")

# 2. 暗号化（一文字ずつ、Base64文字列出力）
st.header("2. 暗号化（動的に表示される鍵を使用）")
st.write("現在の公開鍵 n:", st.session_state['n'])
st.write("現在の公開鍵 e:", st.session_state['e'])
plain = st.text_input("平文（大文字5文字以内）", max_chars=5, key="plain")
if st.button("暗号化", key="enc"):
    if st.session_state['n'] == 0:
        st.error("先に鍵生成を行ってください。")
    elif not plain.isupper() or len(plain) == 0:
        st.error("大文字アルファベットで入力してください。")
    else:
        byte_size = (st.session_state['n'].bit_length() + 7) // 8
        cipher_bytes = b''
        for c in plain:
            m_i = ord(c) - 65
            c_i = pow(m_i, st.session_state['e'], st.session_state['n'])
            cipher_bytes += c_i.to_bytes(byte_size, 'big')
        b64 = base64.b64encode(cipher_bytes).decode('ascii')
        st.session_state['cipher_str'] = b64
        st.write("暗号文 (Base64文字列):")
        st.code(b64)

# 3. 復号（Base64文字列入力）
st.header("3. 復号（動的に表示される鍵を使用）")
st.write("現在の公開鍵 n:", st.session_state['n'])
st.write("現在の秘密鍵 d:", st.session_state['d'])

cipher_input = st.text_area("暗号文 (Base64文字列)", value=st.session_state['cipher_str'])
if st.button("復号", key="dec"):
    if st.session_state['n'] == 0:
        st.error("先に鍵生成と暗号化を行ってください。")
    else:
        try:
            cipher_bytes = base64.b64decode(cipher_input)
            byte_size = (st.session_state['n'].bit_length() + 7) // 8
            chars = []
            for i in range(0, len(cipher_bytes), byte_size):
                block = cipher_bytes[i:i+byte_size]
                c_i = int.from_bytes(block, 'big')
                m_i = pow(c_i, st.session_state['d'], st.session_state['n'])
                chars.append(chr(m_i + 65))
            st.write("復号結果:", ''.join(chars))
        except Exception:
            st.error("暗号文の形式が正しくありません。有効なBase64文字列を入力してください。")
