import streamlit as st
import base64

# ---- ページ設定 ----
st.set_page_config(page_title="PrimeGuard RSA")

# ---- ヘルパー関数 ----
def generate_primes(n):
    sieve = [True] * (n + 1)
    sieve[0:2] = [False, False]
    for i in range(2, int(n ** 0.5) + 1):
        if sieve[i]:
            for j in range(i * i, n + 1, i):
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

# ---- 素数リスト（5000～6000） ----
primes = generate_primes(6000)
primes = [p for p in primes if 5000 <= p <= 6000]

# ---- セッション初期化 ----
state_keys = ['n', 'e', 'd', 'cipher_str', 'done_recv', 'done_send', 'done_solo']
for key in state_keys:
    if key not in st.session_state:
        st.session_state[key] = False if key.startswith('done_') else ""

# ---- アプリタイトル／役割選択 ----
st.title("PrimeGuard RSA")
st.subheader("役割を選択してください")
role = st.radio("", ["受信者", "送信者", "一人で行う"], horizontal=True)

# ---- RSA説明 ----
st.markdown(
    """
RSA暗号では2つの大きな素数 p, q を用意し、
`n = p × q` を計算して鍵の基礎とします。

**公開鍵 (n, e)**: メッセージを暗号化する鍵

 e は `(p-1)(q-1)` と互いに素な自然数です

**秘密鍵 (d)**: メッセージを復号する鍵

 d は `e × d ≡ 1 (mod (p-1)(q-1))` を満たす自然数です

暗号化: `C ≡ M^e mod n`

復号  : `M ≡ C^d mod n`

送信者は公開鍵で暗号化し、受信者は秘密鍵で復号します。
"""
)

st.markdown("---")
# --- 受信者モード ---
if role == "受信者":
    st.header("1. 鍵生成（受信者）")
    st.caption("p, q は異なる素数を選び、互いに素な e を選択してください。")
    c1, c2, c3 = st.columns(3)
    with c1:
        p = st.selectbox("素数 p", primes, key='recv_p')
    with c2:
        q = st.selectbox("素数 q", primes, key='recv_q')
    with c3:
        phi = (p - 1) * (q - 1)
        e_opts = [i for i in range(5001, 6000) if gcd(i, phi) == 1 and i not in (p, q)]
        e = st.selectbox("公開鍵 e", e_opts, key='recv_e')
    if st.button("鍵生成（受信者）", key='recv_gen'):
        if p == q:
            st.error("p と q は異なる素数を選んでください。")
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
        d1, d2, d3 = st.columns(3)
        with d1:
            n_in = st.text_input("公開鍵 n", key='dec_n')
        with d2:
            d_in = st.text_input("秘密鍵 d", key='dec_d')
        with d3:
            c_in = st.text_area("暗号文(Base64)", key='dec_c')
        if st.button("復号（受信者）", key='dec_btn'):
            try:
                n_val = int(n_in)
                d_val = int(d_in)
                cb = base64.b64decode(c_in)
                size = (n_val.bit_length() + 7) // 8
                msg = ''.join(
                    chr(pow(int.from_bytes(cb[i:i+size], 'big'), d_val, n_val) + 65)
                    for i in range(0, len(cb), size)
                )
                st.success(f"復号結果: {msg}")
            except:
                st.error("復号に失敗しました。")

# --- 送信者モード ---
elif role == "送信者":
    st.header("1. 暗号化（送信者）")
    st.caption("受信者の公開鍵を入力してください。")
    s1, s2, s3 = st.columns(3)
    with s1:
        n_in = st.text_input("公開鍵 n", key='enc_n')
    with s2:
        e_in = st.text_input("公開鍵 e", key='enc_e')
    with s3:
        plain = st.text_input("平文 (A-Z、最大5文字)", max_chars=5, key='enc_msg')
    if st.button("暗号化（送信者）", key='enc_btn'):
        try:
            n_val = int(n_in)
            e_val = int(e_in)
            size = (n_val.bit_length() + 7) // 8
            cb = b''.join(
                pow(ord(c) - 65, e_val, n_val).to_bytes(size, 'big')
                for c in plain
            )
            b64 = base64.b64encode(cb).decode()
            st.subheader("暗号文 (Base64)")
            st.code(b64)
            st.session_state.cipher_str = b64
        except:
            st.error("暗号化に失敗しました。")

# --- 一人で行うモード ---
elif role == "一人で行う":
    st.header("1-3. 一人で体験")
    st.caption("一連のステップをひとりで体験できます。")
    # 統合 UI...
    # （省略）
