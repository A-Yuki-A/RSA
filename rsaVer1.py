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

# --- RSA の流れ ---
st.markdown("""
**RSA の流れ**
1. [受信者] 素数 p, q を選び、鍵 n, e, d を生成
2. [送信者] 公開鍵 (n, e) でメッセージを暗号化
3. [受信者] 秘密鍵 d で復号
""")
# フロー図表示
st.markdown("""
```plaintext
受信者 ── 鍵生成 (p, q → n, e, d) ──> 公開鍵 (n, e)
公開鍵 (n, e) ── 暗号化 (送信者) ──> 暗号文 (C)
暗号文 (C) ── 復号 (受信者) ──> 平文 (M)
秘密鍵 (d) は受信者のみ保持
```
""")

# --- モード選択 ---
role = st.radio("役割を選んでください", ["受信者", "送信者", "一人で実験"], horizontal=True)
st.markdown("---")

# --- コピー用ボタン HTML ---
def make_copy_button(label, val):
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
    <button class='copy-btn' onclick="navigator.clipboard.writeText('{val}')">{label}</button>
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
        e_list = [e for e in common_es if gcd(e, phi) == 1] + \
                 [i for i in range(5001, 6000) if gcd(i, phi) == 1 and i not in (p, q)]
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
        st.subheader("生成された鍵 (Copy ボタンでコピー)")
        for label, val in [("公開鍵 n", st.session_state.n), ("公開鍵 e", st.session_state.e), ("秘密鍵 d", st.session_state.d)]:
            col, btn = st.columns([3,1])
            col.text_input(label, value=str(val), disabled=True)
            with btn:
                components.html(make_copy_button("Copy", val), height=40)

        # 復号パート
        st.header("2. 復号 (受信者)")
        nv = st.text_input("公開鍵 n", key='dec_n')
        dv = st.text_input("秘密鍵 d", key='dec_d')
        c_in = st.text_area("暗号文 (Base64)", key='dec_c')
        if st.button("復号", key='dec_btn'):
            try:
                nv_i = int(nv); dv_i = int(dv)
                cb = base64.b64decode(c_in)
                size = (nv_i.bit_length() + 7) // 8
                decoded = []
                for i in range(0, len(cb), size):
                    chunk = cb[i:i+size]
                    num   = int.from_bytes(chunk, 'big')
                    m     = pow(num, dv_i, nv_i)
                    decoded.append(chr(m + 65))
                msg = ''.join(decoded)
                st.success(f"復号結果: {msg}")
            except ValueError:
                st.error("数値変換エラー。鍵の値を確認してください。")
            except base64.binascii.Error:
                st.error("Base64 デコードエラー。暗号文を確認してください。")

# --- 送信者モード ---
elif role == "送信者":
    st.header("1. 暗号化 (送信者)")
    nv = st.text_input("受信者の公開鍵 n", key='enc_n')
    ev = st.text_input("受信者の公開鍵 e", key='enc_e')
    plain = st.text_input("平文 (A-Z 最大5文字)（暗号化したい文章）", max_chars=5, key='enc_msg')
    if st.button("暗号化", key='enc_btn'):
        try:
            nv_i = int(nv); ev_i = int(ev)
            size = (nv_i.bit_length() + 7) // 8
            cb = b''.join(pow(ord(c)-65, ev_i, nv_i).to_bytes(size, 'big') for c in plain)
            b64 = base64.b64encode(cb).decode()
            st.subheader("暗号文 (Base64)")
            st.code(b64)
            st.session_state.cipher_str = b64
        except ValueError:
            st.error("数値変換エラー。鍵の値を確認してください。")

# --- 一人で実験モード ---
elif role == "一人で実験":
    st.header("1. 鍵生成 → 2. 暗号化 → 3. 復号 (一人)")
    p1 = st.selectbox("素数 p1", primes, key='solo_p1')
    q1 = st.selectbox("素数 q1", primes, key='solo_q1')
    phi1 = (p1 - 1) * (q1 - 1)
    e1_list = [e for e in [3,17,65537] if gcd(e,phi1)==1] + \
              [i for i in range(5001,6000) if gcd(i,phi1)==1 and i not in (p1,q1)]
    e1 = st.selectbox("公開鍵 e1", e1_list, key='solo_e1')
    if st.button("鍵生成（一人）", key='solo_gen'):
        if p1==q1:
            st.error("p1 と q1 は異なる素数を選んでください。")
        else:
            n1 = p1*q1; d1 = mod_inverse(e1,phi1)
            st.session_state.update({'n':n1,'e':e1,'d':d1,'done_solo':True})
            st.success("鍵生成完了。次の値をコピーしてください。")
    if st.session_state.done_solo:
        st.subheader("生成された鍵 (Copy) ")
        for label, val in [("公開鍵 n1", st.session_state.n), ("公開鍵 e1", st.session_state.e), ("秘密鍵 d1", st.session_state.d)]:
            col, btn = st.columns([3,1])
            col.text_input(label, value=str(val), disabled=True)
            with btn:
                components.html(make_copy_button("Copy", val), height=40)

        st.header("2. 暗号化 (一人)")
        n_enc = st.text_input("公開鍵 n", key='solo_enc_n')
        e_enc = st.text_input("公開鍵 e", key='solo_enc_e')
        plain1 = st.text_input("平文 (A-Z 最大5文字)", max_chars=5, key='solo_plain1')
        if st.button("暗号化 (一人)", key='solo_enc_btn'):
            try:
                nv2 = int(n_enc); ev2 = int(e_enc)
                size2 = (nv2.bit_length()+7)//8
                cb2 = b''.join(pow(ord(c)-65, ev2, nv2).to_bytes(size2,'big') for c in plain1)
                b64_2 = base64.b64encode(cb2).decode()
                st.code(b64_2)
                st.session_state.cipher_str = b64_2
            except ValueError:
                st.error("数値変換エラー。鍵の値を確認してください。")

        st.header("3. 復号 (一人)")
        n_dec = st.text_input("公開鍵 n", key='solo_dec_n')
        d_dec = st.text_input("秘密鍵 d", key='solo_dec_d')
        ciph = st.text_area("暗号文 (Base64)", key='solo_dec_c')
        if st.button("復号 (一人)", key='solo_dec_btn'):
            try:
                nn = int(n_dec); dd = int(d_dec)
                cb3 = base64.b64decode(ciph)
                size3 = (nn.bit_length()+7)//8
                decoded3 = []
                for i in range(0,len(cb3),size3):
                    chunk = cb3[i:i+size3]
                    num3 = int.from_bytes(chunk,'big')
                    m3 = pow(num3,dd,nn)
                    decoded3.append(chr(m3+65))
                msg3 = ''.join(decoded3)
                st.success(f"復号結果: {msg3}")
            except ValueError:
                st.error("数値変換エラー。鍵の値を確認してください。")
            except base64.binascii.Error:
                st.error("Base64 デコードエラー。暗号文を確認してください。")
