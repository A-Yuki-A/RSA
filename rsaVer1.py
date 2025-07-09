import streamlit as st
import base64
import streamlit.components.v1 as components

# --- ページ設定 ---
st.set_page_config(page_title="PrimeGuard RSA デモ (実際はもっと大きな素数)")

# --- ヘルパー関数 ---
def generate_primes(n):
    """2 以上 n 以下の素数をエラトステネスの篩で返す"""
    sieve = [True] * (n + 1)
    sieve[0:2] = [False, False]
    for i in range(2, int(n**0.5) + 1):
        if sieve[i]:
            for j in range(i*i, n + 1, i):
                sieve[j] = False
    return [i for i, ok in enumerate(sieve) if ok]

def gcd(a, b):
    """a と b の最大公約数を返す"""
    while b:
        a, b = b, a % b
    return a

def mod_inverse(a, m):
    """a × x ≡ 1 (mod m) のときの x を返す。なければ None"""
    def egcd(x, y):
        if y == 0:
            return (1, 0, x)
        u, v, g = egcd(y, x % y)
        return (v, u - (x//y)*v, g)
    x, _, g = egcd(a, m)
    return x % m if g == 1 else None

# --- 素数リスト (5000～6000) ---
primes = [p for p in generate_primes(6000) if 5000 <= p <= 6000]

# --- セッション初期化 ---
for key in ['n','e','d','cipher_str','done_recv','done_solo']:
    if key not in st.session_state:
        st.session_state[key] = False if key.startswith('done_') else None

# --- タイトルと注意書き ---
st.title("PrimeGuard RSA デモ")
st.info("注意: 実際の RSA 暗号では数百桁の素数を使います。このデモでは学習用に小さい素数を使用しています。")

st.markdown("""
**RSA の流れ**
1. [受信者] 素数 p, q を選び、鍵 n, e, d を生成
2. [送信者] 公開鍵 (n, e) でメッセージを暗号化
3. [受信者] 秘密鍵 d で復号
""")

# --- モード選択 ---
role = st.radio("役割を選んでください", ["受信者", "送信者", "一人で実験"], horizontal=True)
st.markdown("---")

# ボタン用HTMLテンプレート関数

def make_copy_button(text, val):
    html = f"""
    <style>
      .copy-btn {{
        padding: 0.25em 0.5em;
        border: 1px solid #ccc;
        border-radius: 4px;
        background-color: #f7f7f7;
        cursor: pointer;
      }}
    </style>
    <button class='copy-btn' onclick="navigator.clipboard.writeText('{val}')">{text}</button>
    """
    return html

# --- 受信者モード ---
if role == "受信者":
    st.header("1. 鍵生成 (受信者)")
    c1, c2, c3 = st.columns(3)
    with c1:
        p = st.selectbox("素数 p", primes, key='recv_p')
    with c2:
        q = st.selectbox("素数 q", primes, key='recv_q')
    with c3:
        phi = (p - 1) * (q - 1)
        common_es = [3, 17, 65537]
        e_candidates = [e for e in common_es if gcd(e, phi) == 1]
        e_list = e_candidates + [i for i in range(5001, 6000) if gcd(i, phi) == 1 and i not in (p, q)]
        e = st.selectbox("公開鍵 e", e_list, key='recv_e')
    if st.button("鍵生成", key='recv_gen'):
        if p == q:
            st.error("p と q は異なる素数を選んでください。")
        else:
            n = p * q
            d = mod_inverse(e, phi)
            st.session_state.update({'n': n, 'e': e, 'd': d, 'done_recv': True})
            st.success("鍵生成完了。次の値をコピーして送信者に渡してください。")
    if st.session_state.done_recv:
        st.subheader("生成された鍵 (コピー)")
        for label, val in [("公開鍵 n", st.session_state.n), ("公開鍵 e", st.session_state.e), ("秘密鍵 d", st.session_state.d)]:
            col, btn = st.columns([3,1])
            col.text_input(label, value=str(val), disabled=True)
            with btn:
                components.html(make_copy_button("Copy", val), height=40)

        # 復号部省略（同様のまま）

# 他のモードも同様に make_copy_button を利用してコピー機能を提供
