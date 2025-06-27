import streamlit as st
import base64

# ---- ページ設定 ----
st.set_page_config(page_title="PrimeGuard RSA")

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
state_keys = ['n','e','d','cipher_str','done_recv','done_send','done_solo']
for key in state_keys:
    if key not in st.session_state:
        st.session_state[key] = False if key.startswith('done_') else None

# ---- アプリタイトル／役割選択 ----
st.title("PrimeGuard RSA")
st.subheader("役割を選択してください")
role = st.radio("", ["受信者", "送信者", "一人で行う"], horizontal=True)

# ---- RSA の説明 ----
st.markdown(
    """
RSA暗号では、まず2つの大きな素数 p, q を用意します。
`n = p × q` を計算し、公開鍵と秘密鍵の基礎とします。

**公開鍵 (n, e)**: メッセージを暗号化するための鍵

 e は `(p-1)(q-1)` と互いに素な自然数です

**秘密鍵 (d)**: メッセージを復号するための鍵

 d は `e × d ≡ 1 (mod (p-1)(q-1))` を満たす自然数です（e の逆元）

暗号化: `C ≡ M^e mod n`

復号: `M ≡ C^d mod n`

送信者は受信者の「公開鍵」を使って暗号化し、
受信者は自分の「秘密鍵」で復号します。
"""
)

# --- 受信者モード ---
st.markdown("---")
if role == "受信者":
    st.header("1. 鍵生成（受信者）")
    st.caption("p, q は異なる素数を選択後、利用可能な公開鍵 e を選んでください。")
    c1, c2, c3 = st.columns(3)
    with c1:
        p = st.selectbox("素数 p", primes)
    with c2:
        q = st.selectbox("素数 q", primes)
    with c3:
        phi = (p - 1) * (q - 1)
        e_options = [i for i in range(5001, 6000) if gcd(i, phi) == 1 and i not in (p, q)]
        e = st.selectbox("公開鍵 e", e_options)

    if st.button("鍵生成（受信者）"):
        if p == q or e in (p, q):
            st.error("p, q, e はすべて異なる値を選んでください。")
        else:
            n = p * q
            d = mod_inverse(e, phi)
            st.session_state.n = n
            st.session_state.e = e
            st.session_state.d = d
            st.session_state.done_recv = True
            st.success("鍵生成完了。以下を保存してください。")

    if st.session_state.done_recv:
        cols = st.columns(3)
        cols[0].write("公開鍵 n")
        cols[0].code(str(st.session_state.n))
        cols[1].write("公開鍵 e")
        cols[1].code(str(st.session_state.e))
        cols[2].write("秘密鍵 d")
        cols[2].code(str(st.session_state.d))

        st.header("2. 復号（受信者）")
        dec1, dec2, dec3 = st.columns(3)
        with dec1:
            n_in = st.text_input("公開鍵 n", key='recv_n')
        with dec2:
            d_in = st.text_input("秘密鍵 d", key='recv_d')
        with dec3:
            c_in = st.text_area("暗号文 (Base64)", key='recv_c')
        if st.button("復号（受信者）"):
            if not n_in or not d_in or not c_in:
                st.error("全て入力してください。")
            else:
                try:
                    n_val = int(n_in)
                    d_val = int(d_in)
                    cb = base64.b64decode(c_in)
                    size = (n_val.bit_length() + 7)//8
                    msg = ''.join(chr(pow(int.from_bytes(cb[i:i+size],'big'), d_val, n_val)+65)
                                   for i in range(0, len(cb), size))
                    st.success(f"復号結果: {msg}")
                except:
                    st.error("復号に失敗しました。")

