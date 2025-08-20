import streamlit as st
import base64
import streamlit.components.v1 as components

# --- ページ設定 ---
st.set_page_config(page_title="PrimeGuard RSA")

# --- ヘルパー関数 ---
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

# --- 素数リスト (5000～6000) ---
primes = [p for p in generate_primes(6000) if 5000 <= p <= 6000]

# --- セッション初期化 ---
for key in ['n','e','d','cipher_str','done_recv','done_send','done_solo']:
    if key not in st.session_state:
        st.session_state[key] = False if key.startswith('done_') else None

# --- アプリタイトル & 説明 ---
st.title("PrimeGuard RSA")
st.markdown(
    """
RSA暗号ではまず2つの大きな素数 p, q を用意し、
n = p × q を計算して鍵の基礎とします。

**公開鍵 (n, e)**: メッセージを暗号化する鍵  
 e は (p−1)(q−1) と互いに素な自然数です

**秘密鍵 (d)**: メッセージを復号する鍵  
 d は e × d ≡ 1 (mod (p−1)(q−1)) を満たす自然数です

暗号化: C ≡ M^e mod n  
復号: M ≡ C^d mod n

送信者は公開鍵で暗号化し、受信者は秘密鍵で復号します。
"""
)

st.subheader("役割を選択してください")
role = st.radio("", ["受信者", "送信者", "一人で行う"], horizontal=True)
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
        e_list = [i for i in range(5001,6000) if gcd(i,phi)==1 and i not in (p,q)]
        e = st.selectbox("公開鍵 e", e_list, key='recv_e')
    if st.button("鍵生成", key='recv_gen'):
        if p == q:
            st.error("p と q は異なる素数を選んでください。")
        else:
            n = p * q
            d = mod_inverse(e, phi)
            st.session_state.update({'n':n,'e':e,'d':d,'done_recv':True})
            st.success("鍵生成完了。以下の値をコピーしてください。")
    if st.session_state.done_recv:
        # 鍵表示とコピーボタン
        for label, val in [("公開鍵 n", st.session_state.n), ("公開鍵 e", st.session_state.e), ("秘密鍵 d", st.session_state.d)]:
            col, btn = st.columns([3,1])
            col.write(f"{label}: {val}")
            with btn:
                components.html(
                    f"<button style=\"border:none;background:none;padding:0;color:blue;cursor:pointer;\" onclick=\"navigator.clipboard.writeText('{val}')\">Copy</button>", height=30)
        # 復号ステップ
        st.header("2. 復号（受信者）")
        d1, d2, d3 = st.columns(3)
        with d1:
            n_in = st.text_input("公開鍵 n", key='dec_n')
        with d2:
            d_in = st.text_input("秘密鍵 d", key='dec_d')
        with d3:
            c_in = st.text_area("暗号文 (Base64)", key='dec_c')
        if st.button("復号", key='dec_btn'):
            try:
                nv, dv = int(n_in), int(d_in)
                cb = base64.b64decode(c_in)
                size = (nv.bit_length()+7)//8
                msg = ''.join(chr(pow(int.from_bytes(cb[i:i+size],'big'),dv,nv)+65) for i in range(0,len(cb),size))
                st.success(f"復号結果: {msg}")
            except:
                st.error("復号に失敗しました。")

# --- 送信者モード ---
elif role == "送信者":
    st.header("1. 暗号化（送信者）")
    st.caption("受信者の公開鍵を入力してください。")
    s1,s2,s3 = st.columns(3)
    with s1:
        n_in = st.text_input("公開鍵 n", key='enc_n')
    with s2:
        e_in = st.text_input("公開鍵 e", key='enc_e')
    with s3:
        plain = st.text_input("平文 (A-Z 最大5文字)", max_chars=5, key='enc_msg')
    if st.button("暗号化", key='enc_btn'):
        try:
            nv, ev = int(n_in), int(e_in)
            size = (nv.bit_length()+7)//8
            cb = b''.join(pow(ord(c)-65,ev,nv).to_bytes(size,'big') for c in plain)
            b64 = base64.b64encode(cb).decode()
            st.subheader("暗号文 (Base64)")
            st.code(b64)
            st.session_state.cipher_str = b64
        except:
            st.error("暗号化に失敗しました。")

