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

# ---- 役割選択 ----
st.title("RSA Secure Exchange")
role = st.radio("Select Role:", ["Sender", "Receiver"])

# 説明
st.markdown(
    """
Use this tool to simulate RSA encryption and decryption between two students.
- Sender: Generate keys and encrypt messages.
- Receiver: Decrypt messages with the shared public key and own private key.
"""
)

# 共通: キー作成パネル
if role == "Sender":
    st.header("1. Key Generation (Sender)")
    col1, col2, col3 = st.columns(3)
    with col1:
        p = st.selectbox("Prime p", primes, index=0)
    with col2:
        q = st.selectbox("Prime q", primes, index=1)
    with col3:
        e = st.selectbox("Public exponent e", primes, index=4)
    if st.button("Generate Keys"):
        phi = (p - 1) * (q - 1)
        if gcd(e, phi) != 1:
            st.error("e must be coprime with φ(n). Choose another e.")
        else:
            st.session_state['n'] = p * q
            st.session_state['e'] = e
            st.session_state['d'] = mod_inverse(e, phi)
            st.success(f"Public key (n, e): ({st.session_state['n']}, {st.session_state['e']})")
            st.success(f"Private key d: {st.session_state['d']}")

    # 暗号化パネル
    st.header("2. Encryption (Sender)")
    if st.session_state['n'] == 0:
        st.info("Generate keys first.")
    else:
        plain = st.text_input("Plaintext (A-Z, max 5 chars)", max_chars=5)
        if st.button("Encrypt"):
            byte_size = (st.session_state['n'].bit_length() + 7) // 8
            cipher_bytes = b''
            for c in plain:
                m_i = ord(c) - 65
                c_i = pow(m_i, st.session_state['e'], st.session_state['n'])
                cipher_bytes += c_i.to_bytes(byte_size, 'big')
            b64 = base64.b64encode(cipher_bytes).decode('ascii')
            st.session_state['cipher_str'] = b64
            st.code(b64, language='text')
elif role == "Receiver":
    # 復号パネル
    st.header("3. Decryption (Receiver)")
    st.text_input("Public key n", value=st.session_state.get('n', 0), disabled=True)
    st.text_input("Public exponent e", value=st.session_state.get('e', 0), disabled=True)
    d_input = st.number_input("Private key d", value=st.session_state.get('d', 0), step=1)
    cipher_input = st.text_area("Ciphertext (Base64)")
    if st.button("Decrypt"):
        try:
            cipher_bytes = base64.b64decode(cipher_input)
            byte_size = (st.session_state['n'].bit_length() + 7) // 8
            chars = []
            for i in range(0, len(cipher_bytes), byte_size):
                block = cipher_bytes[i:i+byte_size]
                c_i = int.from_bytes(block, 'big')
                m_i = pow(c_i, d_input, st.session_state['n'])
                chars.append(chr(m_i + 65))
            st.write("Decrypted message:", ''.join(chars))
        except Exception:
            st.error("Invalid Base64 or decryption error.")
