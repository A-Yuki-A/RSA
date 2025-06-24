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

# ---- セッション状態初期化 ----
for key in ('n','e','d','cipher_str','done_recv','done_send','done_solo'):
    if key not in st.session_state:
        st.session_state[key] = False

st.title("CipherLink")
st.subheader("役割を選択してください")
role = st.radio("", ["受信者","送信者","一人で行う"], horizontal=True)

# 共通説明
st.markdown(
    """
このツールはRSA暗号の流れを学ぶためのものです。
- **受信者**: 鍵生成し公開鍵を渡し、暗号文を復号。
- **送信者**: 受信者から公開鍵を受け取り暗号化。
- **一人で行う**: すべてのステップを一人で実行。
"""
)
# RSA 暗号の流れ説明
st.markdown(
    """
**RSA 暗号のしくみ**

1. **素数の選定**: 二つの大きな素数 `p`, `q` を選びます。
2. **モジュラス計算**: `n = p × q`
3. **公開指数の選択**: 公開鍵 `(n, e)` として、`e` を `1 < e < φ(n)` の範囲（`φ(n)=(p-1)(q-1)`）で選びます。
4. **秘密指数の計算**: 秘密鍵 `d` を `e × d ≡ 1 mod φ(n)` を満たすように求めます。

- **暗号化**: 公開鍵 `(n, e)` を用いて、メッセージ `m` (`0 ≤ m < n`) から暗号文 `c = m^e mod n` を計算します。
- **復号**: 秘密鍵 `d` と公開鍵 `n` を用い（公開指数 `e` は暗号化時のみ使用）、`m = c^d mod n` で元のメッセージ `m` を復元します。

この仕組みにより、`p`, `q` を知らない第三者は `d` を計算できず、安全性が保たれます。
"""
)
` の範囲で選びます（`φ(n)=(p-1)(q-1)`）。
4. **秘密指数**: 秘密鍵 `d` を `e × d ≡ 1 mod φ(n)` を満たすように計算します。

- **暗号化**: メッセージ `m` を `0 ≤ m < n` の数値に変換し、
  `c = m^e mod n` を計算して暗号文 `c` を得ます。
- **復号**: 暗号文 `c` に対して `m = c^d mod n` を計算し、元のメッセージ `m` を復元します。

この仕組みにより、`p`, `q` を知らない第三者は `d` を計算できず、安全性が保たれます。
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
        st.session_state['done_recv'] = True
        if p == q or p == e or q == e:
            st.error("p, q, e はすべて異なる値である必要があります。")
        else:
            phi = (p-1)*(q-1)
            if gcd(e,phi) != 1:
                st.error("e は φ(n) と互いに素である必要があります。")
            else:
                st.session_state['n'] = p*q
                st.session_state['d'] = mod_inverse(e,phi)
                st.session_state['e'] = e
                st.success("鍵生成完了。以下を控えてください。")
    if st.session_state['done_recv']:
        cols = st.columns([2,3])
        cols[0].write("公開鍵 n (n = p × q)")
        cols[0].caption(f"p={p}, q={q}")
        cols[1].code(str(st.session_state['n']))
        cols = st.columns([2,3])
        cols[0].write("公開鍵 e")
        cols[1].code(str(st.session_state['e']))
        cols = st.columns([2,3])
        cols[0].write("秘密鍵 d (受信者のみ)" )
        cols[1].code(str(st.session_state['d']))
    st.header("2. 復号（受信者）")
    # 復号用入力フォームを横並びに
    dec_cols = st.columns(3)
    with dec_cols[0]:
        n_in = st.text_input("公開鍵 n", "", key='n_in_recv')
    with dec_cols[1]:
        d_in = st.text_input("秘密鍵 d", "", key='d_in_recv')
    with dec_cols[2]:
        c_in = st.text_area("暗号文 (Base64)", "", key='c_in_recv')
    if st.button("復号（受信者）"):
        if not n_in or not d_in or not c_in:
            st.error("全て入力してください。")
        else:
            try:
                n=int(n_in); d=int(d_in)
                cb=base64.b64decode(c_in)
                size=(n.bit_length()+7)//8
                msg=''.join(chr(pow(int.from_bytes(cb[i:i+size],'big'),d,n)+65)
                            for i in range(0,len(cb),size))
                st.success(f"復号結果: {msg}")
            except:
                st.error("復号に失敗しました。")

# --- 送信者モード ---
elif role == "送信者":
    st.header("1. 暗号化（送信者）")
    st.caption("受信者から公開鍵 n,e をコピーして入力してください。")
    cols=st.columns(3)
    with cols[0]: n_in=st.text_input("公開鍵 n","")
    with cols[1]: e_in=st.text_input("公開鍵 e","")
    with cols[2]: plain=st.text_input("平文 (A-Z最大5)","",max_chars=5)
    if st.button("暗号化（送信者）"):
        st.session_state['done_send']=True
        if not n_in or not e_in or not plain:
            st.error("全て入力してください。")
        else:
            try:
                n=int(n_in); e=int(e_in)
                size=(n.bit_length()+7)//8
                cb=b''.join(pow(ord(c)-65,e,n).to_bytes(size,'big') for c in plain)
                b64=base64.b64encode(cb).decode('ascii')
                st.subheader("暗号文 (Base64)")
                st.code(b64)
                st.session_state['cipher_str']=b64
            except:
                st.error("暗号化失敗。鍵と平文を確認してください。")

# --- 一人で行うモード ---
elif role == "一人で行う":
    st.header("1. 鍵生成 → 2. 暗号化 → 3. 復号")
    st.caption("p, q, e はすべて異なる素数を選んでください。")
    cols=st.columns(3)
    with cols[0]: p_val=st.selectbox("素数 p",primes,key='p1')
    with cols[1]: q_val=st.selectbox("素数 q",primes,key='q1')
    with cols[2]: e_val=st.selectbox("公開鍵 e",primes,key='e1')
    if st.button("鍵生成（1人）"):
        st.session_state['done_solo']=True
        if p_val==q_val or p_val==e_val or q_val==e_val:
            st.error("p,q,e は異なる必要があります。")
        else:
            phi=(p_val-1)*(q_val-1)
            if gcd(e_val,phi)!=1:
                st.error("e は φ(n) と互いに素である必要があります。")
            else:
                st.session_state['n']=p_val*q_val
                st.session_state['e']=e_val
                st.session_state['d']=mod_inverse(e_val,phi)
                st.success("鍵生成完了")
    if st.session_state['done_solo']:
        # 表示同様
        cs=st.columns([2,3])
        cs[0].write("公開鍵 n (n = p × q)")
        cs[0].caption(f"p={p_val},q={q_val}")
        cs[1].code(str(st.session_state['n']))
        cs=st.columns([2,3])
        cs[0].write("公開鍵 e")
        cs[1].code(str(e_val))
        cs=st.columns([2,3])
        cs[0].write("秘密鍵 d (受信者のみ)")
        cs[1].code(str(st.session_state['d']))
    st.subheader("2. 暗号化")
    enc_cols=st.columns(3)
    with enc_cols[0]: n_enc=st.text_input("公開鍵 n を入力","",key='n_enc1')
    with enc_cols[1]: e_enc=st.text_input("公開鍵 e を入力","",key='e_enc1')
    with enc_cols[2]: plain1=st.text_input("平文 (A-Z最大5)","",key='plain1')
    if st.button("暗号化（1人）"):
        if not n_enc or not e_enc or not plain1:
            st.error("全て入力してください。")
        else:
            try:
                n=int(n_enc);e=int(e_enc)
                size=(n.bit_length()+7)//8
                cb=b''.join(pow(ord(c)-65,e,n).to_bytes(size,'big') for c in plain1)
                b64=base64.b64encode(cb).decode('ascii')
                st.code(b64)
                st.session_state['cipher_str']=b64
            except:
                st.error("暗号化エラー")
    st.subheader("3. 復号")
    dec_cols=st.columns(3)
    with dec_cols[0]: n_dec=st.text_input("公開鍵 n を入力","",key='n_dec1')
    with dec_cols[1]: d_dec=st.text_input("秘密鍵 d を入力","",key='d_dec1')
    with dec_cols[2]: cipher1=st.text_area("暗号文(Base64)","",key='cipher1')
    if st.button("復号（1人）"):
        if not n_dec or not d_dec or not cipher1:
            st.error("全て入力してください。")
        else:
            try:
                n=int(n_dec);d=int(d_dec)
                cb=base64.b64decode(cipher1)
                size=(n.bit_length()+7)//8
                msg=''.join(chr(pow(int.from_bytes(cb[i:i+size],'big'),d,n)+65) for i in range(0,len(cb),size))
                st.success(f"復号結果: {msg}")
            except:
                st.error("復号エラー")
