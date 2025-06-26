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
primes = generate_primes(6000)
primes = [p for p in primes if 5000 <= p <= 6000]

# ---- セッション状態初期化 ----
session_keys = ['n','e','d','cipher_str','done_recv','done_send','done_solo','p','q','p1','q1','e_val','e1_val']
for key in session_keys:
    if key not in st.session_state:
        if key.startswith('done_'):
            st.session_state[key] = False
        else:
            st.session_state[key] = ''

st.title("CipherLink")
st.subheader("役割を選択してください")
role = st.radio("", ["受信者","送信者","一人で行う"], horizontal=True)

# ---- RSAのキーフィーチャー説明 ----
st.markdown(
    """
**公開鍵 (Public Key)**: 誰でも知ることができ、メッセージの暗号化に使用します。
- 形式: `(n, e)`
- `n = p × q` で計算されるモジュラス
- `e` は公開指数

**秘密鍵 (Private Key)**: 受信者だけが持つ安全な鍵で、暗号文の復号に使用します。
- 形式: `d`
- `d × e ≡ 1 mod φ(n)` を満たす秘密指数

**送信者**: 個人情報などを送る人。公開鍵 `(n, e)` を用いてメッセージを暗号化。
**受信者**: メッセージを受け取る人。秘密鍵 `d` と公開鍵 `n` を用いて受信した暗号文を復号。
"""
)

# --- 受信者モード ---
if role == "受信者":
    st.header("1. 鍵生成（受信者）")
    st.caption("p, q, e はすべて異なる素数を選んでください。")
    c1, c2, c3 = st.columns(3)
    with c1:
        p = st.selectbox("素数 p", primes)
    with c2:
        q = st.selectbox("素数 q", primes)
    with c3:
        e = st.selectbox("公開鍵 e", primes)
    if st.button("鍵生成（受信者）"):
        st.session_state['done_recv'] = True
        if p == q or p == e or q == e:
            st.error("p, q, e はすべて異なる値である必要があります。")
        else:
            phi = (p - 1) * (q - 1)
            if gcd(e, phi) != 1:
                st.error("e は φ(n) と互いに素である必要があります。")
            else:
                st.session_state['n'] = p * q
                st.session_state['d'] = mod_inverse(e, phi)
                st.session_state['e'] = e
                st.success("鍵生成完了。以下を控えてください。")
    if st.session_state['done_recv']:
        cols = st.columns([2,3])
        cols[0].write("公開鍵 n (n = p × q)")
        cols[0].caption(f"p={p}, q={q}")
        cols[1].code(str(st.session_state['n']))
        cols = st.columns([2,3])
        cols[0].write("公開鍵 e")
        cols[1].code(str(st.session_state['e']))
        cols = st.columns([2,3])
        cols[0].write("秘密鍵 d (受信者のみ)")
        cols[1].code(str(st.session_state['d']))
    st.header("2. 復号（受信者）")
    dec_cols = st.columns(3)
    with dec_cols[0]:
        n_in = st.text_input("公開鍵 n", "", key='recv_n')
    with dec_cols[1]:
        d_in = st.text_input("秘密鍵 d", "", key='recv_d')
    with dec_cols[2]:
        c_in = st.text_area("暗号文 (Base64)", "", key='recv_c')
    if st.button("復号（受信者）"):
        if not n_in or not d_in or not c_in:
            st.error("全て入力してください。")
        else:
            try:
                n_val = int(n_in)
                d_val = int(d_in)
                cb = base64.b64decode(c_in)
                size = (n_val.bit_length() + 7) // 8
                msg = ''.join(chr(pow(int.from_bytes(cb[i:i+size],'big'), d_val, n_val) + 65)
                              for i in range(0, len(cb), size))
                st.success(f"復号結果: {msg}")
            except Exception:
                st.error("復号に失敗しました。")

