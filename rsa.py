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
role = st.radio("", ["受信者", "送信者", "一人で行う"])

st.markdown(
    """
このツールはRSA暗号の流れを学ぶためのものです。
- **受信者**: 鍵を生成し公開鍵を送信者に渡し、暗号文を復号します。
- **送信者**: 受信者から受け取った公開鍵で暗号化します。
- **一人で行う**: 鍵生成→暗号化→復号を一人で体験できます。
    """
)

# --- 受信者モード ---
if role == "受信者":
    st.header("1. 鍵生成（受信者）")
    col1, col2, col3 = st.columns(3)
    with col1:
        p = st.selectbox("素数 p", primes)
    with col2:
        q = st.selectbox("素数 q", primes)
    with col3:
        e = st.selectbox("公開指数 e", primes)
    if st.button("鍵生成（受信者）"):
        phi = (p - 1) * (q - 1)
        if gcd(e, phi) != 1:
            st.error("e は φ(n) と互いに素である必要があります。")
        else:
            n = p * q
            d = mod_inverse(e, phi)
            st.session_state.update({'n': n, 'e': e, 'd': d})
            st.success("鍵を生成しました。以下を控えてください。")
            st.write(f"公開鍵 n: {n}")
            st.write(f"公開鍵 e: {e}")
            st.write(f"秘密鍵 d: {d}")

    st.header("2. 復号（受信者）")
    n_input = st.text_input("公開鍵 n", value="")
    d_input = st.text_input("秘密鍵 d", value="")
    cipher_input = st.text_area("暗号文 (Base64)")
    if st.button("復号（受信者）"):
        n_val = n_input.strip()
        d_val = d_input.strip()
        if not n_val or not d_val or not cipher_input.strip():
            st.error("公開鍵・秘密鍵・暗号文をすべて入力してください。")
        else:
            try:
                n = int(n_val)
                d = int(d_val)
                # Base64のパディングを自動補完
                b64 = cipher_input.strip()
                pad_len = (-len(b64)) % 4
                b64 += '=' * pad_len
                cipher_bytes = base64.urlsafe_b64decode(b64)
                size = (n.bit_length() + 7) // 8
                msg = ''
                for i in range(0, len(cipher_bytes), size):
                    block = cipher_bytes[i:i+size]
                    m = pow(int.from_bytes(block, 'big'), d, n)
                    msg += chr(m + 65)
                st.success(f"復号結果: {msg}")
            except ValueError:
                st.error("公開鍵・秘密鍵は数字で入力してください。")
            except Exception:
                st.error("復号に失敗しました。公開鍵、秘密鍵、暗号文を確認してください。")
elif role == "送信者":
    st.header("1. 暗号化（送信者）")
    n_input = st.text_input("受信者から受け取った公開鍵 n", value="")
    e_input = st.text_input("受信者から受け取った公開指数 e", value="")
    plain = st.text_input("平文 (A-Z、最大5文字)", max_chars=5)
    if st.button("暗号化（送信者）"):
        try:
            n = int(n_input)
            e = int(e_input)
            size = (n.bit_length() + 7) // 8
            ciphertext = b''
            for c in plain:
                m = ord(c) - 65
                ciphertext += pow(m, e, n).to_bytes(size,'big')
            b64 = base64.urlsafe_b64encode(ciphertext).decode().rstrip('=')
            st.subheader("暗号文 (Base64)")
            st.code(b64)
            st.session_state['cipher_str'] = b64
        except:
            st.error("公開鍵と平文を確認してください。")

# --- 一人で行うモード ---
elif role == "一人で行う":
    st.header("1. 鍵生成 → 2. 暗号化 → 3. 復号")
    # 鍵生成
    p, q, e = st.columns(3)
    with p:
        p_val = st.selectbox("素数 p", primes, key='p1')
    with q:
        q_val = st.selectbox("素数 q", primes, key='q1')
    with e:
        e_val = st.selectbox("公開指数 e", primes, key='e1')
    if st.button("鍵生成（1人）"):
        phi = (p_val-1)*(q_val-1)
        if gcd(e_val,phi)!=1:
            st.error("e は φ(n) と互いに素である必要があります。")
        else:
            st.session_state.update({'n':p_val*q_val,'e':e_val,'d':mod_inverse(e_val,phi)})
            st.success(f"n={st.session_state['n']}, e={st.session_state['e']}, d={st.session_state['d']}")
    # 暗号化
    plain1 = st.text_input("平文 (A-Z、最大5文字)", key='plain1')
    if st.button("暗号化（1人）"):
        try:
            n, e = st.session_state['n'], st.session_state['e']
            size=(n.bit_length()+7)//8
            ct=b''
            for c in plain1:
                ct+=pow(ord(c)-65, e, n).to_bytes(size,'big')
            b64=base64.urlsafe_b64encode(ct).decode().rstrip('=')
            st.session_state['cipher_str']=b64
            st.code(b64)
        except:
            st.error("鍵と平文を確認してください。")
    # 復号
    if 'cipher_str' in st.session_state and st.session_state['cipher_str']:
        if st.button("復号（1人）"):
            try:
                n, d = st.session_state['n'], st.session_state['d']
                cb=base64.urlsafe_b64decode(st.session_state['cipher_str']+'==')
                size=(n.bit_length()+7)//8
                msg=''
                for i in range(0,len(cb),size):
                    m=pow(int.from_bytes(cb[i:i+size],'big'), d, n)
                    msg+=chr(m+65)
                st.write(f"復号結果: {msg}")
            except:
                st.error("復号失敗。データを確認してください。")
