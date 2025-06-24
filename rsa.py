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
role = st.radio("", ["受信者","送信者","一人で行う"])

st.markdown(
    """
このツールはRSA暗号の流れを学ぶためのものです。
- **受信者**: 鍵生成→公開鍵を送信者に渡す→暗号文を復号します。
- **送信者**: 公開鍵を受け取り→メッセージを暗号化します。
- **一人で行う**: すべてのステップをひとりで体験できます。
"""
)

# --- 一人で行うモード ---
elif role == "一人で行う":
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
        st.columns([2,3])[0].write("公開鍵 n (n = p × q)")
        st.columns([2,3])[0].caption(f"p={st.session_state['p1_val']}, q={st.session_state['q1_val']}")
        st.columns([2,3])[1].code(str(n_val))
        st.columns([2,3])[0].write("公開鍵 e")
        st.columns([2,3])[1].code(str(st.session_state['e1_val']))
        st.columns([2,3])[0].write("秘密鍵 d (受信者のみが持つ鍵)")
        st.columns([2,3])[1].code(str(d_val))

    st.subheader("2. 暗号化")
    # 生徒がコピー＆貼り付け用: 初期値空欄
    n_enc = st.text_input("公開鍵 n を入力", "", key='n_enc1')
    e_enc = st.text_input("公開鍵 e を入力", "", key='e_enc1')
    plain1 = st.text_input("平文 (A-Z、最大5文字)", "", key='plain1')
    if st.button("暗号化（1人）"):
        # ... 暗号化ロジック省略 ...
        pass

    st.subheader("3. 復号")
    # 初期値空欄にしてコピペ可能
    n_dec = st.text_input("公開鍵 n を入力", "", key='n_dec1')
    d_dec = st.text_input("秘密鍵 d を入力", "", key='d_dec1')
    cipher1 = st.text_area("暗号文 (Base64)", "", key='cipher1')
    if st.button("復号（1人）"):
        # ... 復号ロジック省略 ...
        pass
