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
p, q は素数である必要があります。

**公開鍵 (Public Key)**: メッセージを暗号化するための鍵  
**秘密鍵 (Private Key)**: メッセージを復号するための鍵
"""
)

# --- 受信者モード ---
st.markdown("---")
if role == "受信者":
    st.header("1. 鍵生成（受信者）")
    st.caption("p, q は異なる素数を選び、e は 5000～6000 の任意整数を入力してください。")
    c1, c2, c3 = st.columns(3)
    with c1:
        p = st.selectbox("素数 p", primes)
    with c2:
        q = st.selectbox("素数 q", primes)
    with c3:
        e = st.number_input("公開鍵 e", min_value=5001, max_value=5999, step=1)

    if st.button("鍵生成（受信者）"):
        phi = (p - 1) * (q - 1)
        if p == q or gcd(e, phi) != 1:
            st.error("p, q は異なり、e は φ(n) と互いに素である必要があります。")
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
            cols = st.columns(2)
            cols[0].write(f"公開鍵 n: {n}\ne: {e}")
            cols[1].write(f"秘密鍵 d: {d}")

    if st.session_state.done_recv:
        st.header("2. 復号（受信者）")
        dec = st.columns(3)
        with dec[0]: n_in = st.text_input("公開鍵 n", "", key='recv_n')
        with dec[1]: d_in = st.text_input("秘密鍵 d", "", key='recv_d')
        with dec[2]: c_in = st.text_area("暗号文(Base64)", "", key='recv_c')
        if st.button("復号（受信者）"):
            if use_crypto:
                try:
                    pt = st.session_state.privkey_rsa.decrypt(base64.b64decode(c_in))
                    st.success(f"復号結果: {pt.decode()}")
                except:
                    st.error("復号エラー。鍵と暗号文を確認してください。")
            else:
                try:
                    n_val, d_val = int(n_in), int(d_in)
                    cb = base64.b64decode(c_in)
                    size = (n_val.bit_length() + 7) // 8
                    msg = ''.join(
                        chr(pow(int.from_bytes(cb[i:i+size],'big'), d_val, n_val) + 65)
                        for i in range(0, len(cb), size)
                    )
                    st.success(f"復号結果: {msg}")
                except:
                    st.error("復号エラー。鍵と暗号文を確認してください。")

# --- 送信者モード ---
elif role == "送信者":
    st.header("1. 暗号化（送信者）")
    st.caption("受信者の公開鍵を入力してください。")
    n_in = st.text_input("公開鍵 n", "", key='send_n')
    e_in = st.text_input("公開鍵 e", "", key='send_e')
    plain = st.text_input("平文 (UTF-8)", "")
    if st.button("暗号化（送信者）"):
        if use_crypto and not st.session_state.pubkey_rsa:
            st.error("まず受信者で鍵生成が必要です。")
        else:
            # 暗号化
            if use_crypto:
                ct = st.session_state.pubkey_rsa.encrypt(plain.encode())
            else:
                n_val, e_val = int(n_in), int(e_in)
                size = (n_val.bit_length() + 7) // 8
                ct = b''.join(
                    pow(ord(c)-65, e_val, n_val).to_bytes(size,'big') for c in plain
                )
            b64 = base64.b64encode(ct).decode()
            st.code(b64)
            components.html(
                f"""
<button onclick="navigator.clipboard.writeText(`{b64}`).then(()=>alert('コピーしました'));">Copy</button>
""", height=50)
            st.session_state.cipher_str = b64

# --- 一人で行うモード ---
elif role == "一人で行う":
    st.header("1-3. 一人で体験")
    st.caption("一連のステップをひとりで体験できます。")
    # 統合 UI の実装省略...
