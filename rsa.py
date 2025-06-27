import streamlit as st
import base64
import streamlit.components.v1 as components

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
        return (v, u - (x // y) * v, g)
    x, _, g = egcd(a, m)
    return x % m if g == 1 else None

# ---- 素数リスト ----
primes = [p for p in generate_primes(6000) if 5000 <= p <= 6000]

# ---- セッション状態初期化 ----
for key in ['n','e','d','cipher_str','done_recv','done_send','done_solo']:
    if key not in st.session_state:
        st.session_state[key] = False if key.startswith('done_') else None

# ---- UI ----
st.title("PrimeGuard RSA")
st.subheader("役割を選択してください")
role = st.radio("", ["受信者", "送信者", "一人で行う"], horizontal=True)

# ---- モード別処理 ----
if role == "受信者":
    st.header("1. 鍵生成（受信者）")
    c1, c2, c3 = st.columns(3)
    with c1:
        p = st.selectbox("素数 p", primes, key='recv_p')
    with c2:
        q = st.selectbox("素数 q", primes, key='recv_q')
    with c3:
        phi = (p-1)*(q-1)
        e_list = [i for i in range(5001,6000) if gcd(i,phi)==1 and i not in (p,q)]
        e = st.selectbox("公開鍵 e", e_list, key='recv_e')
    if st.button("鍵生成", key='recv_gen'):
        if p == q:
            st.error("p と q は異なる素数を選んでください。")
        else:
            n = p*q
            d = mod_inverse(e, phi)
            st.session_state.update({'n':n,'e':e,'d':d,'done_recv':True})
            st.success("鍵生成完了。値をコピーしてください。")
    if st.session_state.done_recv:
        # 鍵表示とコピーボタン
        for label, val in [("公開鍵 n", st.session_state.n), ("公開鍵 e", st.session_state.e), ("秘密鍵 d", st.session_state.d)]:
            col, btn = st.columns([3,1])
            col.write(f"{label}: {val}")
            with btn:
                components.html(
                    f"<button onclick=\"navigator.clipboard.writeText('{val}')\">Copy</button>",
                    height=30
                )
        # 復号ステップ
        st.header("2. 復号（受信者）")
        d1, d2, d3 = st.columns(3)
        with d1:
            n_in = st.text_input("公開鍵 n", key='dec_n')
        with d2:
            d_in = st.text_input("秘密鍵 d", key='dec_d')
        with d3:
            c_in = st.text_area("暗号文(Base64)", key='dec_c')
        if st.button("復号", key='dec_btn'):
            try:
                n_val, d_val = int(n_in), int(d_in)
                cb = base64.b64decode(c_in)
                size = (n_val.bit_length()+7)//8
                msg = ''.join(
                    chr(pow(int.from_bytes(cb[i:i+size],'big'), d_val, n_val)+65)
                    for i in range(0, len(cb), size)
                )
                st.success(f"復号結果: {msg}")
            except:
                st.error("復号に失敗しました。")

elif role == "送信者":
    st.header("1. 暗号化（送信者）")
    s1, s2, s3 = st.columns(3)
    with s1:
        n_in = st.text_input("公開鍵 n", key='enc_n')
    with s2:
        e_in = st.text_input("公開鍵 e", key='enc_e')
    with s3:
        plain = st.text_input("平文 (A-Z 最大5文字)", max_chars=5, key='enc_msg')
    if st.button("暗号化", key='enc_btn'):
        try:
            n_val, e_val = int(n_in), int(e_in)
            size = (n_val.bit_length()+7)//8
            cb = b''.join(pow(ord(c)-65,e_val,n_val).to_bytes(size,'big') for c in plain)
            b64 = base64.b64encode(cb).decode()
            st.subheader("暗号文 (Base64)")
            st.code(b64)
            st.session_state.cipher_str = b64
        except:
            st.error("暗号化に失敗しました。")

elif role == "一人で行う":
    st.header("1-3. 一人で体験")
    c1, c2, c3 = st.columns(3)
    with c1:
        p1 = st.selectbox("素数 p1", primes, key='solo_p1')
    with c2:
        q1 = st.selectbox("素数 q1", primes, key='solo_q1')
    with c3:
        phi1 = (p1-1)*(q1-1)
        e1_list = [i for i in range(5001,6000) if gcd(i,phi1)==1 and i not in (p1,q1)]
        e1 = st.selectbox("公開鍵 e1", e1_list, key='solo_e1')
    if st.button("鍵生成（一人）", key='solo_gen'):
        if p1==q1:
            st.error("p1 と q1 は異なる素数を選んでください。")
        else:
            n1 = p1*q1
            d1 = mod_inverse(e1,phi1)
            st.session_state.update({'n':n1,'e':e1,'d':d1,'done_solo':True})
            st.success("鍵生成完了。値をコピーしてください。")
    if st.session_state.done_solo:
        # 鍵表示とコピー
        for label,val in [("公開鍵 n1",st.session_state.n),("公開鍵 e1",st.session_state.e),("秘密鍵 d1",st.session_state.d)]:
            col,btn=st.columns([3,1])
            col.write(f"{label}: {val}")
            with btn:
                components.html(
                    f"<button onclick=\"navigator.clipboard.writeText('{val}')\">Copy</button>",
                    height=30
                )
        # 暗号化
        st.header("2. 暗号化（一人）")
        oc1,oc2,oc3=st.columns(3)
        with oc1:
            n_enc=st.text_input("公開鍵 n", key='solo_enc_n')
        with oc2:
            e_enc=st.text_input("公開鍵 e", key='solo_enc_e')
        with oc3:
            plain1=st.text_input("平文 (A-Z 最大5文字)", max_chars=5, key='solo_plain1')
        if st.button("暗号化（一人）", key='solo_enc_btn'):
            if not (n_enc and e_enc and plain1): st.error("全て入力してください。")
            else:
                n_val,e_val=int(n_enc),int(e_enc)
                size=(n_val.bit_length()+7)//8
                cb=b''.join(pow(ord(c)-65,e_val,n_val).to_bytes(size,'big') for c in plain1)
                b64=base64.b64encode(cb).decode()
                st.code(b64)
                st.session_state.cipher_str=b64
        # 復号
        st.header("3. 復号（一人）")
        dc1,dc2,dc3=st.columns(3)
        with dc1:
            n_dec=st.text_input("公開鍵 n", key='solo_dec_n')
        with dc2:
            d_dec=st.text_input("秘密鍵 d", key='solo_dec_d')
        with dc3:
            ciph=st.text_area("暗号文(Base64)", key='solo_dec_c')
        if st.button("復号（一人）", key='solo_dec_btn'):
            try:
                nn,dd=map(int,(n_dec,d_dec))
                cb=base64.b64decode(ciph)
                size=(nn.bit_length()+7)//8
                msg=''.join(chr(pow(int.from_bytes(cb[i:i+size],'big'),dd,nn)+65) for i in range(0,len(cb),size))
                st.success(f"復号結果: {msg}")
            except:
                st.error("復号に失敗しました。")
