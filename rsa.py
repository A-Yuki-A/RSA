import streamlit as st
import base64
import streamlit.components.v1 as components

# ---- Crypto のフォールバックチェック ----
use_crypto = True
try:
    from Crypto.PublicKey import RSA
    from Crypto.Cipher import PKCS1_OAEP
except ImportError:
    use_crypto = False

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
    'pubkey_rsa', 'privkey_rsa', 'cipher_str',
    'done_recv', 'done_send', 'done_solo'
]
for key in session_keys:
    if key not in st.session_state:
        st.session_state[key] = False if key.startswith('done_') else None

# ---- UI: タイトルと役割選択 ----
st.title("PrimeGuard RSA")
st.subheader("役割を選択してください")
role = st.radio("", ["受信者", "送信者", "一人で行う"], horizontal=True)

# ---- RSA の説明 ----
st.markdown(
    """
RSA暗号では、まず2つの大きな素数 p, q を用意します。
`n = p × q` を計算し、公開鍵と秘密鍵の基礎とします。

公開鍵 (n, e): メッセージを暗号化するための鍵

 e は `(p-1)(q-1)` と互いに素な自然数です

秘密鍵 (d): メッセージを復号するための鍵

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
        phi = (p - 1) * (q - 1)
        if p == q or e in (p, q):
            st.error("p, q, e はすべて異なる値を選んでください。")
        else:
            n = p * q
            d = mod_inverse(e, phi)
            if use_crypto:
                key = RSA.construct((n, e, d))
                st.session_state.pubkey_rsa = PKCS1_OAEP.new(RSA.construct((n, e)))
                st.session_state.privkey_rsa = PKCS1_OAEP.new(key)
            else:
                st.session_state.pubkey_rsa = (n, e)
                st.session_state.privkey_rsa = (n, d)
            st.session_state.done_recv = True
            st.success("鍵生成完了。以下を保存してください。")
            # 鍵表示とコピーボタン
            cols = st.columns(3)
            # 公開鍵 n
            cols[0].write("公開鍵 n")
            cols[0].code(str(n))

