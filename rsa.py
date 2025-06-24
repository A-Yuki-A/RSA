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
for key in ('n','e','d','cipher_str','generated','generated_1','p1_val','q1_val','e1_val'):
    if key not in st.session_state:
        st.session_state[key] = False if key.startswith('generated') else (0 if key in ('n','e','d') else "")

# ---- アプリタイトル／役割選択 ----
st.title("CipherLink")
st.subheader("役割を選択してください")
role = st.radio("", ["受信者","送信者","一人で行う"], horizontal=True) ["受信者","送信者","一人で行う"])

st.markdown(
    """
このツールはRSA暗号の流れを学ぶためのものです。
- **受信者**: 鍵生成→公開鍵を送信者に渡す→暗号文を復号します。
- **送信者**: 公開鍵を受け取り→メッセージを暗号化します。
- **一人で行う**: すべてのステップをひとりで体験できます。
"""
)

# --- 一人で行うモード ---
if role == "一人で行う":
    st.header("1. 鍵生成 → 2. 暗号化 → 3. 復号")
    st.caption("p, q, e はすべて異なる素数を選んでください。")
    p, q, e = st.columns(3)
    with p:
        p_val = st.selectbox("素数 p", primes, key='p1')
    with q:
        q_val = st.selectbox("素数 q", primes, key='q1')
    with e:
        e_val = st.selectbox("公開鍵 e", primes, key='e1')
    if st.button("鍵生成（1人）"):
        st.session_state['generated_1'] = True
        st.session_state['p1_val'] = p_val
        st.session_state['q1_val'] = q_val
        st.session_state['e1_val'] = e_val
        if p_val == q_val or p_val == e_val or q_val == e_val:
            st.error("p, q, e はすべて異なる値である必要があります。")
        else:
            phi = (p_val - 1) * (q_val - 1)
            if gcd(e_val, phi) != 1:
                st.error("e は φ(n) と互いに素である必要があります。")
            else:
                st.session_state['n'] = p_val * q_val
                st.session_state['d'] = mod_inverse(e_val, phi)
                st.session_state['e'] = e_val
                st.success("鍵生成完了。以下の値を控えてください。")
    if st.session_state['generated_1']:
        n_val = st.session_state['n']
        d_val = st.session_state['d']
        # 公開鍵表示
        cols = st.columns([2,3])
        cols[0].write("公開鍵 n (n = p × q)")
        cols[0].caption(f"p={st.session_state['p1_val']}, q={st.session_state['q1_val']}")
        cols[1].code(str(n_val))
        # 公開指数表示
        cols = st.columns([2,3])
        cols[0].write("公開鍵 e")
        cols[1].code(str(st.session_state['e1_val']))
        # 秘密鍵表示
        cols = st.columns([2,3])
        cols[0].write("秘密鍵 d (受信者のみが持つ鍵)")
        cols[1].code(str(d_val))

    st.subheader("2. 暗号化")
    # 生徒がコピー＆貼り付け用: 初期値空欄で横並び
    enc_cols = st.columns(3)
    with enc_cols[0]:
        n_enc = st.text_input("公開鍵 n を入力", "", key='n_enc1')
    with enc_cols[1]:
        e_enc = st.text_input("公開鍵 e を入力", "", key='e_enc1')
    with enc_cols[2]:
        plain1 = st.text_input("平文 (A-Z、最大5文字)", "", key='plain1')
    if st.button("暗号化（1人）"):
        if not n_enc or not e_enc or not plain1:
            st.error("公開鍵・指数・平文を入力してください。")
        else:
            try:
                n_val = int(n_enc)
                e_val = int(e_enc)
            except ValueError:
                st.error("公開鍵と指数は数字で入力してください。")
                st.stop()
            if not plain1.isupper() or len(plain1) == 0:
                st.error("平文は大文字アルファベット5文字以内で入力してください。")
            else:
                byte_size = (n_val.bit_length() + 7) // 8
                cipher_bytes = b''
                for c in plain1:
                    m = ord(c) - 65
                    c_i = pow(m, e_val, n_val)
                    cipher_bytes += c_i.to_bytes(byte_size, 'big')
                b64 = base64.b64encode(cipher_bytes).decode('ascii')
                st.subheader("暗号文 (Base64)")
                st.code(b64)
                st.session_state['cipher_str'] = b64

    st.subheader("3. 復号")
    # 初期値空欄にしてコピペ可能
    n_dec = st.text_input("公開鍵 n を入力", "", key='n_dec1')
    d_dec = st.text_input("秘密鍵 d を入力", "", key='d_dec1')
    cipher1 = st.text_area("暗号文 (Base64)", "", key='cipher1')
    if st.button("復号（1人）"):
        if not n_dec or not d_dec or not cipher1:
            st.error("公開鍵・秘密鍵・暗号文を入力してください。")
        else:
            try:
                n_val = int(n_dec)
                d_val = int(d_dec)
            except ValueError:
                st.error("公開鍵と秘密鍵は数字で入力してください。")
                st.stop()
            try:
                cipher_bytes = base64.b64decode(cipher1)
                byte_size = (n_val.bit_length() + 7) // 8
                chars = []
                for i in range(0, len(cipher_bytes), byte_size):
                    block = cipher_bytes[i:i+byte_size]
                    c_i = int.from_bytes(block, 'big')
                    m = pow(c_i, d_val, n_val)
                    chars.append(chr(m + 65))
                st.success(f"復号結果: {''.join(chars)}")
            except Exception:
                st.error("復号に失敗しました。鍵と暗号文を確認してください。")
