import streamlit as st
import base64

# ---- Crypto のインポートと依存チェック ----
try:
    from Crypto.PublicKey import RSA
    from Crypto.Cipher import PKCS1_OAEP
except ImportError:
    st.error("エラー: pycryptodome ライブラリが必要です。\nターミナルで `pip install pycryptodome` を実行してください。")
    st.stop()

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
session_keys = [
    'privkey_rsa', 'pubkey_rsa', 'cipher_str',
    'done_recv', 'done_send', 'done_solo'
]
for key in session_keys:
    if key not in st.session_state:
        st.session_state[key] = False if key.startswith('done_') else None

# ---- アプリタイトル／役割選択 ----
st.title("PrimeGuard RSA")
st.subheader("役割を選択してください")
role = st.radio("", ["受信者", "送信者", "一人で行う"], horizontal=True)

# ---- RSAのキーフィーチャー説明 ----
st.markdown(
    """
p, q は素数である必要があります。

**公開鍵 (Public Key)**: メッセージを暗号化するための鍵
**秘密鍵 (Private Key)**: メッセージを復号するための鍵
"""
)

# --- 受信者モード ---
st.markdown("---")
if role == "受信者":
    st.header("1. 鍵生成（受信者）")
    st.caption("p, q は異なる素数を選び、e は 5000 から 6000 の任意整数を入力してください。")
    col1, col2, col3 = st.columns(3)
    with col1:
        p = st.selectbox("素数 p", primes)
    with col2:
        q = st.selectbox("素数 q", primes)
    with col3:
        e = st.number_input("公開鍵 e", min_value=5001, max_value=5999, step=1)

    if st.button("鍵生成（受信者）"):
        phi = (p-1)*(q-1)
        if p == q or gcd(e, phi) != 1:
            st.error("p, q は異なり、e は φ(n) と互いに素である必要があります。")
        else:
            n = p * q
            d = mod_inverse(e, phi)
            key = RSA.construct((n, e, d))
            st.session_state.pubkey_rsa = PKCS1_OAEP.new(RSA.construct((n, e)))
            st.session_state.privkey_rsa = PKCS1_OAEP.new(key)
            st.success("鍵生成完了。以下を保存してください。")
            cols = st.columns(2)
            cols[0].write(f"公開鍵 n: {n}\ne: {e}")
            cols[1].write(f"秘密鍵 d: {d}")

    # 省略: 復号 UI ...

# --- 送信者モード ---
elif role == "送信者":
    st.header("1. 暗号化（送信者）")
    st.caption("受信者の公開鍵を入力してください。")
    n_in = st.text_input("公開鍵 n", "")
    e_in = st.text_input("公開鍵 e", "")
    plain = st.text_input("平文 (UTF-8)", "")
    if st.button("暗号化（送信者）"):
        if not st.session_state.get('pubkey_rsa'):
            st.error("まず受信者で鍵生成が必要です。")
        else:
            ct = st.session_state.pubkey_rsa.encrypt(plain.encode())
            b64 = base64.b64encode(ct).decode()
            st.code(b64)
            st.session_state.cipher_str = b64

# --- 一人で行うモード ---
elif role == "一人で行う":
    st.header("1-3. 一人で体験")
    # 省略: シングルモード UI ...
    pass