# --- 送信者モード ---
elif role == "送信者":
    st.header("1. 暗号化（送信者）")
    st.caption("受信者から公開鍵 n, e をコピーして入力してください。")
    cols = st.columns(3)
    with cols[0]:
        n_in = st.text_input("公開鍵 n", "", key='send_n')
    with cols[1]:
        e_in = st.text_input("公開鍵 e", "", key='send_e')
    with cols[2]:
        plain = st.text_input("平文 (A-Z、最大5文字)", "", max_chars=5)
    if st.button("暗号化（送信者）"):
        st.session_state['done_send'] = True
        if not n_in or not e_in or not plain:
            st.error("全て入力してください。")
        else:
            try:
                n_val = int(n_in)
                e_val = int(e_in)
                size = (n_val.bit_length() + 7) // 8
                cb = b''.join(pow(ord(c)-65, e_val, n_val).to_bytes(size,'big') for c in plain)
                b64 = base64.b64encode(cb).decode('ascii')
                st.subheader("暗号文 (Base64)")
                st.code(b64)
                st.session_state['cipher_str'] = b64
            except Exception:
                st.error("暗号化失敗。鍵と平文を確認してください。")

# --- 一人で行うモード ---
elif role == "一人で行う":
    st.header("1. 鍵生成 → 2. 暗号化 → 3. 復号")
    st.caption("p, q, e はすべて異なる素数を選んでください。")
    cols = st.columns(3)
    with cols[0]:
        p1 = st.selectbox("素数 p", primes, key='solo_p')
    with cols[1]:
        q1 = st.selectbox("素数 q", primes, key='solo_q')
    with cols[2]:
        e1 = st.selectbox("公開鍵 e", primes, key='solo_e')
    if st.button("鍵生成（1人）"):
        st.session_state['done_solo'] = True
        if p1 == q1 or p1 == e1 or q1 == e1:
            st.error("p, q, e は異なる値を選んでください。")
        else:
            phi = (p1-1)*(q1-1)
            if gcd(e1, phi) != 1:
                st.error("e は φ(n) と互いに素である必要があります。")
            else:
                st.session_state['n'] = p1*q1
                st.session_state['e'] = e1
                st.session_state['d'] = mod_inverse(e1, phi)
                st.success("鍵生成完了。以下をコピーして次のステップへ進んでください。")
    if st.session_state['done_solo']:
        cs = st.columns([2,3])
        cs[0].write("公開鍵 n (n = p × q)")
        cs[0].caption(f"p={p1}, q={q1}")
        cs[1].code(str(st.session_state['n']))
        cs = st.columns([2,3])
        cs[0].write("公開鍵 e")
        cs[1].code(str(st.session_state['e']))
        cs = st.columns([2,3])
        cs[0].write("秘密鍵 d (受信者のみ)")
        cs[1].code(str(st.session_state['d']))
    st.subheader("2. 暗号化")
    enc_cols = st.columns(3)
    with enc_cols[0]:
        n_enc = st.text_input("公開鍵 n を入力","", key='solo_n')
    with enc_cols[1]:
        e_enc = st.text_input("公開鍵 e を入力","", key='solo_e_input')
    with enc_cols[2]:
        plain1 = st.text_input("平文 (A-Z、最大5文字)","", key='solo_plain')
    if st.button("暗号化（1人）"):
        if not n_enc or not e_enc or not plain1:
            st.error("全て入力してください。")
        else:
            try:
                n_val = int(n_enc)
                e_val = int(e_enc)
                size = (n_val.bit_length() + 7) // 8
                cb = b''.join(pow(ord(c)-65, e_val, n_val).to_bytes(size,'big') for c in plain1)
                b64 = base64.b64encode(cb).decode('ascii')
                st.subheader("暗号文 (Base64)")
                st.code(b64)
                st.session_state['cipher_str'] = b64
            except Exception:
                st.error("暗号化エラー。鍵と平文を確認してください。")
    st.subheader("3. 復号")
    dec_cols = st.columns(3)
    with dec_cols[0]:
        n_dec = st.text_input("公開鍵 n を入力","", key='solo_n_dec')
    with dec_cols[1]:
        d_dec = st.text_input("秘密鍵 d を入力","", key='solo_d_dec')
    with dec_cols[2]:
        cipher1 = st.text_area("暗号文(Base64)","", key='solo_cipher')
    if st.button("復号（1人）"):
        if not n_dec or not d_dec or not cipher1:
            st.error("全て入力してください。")
        else:
            try:
                n_val = int(n_dec)
                d_val = int(d_dec)
                cb = base64.b64decode(cipher1)
                size = (n_val.bit_length() + 7) // 8
                msg = ''.join(chr(pow(int.from_bytes(cb[i:i+size],'big'), d_val, n_val) + 65)
                              for i in range(0, len(cb), size))
                st.success(f"復号結果: {msg}")
            except Exception:
                st.error("復号エラー。鍵と暗号文を確認してください。")
