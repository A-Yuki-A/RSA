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
        e = st.selectbox("公開鍵 e", primes)

    if st.button("鍵生成（受信者）"):
        st.session_state['generated'] = True
        st.session_state['p'] = p
        st.session_state['q'] = q
        st.session_state['e_val'] = e
        phi = (p - 1) * (q - 1)
        if p == q or p == e or q == e:
            st.error("p, q, e はすべて異なる値である必要があります。")
        elif gcd(e, phi) != 1:
            st.error("e は φ(n) と互いに素である必要があります。")
        else:
            st.session_state['n'] = p * q
            st.session_state['e'] = e
            st.session_state['d'] = mod_inverse(e, phi)
            st.success("鍵生成完了。以下の値を控えてください。")

    if st.session_state.get('generated'):
        # 常に表示
        n = st.session_state['n']
        e = st.session_state['e']
        d = st.session_state['d']
        p = st.session_state['p']
        q = st.session_state['q']
        col_n_label, col_n_code = st.columns([2,3])
        col_n_label.write("公開鍵 n (n = p × q)")
        col_n_label.caption(f"p={p}, q={q}")
        col_n_code.code(str(n))
        col_e_label, col_e_code = st.columns([2,3])
        col_e_label.write("公開鍵 e")
        col_e_code.code(str(e))
        col_d_label, col_d_code = st.columns([2,3])
        col_d_label.write("秘密鍵 d (受信者のみが持つ鍵)")
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
                n_val = int(n_input)
                d_val = int(d_input)
            except ValueError:
                st.error("公開鍵と秘密鍵は数字で入力してください。")
                st.stop()
            try:
                b64 = cipher_input.strip()
                pad = (-len(b64)) % 4
                b64 += "=" * pad
                cb = base64.urlsafe_b64decode(b64)
                size = (n_val.bit_length() + 7) // 8
                msg = ''
                for i in range(0, len(cb), size):
                    block = cb[i:i+size]
                    m = pow(int.from_bytes(block, 'big'), d_val, n_val)
                    msg += chr(m + 65)
                st.success(f"復号結果: {msg}")
            except Exception:
                st.error("復号に失敗しました。鍵と暗号文を確認してください。")

# --- 送信者モード ---
elif role == "送信者":
    st.header("1. 暗号化（送信者）")
    n_input = st.text_input("公開鍵 n を入力", "")
    e_input = st.text_input("公開鍵 e を入力", "")
    plain = st.text_input("平文 (A-Z、最大5文字)", max_chars=5)
    if st.button("暗号化（送信者）"):
        if not n_input or not e_input or not plain:
            st.error("公開鍵・指数・平文をすべて入力してください。")
        else:
            try:
                n_val = int(n_input)
                e_val = int(e_input)
            except ValueError:
                st.error("公開鍵と指数は数字で入力してください。")
                st.stop()
            size = (n_val.bit_length() + 7) // 8
            ct = b''
            for c in plain:
                m = ord(c) - 65
                ct += pow(m, e_val, n_val).to_bytes(size, 'big')
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
        e_val = st.selectbox("公開鍵 e", primes, key='e1')
    if st.button("鍵生成（1人）"):
        # フラグと素数保存（widget key と衝突しない名前を使用）
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
                n_val = p_val * q_val
                d_val = mod_inverse(e_val, phi)
                st.session_state['n'] = n_val
                st.session_state['e'] = e_val
                st.session_state['d'] = d_val
                # 正しい st.success の呼び出しのみ
                st.success("鍵生成完了。以下の値を控えてください。")({'n': n_val, 'e': e_val, 'd': d_val})
                st.success("鍵生成完了。以下の値を控えてください。")
    if st.session_state.get('generated_1'):
        # 一人モード鍵情報表示
        col_n_label, col_n_code = st.columns([2,3])
        col_n_label.write("公開鍵 n (n = p × q)")
        col_n_label.caption(f"p={st.session_state['p1_val']}, q={st.session_state['q1_val']}")
        col_n_code.code(str(st.session_state['n']))
        col_e_label, col_e_code = st.columns([2,3])
        col_e_label.write("公開鍵 e")
        col_e_code.code(str(st.session_state['e1_val']))
        col_d_label, col_d_code = st.columns([2,3])
        col_d_label.write("秘密鍵 d (受信者のみが持つ鍵)")
        col_d_code.code(str(st.session_state['d']))
        col_e_label, col_e_code = st.columns([2,3])
        col_e_label.write("公開鍵 e")
        col_e_code.code(str(st.session_state['e']))
        col_d_label, col_d_code = st.columns([2,3])
        col_d_label.write("秘密鍵 d (受信者のみが持つ鍵)")
        col_d_code.code(str(st.session_state['d']))
    
    st.subheader("2. 暗号化")
    n_enc = st.text_input("公開鍵 n を入力", key='n_enc1')
    e_enc = st.text_input("公開鍵 e を入力", key='e_enc1')
    plain1 = st.text_input("平文 (A-Z、最大5文字)", key='plain1')
    if st.button("暗号化（1人）"):
        if not n_enc or not e_enc or not plain1:
            st.error("公開鍵・指数・平文を入力してください。")
        else:
            try:
                n_val = int(n_enc)
                e_val = int(e_enc)
            except ValueError:
                st.error("公開鍵・指数は数字で入力してください。")
                st.stop()
            size = (n_val.bit_length() + 7) // 8
            ct = b''
            for c in plain1:
                ct += pow(ord(c) - 65, e_val, n_val).to_bytes(size, 'big')
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
                n_val = int(n_dec)
                d_val = int(d_dec)
            except ValueError:
                st.error("鍵は数字で入力してください。")
                st.stop()
            try:
                b64 = cipher1.strip()
                pad = (-len(b64)) % 4
                b64 += '=' * pad
                cb = base64.urlsafe_b64decode(b64)
                size = (n_val.bit_length() + 7) // 8
                msg = ''
                for i in range(0, len(cb), size):
                    block = cb[i:i+size]
                    m = pow(int.from_bytes(block, 'big'), d_val, n_val)
                    msg += chr(m + 65)
                st.success(f"復号結果: {msg}")
            except Exception:
                st.error("復号に失敗しました。鍵と暗号文を確認してください。")