# --- 送信者モード ---
elif role == "送信者":
    st.header("1. 暗号化（送信者）")
    st.caption("受信者から公開鍵 n, e をコピーして入力してください。")
    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        n_in = st.text_input("公開鍵 n", key='send_n')
    with sc2:
        e_in = st.text_input("公開鍵 e", key='send_e')
    with sc3:
        plain = st.text_input("平文 (A-Z、最大5文字)", max_chars=5, key='plain')
    if st.button("暗号化（送信者）"):
        if not n_in or not e_in or not plain:
            st.error("全て入力してください。")
        else:
            try:
                n_val = int(n_in)
                e_val = int(e_in)
                size = (n_val.bit_length() + 7)//8
                cb = b''.join(pow(ord(c)-65, e_val, n_val).to_bytes(size,'big') for c in plain)
                b64 = base64.b64encode(cb).decode()
                st.subheader("暗号文 (Base64)")
                st.code(b64)
                st.session_state.cipher_str = b64
            except:
                st.error("暗号化に失敗しました。")

# --- 一人で行うモード ---
elif role == "一人で行う":
    st.header("1. 鍵生成 → 2. 暗号化 → 3. 復号")
    st.caption("一連のステップをひとりで体験できます。")
    # 鍵生成
    c1, c2, c3 = st.columns(3)
    with c1:
        p1 = st.selectbox("素数 p", primes, key='solo_p')
    with c2:
        q1 = st.selectbox("素数 q", primes, key='solo_q')
    with c3:
        phi1 = (p1-1)*(q1-1)
        e_opts = [i for i in range(5001,6000) if gcd(i, phi1)==1 and i not in (p1,q1)]
        e1 = st.selectbox("公開鍵 e", e_opts, key='solo_e')
    if st.button("鍵生成（1人）"):
        if p1==q1 or e1 in (p1,q1):
            st.error("p, q, e はすべて異なる値を選んでください。")
        else:
            n1 = p1*q1
            d1 = mod_inverse(e1, phi1)
            st.session_state.n = n1
            st.session_state.e = e1
            st.session_state.d = d1
            st.session_state.done_solo = True
            st.success("鍵生成完了。以下を控えてください。")
    if st.session_state.done_solo:
        cols1 = st.columns([2,3])
        cols1[0].write("公開鍵 n")
        cols1[0].code(str(st.session_state.n))
        cols1[1].write("公開鍵 e")
        cols1[1].code(str(st.session_state.e))
        cols1 = st.columns([2,3])
        cols1[0].write("秘密鍵 d")
        cols1[1].code(str(st.session_state.d))

        # 暗号化
        st.subheader("2. 暗号化（1人）")
        ec1, ec2, ec3 = st.columns(3)
        with ec1:
            n_enc = st.text_input("公開鍵 n を入力", key='solo_n')
        with ec2:
            e_enc = st.text_input("公開鍵 e を入力", key='solo_e')
        with ec3:
            plain1 = st.text_input("平文 (A-Z、最大5文字)", max_chars=5, key='solo_plain')
        if st.button("暗号化（1人）"):
            if not n_enc or not e_enc or not plain1:
                st.error("全て入力してください。")
            else:
                try:
                    n_val = int(n_enc)
                    e_val = int(e_enc)
                    size = (n_val.bit_length() + 7)//8
                    cb = b''.join(pow(ord(c)-65, e_val, n_val).to_bytes(size,'big') for c in plain1)
                    b64 = base64.b64encode(cb).decode()
                    st.subheader("暗号文 (Base64)")
                    st.code(b64)
                    st.session_state.cipher_str = b64
                except:
                    st.error("暗号化に失敗しました。")

        # 復号
        st.subheader("3. 復号（1人）")
        dc1, dc2, dc3 = st.columns(3)
        with dc1:
            n_dec = st.text_input("公開鍵 n を入力", key='solo_n_dec')
        with dc2:
            d_dec = st.text_input("秘密鍵 d を入力", key='solo_d_dec')
        with dc3:
            ciph = st.text_area("暗号文(Base64)", key='solo_cipher')
        if st.button("復号（1人）"):
            if not n_dec or not d_dec or not ciph:
                st.error("全て入力してください。")
            else:
                try:
                    n_val = int(n_dec)
                    d_val = int(d_dec)
                    cb = base64.b64decode(ciph)
                    size = (n_val.bit_length() + 7)//8
                    msg = ''.join(chr(pow(int.from_bytes(cb[i:i+size],'big'), d_val, n_val)+65) for i in range(0, len(cb), size))
                    st.success(f"復号結果: {msg}")
                except:
                    st.error("復号に失敗しました。")
