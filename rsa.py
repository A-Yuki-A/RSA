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
for key in ('n', 'e', 'd', 'cipher_str'):
    if key not in st.session_state:
        st.session_state[key] = 0 if key != 'cipher_str' else ''

# ---- タイトル ----
st.title("CipherLink")

# ---- 役割選択 ----
st.subheader("役割を選択してください")
role = st.radio("", ["受信者", "送信者"])

# ---- 説明 ----
st.markdown(
    """
このツールは二人でRSA暗号を学びます。
- **受信者**: まず鍵を生成し、公開鍵を送信者に渡します。
- **送信者**: 受信者から受け取った公開鍵でメッセージを暗号化し、暗号文を送信します。
- **受信者**: 送られた暗号文を秘密鍵で復号します。
    """
)

# 受信者の画面
if role == "受信者":
    st.header("1. 鍵の生成（受信者）")
    col1, col2, col3 = st.columns(3)
    with col1:
        p = st.selectbox("素数 p", primes, index=0)
    with col2:
        q = st.selectbox("素数 q", primes, index=1)
    with col3:
        e = st.selectbox("公開指数 e", primes, index=2)
    if st.button("鍵生成"):
        phi = (p - 1) * (q - 1)
        if gcd(e, phi) != 1:
            st.error("e は φ(n) と互いに素である必要があります。別の値を選択してください。")
        else:
            st.session_state['n'] = p * q
            st.session_state['e'] = e
            st.session_state['d'] = mod_inverse(e, phi)
            st.success(f"公開鍵 (n, e): ({st.session_state['n']}, {st.session_state['e']}) を生成しました。")
            st.code(f"{st.session_state['n']},{st.session_state['e']}", language='text')
    st.header("2. 復号（受信者）")
    cipher_input = st.text_area("送信者から受け取った暗号文 (Base64)")
    if st.button("復号"):
        try:
            n = st.session_state['n']
            d = st.session_state['d']
            cipher_bytes = base64.b64decode(cipher_input)
            byte_size = (n.bit_length() + 7) // 8
            chars = []
            for i in range(0, len(cipher_bytes), byte_size):
                block = cipher_bytes[i:i+byte_size]
                c_i = int.from_bytes(block, 'big')
                m_i = pow(c_i, d, n)
                chars.append(chr(m_i + 65))
            st.write("復号結果：", ''.join(chars))
        except Exception:
            st.error("復号に失敗しました。暗号文を確認してください。")

# 送信者の画面
elif role == "送信者":
    st.header("3. 暗号化（送信者）")
    pub_input = st.text_input("受信者から受け取った公開鍵 (n,e) を貼り付けてください", value="")
    plain = st.text_input("平文（大文字A-Z、最大5文字）", max_chars=5)
    if st.button("暗号化"):
        try:
            n_str, e_str = pub_input.split(',')
            n = int(n_str)
            e = int(e_str)
            if not plain.isupper() or len(plain) == 0:
                st.error("大文字5文字以内で入力してください。")
            else:
                byte_size = (n.bit_length() + 7) // 8
                cipher_bytes = b''
                for c in plain:
                    m_i = ord(c) - 65
                    c_i = pow(m_i, e, n)
                    cipher_bytes += c_i.to_bytes(byte_size, 'big')
                b64 = base64.b64encode(cipher_bytes).decode('ascii')
                st.session_state['cipher_str'] = b64
                st.subheader("暗号文 (Base64)")
                st.code(b64, language='')
        except Exception:
            st.error("公開鍵と平文を確認してください。形式: n,e と文字列。")
