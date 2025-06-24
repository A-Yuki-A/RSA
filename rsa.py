import streamlit as st

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
primes_small = [p for p in generate_primes(1000)]

# ---- セッションステート初期化 ----
if 'n' not in st.session_state:
    st.session_state.update({'n': 0, 'e': 0, 'd': 0})

st.title("RSA 暗号シミュレータ（一文字ずつ暗号化）")

# ---- 鍵の説明 ----
st.markdown("""
**公開鍵 (n, e)**…平文を暗号化する鍵（みんなに公開）  
**秘密鍵 d**…暗号文を復号する鍵（自分だけ）
""")

# 1. 鍵作成
st.header("1. 鍵の作成（素数 p, q は 5000～6000）")
col1, col2, col3 = st.columns(3)
with col1:
    p = st.selectbox("素数 p", primes, index=0)
with col2:
    q = st.selectbox("素数 q", primes, index=1)
with col3:
    e = st.selectbox("公開鍵指数 e", primes_small, index=4)

if st.button("鍵生成"):
    phi = (p - 1) * (q - 1)
    if gcd(e, phi) != 1:
        st.error("公開指数 e が φ(n) と互いに素ではありません。別の e を選んでください。")
    else:
        d = mod_inverse(e, phi)
        st.session_state.n = p * q
        st.session_state.e = e
        st.session_state.d = d
        st.success(f"公開鍵 (n, e) = ({st.session_state.n}, {st.session_state.e})")
        st.success(f"秘密鍵 d = {st.session_state.d}")

# 2. 暗号化（一文字ずつ）
st.header("2. 暗号化（動的に表示される鍵を使用）")
# 鍵の表示
st.write("現在の公開鍵 n:", st.session_state.n)
st.write("現在の公開鍵 e:", st.session_state.e)
plain = st.text_input("平文（大文字5文字以内）", max_chars=5, key="plain")

if st.button("暗号化", key="enc"):
    if st.session_state.n == 0:
        st.error("先に鍵生成を行ってください。")
    elif not plain.isupper():
        st.error("大文字アルファベットで入力してください。")
    else:
        cipher_list = []
        for c in plain:
            m_i = ord(c) - 65
            c_i = pow(m_i, st.session_state.e, st.session_state.n)
            cipher_list.append(c_i)
        st.session_state.cipher_list = cipher_list
        st.write("暗号文（数値リスト）:", cipher_list)

# 3. 復号（一文字ずつ）
st.header("3. 復号（動的に表示される鍵を使用）")
# 鍵の表示
st.write("現在の公開鍵 n:", st.session_state.n)
st.write("現在の秘密鍵 d:", st.session_state.d)

if 'cipher_list' in st.session_state:
    cipher_input = ",".join(str(x) for x in st.session_state.cipher_list)
else:
    cipher_input = ''
cipher = st.text_area("暗号文（数値リストをカンマ区切りで編集可）", value=cipher_input)

if st.button("復号", key="dec"):
    if st.session_state.n == 0:
        st.error("先に鍵生成と暗号化を行ってください。")
    else:
        try:
            nums = [int(x.strip()) for x in cipher.split(',')]
            plain_chars = []
            for c_i in nums:
                m_i = pow(c_i, st.session_state.d, st.session_state.n)
                plain_chars.append(chr(m_i + 65))
            st.write("復号結果:", ''.join(plain_chars))
        except:
            st.error("暗号文の形式が正しくありません。数値をカンマ区切りで入力してください。")
