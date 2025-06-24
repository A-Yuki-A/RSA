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
for key in ('n','e','d','cipher_str'):
    if key not in st.session_state:
        st.session_state[key] = 0 if key!='cipher_str' else ''

# ---- アプリタイトル／役割選択 ----
st.title("CipherLink")
st.subheader("役割を選択してください")
role = st.radio("", ["受信者","送信者","一人で行う"])

st.markdown(
    """
このツールはRSA暗号の流れを学ぶためのものです。
- **受信者**: 鍵生成→公開鍵を送信者に渡す→暗号文を復号します。
- **送信者**: 公開鍵を受け取り→メッセージを暗号化します。
- **一人で行う**: すべてのステップをひとりで体験できます。
"""
)

# --- 受信者モード ---
if role == "受信者":
    st.header("1. 鍵生成（受信者）")
    st.caption("p, q, e はすべて異なる素数を選んでください。")
    col1, col2, col3 = st.columns(3)
    with col1:
        p = st.selectbox("素数 p", primes)
    with col2:
        q = st.selectbox("素数 q", primes)
    with col3:
        e = st.selectbox("公開指数 e", primes)
    if st.button("鍵生成（受信者）"):
        if p == q or p == e or q == e:
            st.error("p, q, e はすべて異なる値である必要があります。")
        else:
            phi = (p - 1) * (q - 1)
            if gcd(e, phi) != 1:
                st.error("e は φ(n) と互いに素である必要があります。")
            else:
                n = p * q
                d = mod_inverse(e, phi)
                st.session_state.update({'n': n, 'e': e, 'd': d})
                st.success("鍵生成完了。以下の値を控えてください。")
                # 鍵の特徴をラベルに追加
                # 公開鍵 n
                col_n_label, col_n_code = st.columns([2,3])
                col_n_label.write("公開鍵 n (n = p × q)")
                # n = p × q を表示
                
                col_n_code.code(str(n))
                # 公開指数 e
                col_e_label, col_e_code = st.columns([2,3])
                col_e_label.write("公開指数 e (公開鍵の指数部)")
                col_e_code.code(str(e))
                # 秘密鍵 d
                col_d_label, col_d_code = st.columns([2,3])
                col_d_label.write("秘密鍵 d (受信者のみが持つ鍵)")
                # 受信者のみが持つ鍵
                
                col_d_code.code(str(d))
    
    st.header("2. 復号（受信者）")
    n_input = st.text_input("公開鍵 n を入力", "")
    d_input = st.text_input("秘密鍵 d を入力", "")
    cipher_input = st.text_area("暗号文 (Base64)")
    if st.button("復号（受信者）"):
        if not n_input or not d_input or not cipher_input:
            st.error("公開鍵・秘密鍵・暗号文をすべて入力してください。")
        else:
            try:
                n = int(n_input)
                d = int(d_input)
            except ValueError:
                st.error("公開鍵と秘密鍵は数字で入力してください。")
                st.stop()
            try:
                b64 = cipher_input.strip()
                pad = (-len(b64)) % 4
                b64 += "=" * pad
                cb = base64.urlsafe_b64decode(b64)
                size = (n.bit_length() + 7) // 8
                msg = ''
                for i in range(0, len(cb), size):
                    block = cb[i:i+size]
                    m = pow(int.from_bytes(block, 'big'), d, n)
                    msg += chr(m + 65)
                st.success(f"復号結果: {msg}")
            except Exception:
                st.error("復号に失敗しました。鍵と暗号文を確認してください。")

# --- 送信者モード ---
elif role == "送信者":
    st.header("1. 暗号化（送信者）")
    n_input = st.text_input("公開鍵 n を入力", "")
    e_input = st.text_input("公開指数 e を入力", "")
    plain = st.text_input("平文 (A-Z、最大5文字)", max_chars=5)
    if st.button("暗号化（送信者）"):
        if not n_input or not e_input or not plain:
            st.error("公開鍵・指数・平文をすべて入力してください。")
        else:
            try:
                n = int(n_input)
                e = int(e_input)
            except ValueError:
                st.error("公開鍵と指数は数字で入力してください。")
                st.stop()
            size = (n.bit_length() + 7) // 8
            ct = b''
            for c in plain:
                m = ord(c) - 65
                ct += pow(m, e, n).to_bytes(size, 'big')
            b64 = base64.urlsafe_b64encode(ct).decode().rstrip('=')
            st.subheader("暗号文 (Base64)")
            st.code(b64)
            st.session_state['cipher_str'] = b64