# --- 一人で行うモード ---
elif role == "一人で行う":
    st.header("1. 鍵生成 → 2. 暗号化 → 3. 復号")

    # --- 授業用の説明（ベストな位置：一連の操作の冒頭） ---
    st.markdown("""
### 🔑 RSAのカギの仕組み（授業用説明）
| 記号 | 役割 | わかりやすい説明 |
|------|------|------------------|
| p, q | 秘密の大きな素数 | 「秘密の材料（素数）」<br>（先生の説明では“かけ算して大きな数を作るための材料”） |
| n = p × q | モジュラス（法） | 公開鍵と秘密鍵で共通 / 「大きな数の土台」<br>（“カギの共通の土台になる数”） |
| e | 公開指数（公開鍵の一部） | 「公開用の数字」<br>（“誰でも使っていい公開の数”） |
| d | 秘密指数（秘密鍵の一部） | 🔑「秘密用の数字」<br>（“自分だけが知っている秘密の数”） |

RSAのカギを作るときは、まず **秘密の材料（p, q）** という大きな素数を2つ準備します。  
そのかけ算で **大きな数の土台（n）** を作ります。  

- 公開鍵 = （公開用の数字 **e** と 土台 **n** のペア）  
- 秘密鍵 = （秘密用の数字 **d** と 土台 **n** のペア）  

👉 公開鍵と秘密鍵は「違う数字の組」だけど、**共通して n を使う**のがポイントです。
""")

    st.caption("p, q は異なる素数を選び、互いに素な e を選択してください。")
    c1,c2,c3 = st.columns(3)
    with c1:
        p = st.selectbox("素数 p", primes, key='solo_p')
    with c2:
        q = st.selectbox("素数 q", primes, key='solo_q')
    with c3:
        phi1 = (p-1)*(q-1)
        e_list = [i for i in range(5001,6000) if gcd(i,phi1)==1 and i not in (p,q)]
        e = st.selectbox("素数 e", e_list, key='solo_e')

    if st.button("鍵生成", key='solo_gen'):
        if p == q:
            st.error("p と q は異なる素数を選んでください。")
        else:
            n1, d1 = p*q, mod_inverse(e,phi1)
            st.session_state.update({'n':n1,'e':e,'d':d1,'done_solo':True})
            st.success("鍵生成完了。以下の値をコピーしてください。")

    if st.session_state.done_solo:
        # 鍵表示とコピー（名称を n, e, d に統一）
        for label,val in [("公開鍵 n",st.session_state.n),("公開鍵 e",st.session_state.e),("秘密鍵 d",st.session_state.d)]:
            col,btn = st.columns([3,1])
            col.write(f"{label}: {val}")
            with btn:
                components.html(
                    f"<button style=\"border:none;background:none;padding:0;color:blue;cursor:pointer;\" onclick=\"navigator.clipboard.writeText('{val}')\">Copy</button>", height=30)

        # 暗号化
        st.header("2. 暗号化")
        oc1,oc2,oc3 = st.columns(3)
        with oc1:
            n_enc = st.text_input("公開鍵 n", key='solo_enc_n')
        with oc2:
            e_enc = st.text_input("公開鍵 e", key='solo_enc_e')
        with oc3:
            plain1 = st.text_input("平文 (A-Z 最大5文字)", max_chars=5, key='solo_plain1')
        if st.button("暗号化", key='solo_enc_btn'):
            try:
                nv, ev = int(n_enc), int(e_enc)
                size = (nv.bit_length()+7)//8
                cb = b''.join(pow(ord(c)-65,ev,nv).to_bytes(size,'big') for c in plain1)
                b64 = base64.b64encode(cb).decode()
                st.code(b64)
                st.session_state.cipher_str = b64
            except:
                st.error("暗号化に失敗しました。")

        # 復号
        st.header("3. 復号")
        dc1,dc2,dc3 = st.columns(3)
        with dc1:
            n_dec = st.text_input("公開鍵 n", key='solo_dec_n')
        with dc2:
            d_dec = st.text_input("秘密鍵 d", key='solo_dec_d')
        with dc3:
            ciph = st.text_area("暗号文 (Base64)", key='solo_dec_c')
        if st.button("復号", key='solo_dec_btn'):
            try:
                nn, dd = map(int,(n_dec,d_dec))
                cb = base64.b64decode(ciph)
                size = (nn.bit_length()+7)//8
                msg = ''.join(chr(pow(int.from_bytes(cb[i:i+size],'big'),dd,nn)+65) for i in range(0,len(cb),size))
                st.success(f"復号結果: {msg}")
            except:
                st.error("復号に失敗しました。")