# --- 一人で行うモード ---
elif role == "一人で行う":
    st.header("1. 鍵生成 → 2. 暗号化 → 3. 復号")
    st.caption("p, q, e はすべて異なる素数を選んでください。")
    p_col, q_col, e_col = st.columns(3)
    with p_col:
        p_val = st.selectbox("素数 p", primes, key='p1')
    with q_col:
        q_val = st.selectbox("素数 q", primes, key='q1')
    with e_col:
        e_val = st.selectbox("公開指数 e", primes, key='e1')
    if st.button("鍵生成（1人）"):
        if p_val == q_val or p_val == e_val or q_val == e_val:
            st.error("p, q, e はすべて異なる値である必要があります。")
        else:
            phi = (p_val - 1) * (q_val - 1)
            if gcd(e_val, phi) != 1:
                st.error("e は φ(n) と互いに素である必要があります。")
            else:
                n = p_val * q_val
                d = mod_inverse(e_val, phi)
                st.session_state.update({'n': n, 'e': e_val, 'd': d})
                st.success("鍵生成完了。以下の値を控えてください。")
                st.markdown("**公開鍵 n (モジュラス)**")
                st.code(str(n))
                st.markdown("**公開指数 e (公開鍵の指数部)**")
                st.code(str(e_val))
                st.markdown("**秘密鍵 d (復号鍵、指数部)**")
                st.code(str(d))

    st.subheader("2. 暗号化")
    n_enc = st.text_input("公開鍵 n を入力", key='n_enc1')
    e_enc = st.text_input("公開指数 e を入力", key='e_enc1')
    plain1 = st.text_input("平文 (A-Z、最大5文字)", key='plain1')
    if st.button("暗号化（1人）"):
        if not n_enc or not e_enc or not plain1:
            st.error("公開鍵・指数・平文を入力してください。")
        else:
            try:
                n = int(n_enc)
                e = int(e_enc)
            except ValueError:
                st.error("公開鍵・指数は数字で入力してください。")
                st.stop()
            size = (n.bit_length() + 7) // 8
            ct = b''
            for c in plain1:
                ct += pow(ord(c) - 65, e, n).to_bytes(size, 'big')
            b64 = base64.urlsafe_b64encode(ct).decode().rstrip('=')
            st.subheader("暗号文 (Base64)")
            st.code(b64)
            st.session_state['cipher_str'] = b64

    st.subheader("3. 復号")
    n_dec = st.text_input("公開鍵 n を入力", key='n_dec1')
    d_dec = st.text_input("秘密鍵 d を入力", key='d_dec1')
    cipher1 = st.text_area("暗号文 (Base64)", value=st.session_state.get('cipher_str',''), key='cipher1')
    if st.button("復号（1人）"):
        if not n_dec or not d_dec or not cipher1:
            st.error("公開鍵・秘密鍵・暗号文を入力してください。")
        else:
            try:
                n = int(n_dec)
                d = int(d_dec)
            except ValueError:
                st.error("鍵は数字で入力してください。")
                st.stop()
            try:
                b64 = cipher1.strip()
                pad = (-len(b64)) % 4
                b64 += '=' * pad
                cb = base64.urlsafe_b64decode(b64)
                size = (n.bit_length() + 7) // 8
                msg = ''
                for i in range(0, len(cb), size):
                    block = cb[i:i+size]
                    m = pow(int.from_bytes(block, 'big'), d, n)
                    msg += chr(m + 65)
                st.success(f"復号結果: {msg}")
            except Exception:
                st.error("復号に失敗しました。鍵と暗号文を確認してください。")
