import re
import base64
import binascii
import streamlit as st
import streamlit.components.v1 as components

# --- ページ設定 ---
st.set_page_config(page_title="PrimeGuard RSA")

# --- ヘルパー関数 ---
def generate_primes(n: int):
    sieve = [True] * (n + 1)
    sieve[0:2] = [False, False]
    for i in range(2, int(n**0.5) + 1):
        if sieve[i]:
            for j in range(i * i, n + 1, i):
                sieve[j] = False
    return [i for i, ok in enumerate(sieve) if ok]

def gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a

def mod_inverse(a: int, m: int):
    # 拡張ユークリッド互除法
    def egcd(x, y):
        if y == 0:
            return (1, 0, x)
        u, v, g = egcd(y, x % y)
        return (v, u - (x // y) * v, g)
    x, _, g = egcd(a, m)
    return x % m if g == 1 else None

# --- 素数リスト (5000～6000) ---
primes = [p for p in generate_primes(6000) if 5000 <= p <= 6000]

# --- セッション初期化 ---
for key in ['n', 'e', 'd', 'cipher_str', 'done_recv', 'done_solo']:
    if key not in st.session_state:
        st.session_state[key] = False if key.startswith('done_') else None

# --- アプリタイトル & 説明 ---
st.title("PrimeGuard RSA")
st.markdown(
    """
RSA暗号ではまず2つの大きな素数 p, q を用意し、n = p × q を計算して鍵の基礎とします。

**公開鍵 (n, e)**: メッセージを暗号化する鍵。e は φ(n)=(p−1)(q−1) と互いに素な自然数です。  
**秘密鍵 (n, d)**: メッセージを復号する鍵。d は e × d ≡ 1 (mod φ(n)) を満たす自然数です。

暗号化: C ≡ M^e mod n  
復号: M ≡ C^d mod n

送信者は公開鍵で暗号化し、受信者は秘密鍵で復号します。

> 教材上の注意: ここでは**パディングなしで1文字ずつ暗号化**する単純化モデルです（実運用のRSAではOAEP等のパディングを用い、しばしば鍵交換や署名に用いられ、本文は共通鍵で暗号化します）。
"""
)

st.subheader("役割を選択してください")
role = st.radio("", ["受信者", "送信者", "一人で行う"], horizontal=True)
st.markdown("---")

# ========== 受信者モード ==========
if role == "受信者":
    st.header("1. 鍵生成（受信者）")
    st.caption("p, q は異なる素数を選び、φ(n) と互いに素な公開鍵 e を選択してください。")
    c1, c2, c3 = st.columns(3)
    with c1:
        p = st.selectbox("素数 p", primes, key='recv_p')
    with c2:
        q = st.selectbox("素数 q", primes, key='recv_q')
    with c3:
        phi = (p - 1) * (q - 1)
        # 教材用に 5001–5999 から φ(n) と互いに素な e を抽出
        e_list = [i for i in range(5001, 6000) if gcd(i, phi) == 1 and i not in (p, q)]
        e = st.selectbox("公開鍵 e", e_list, key='recv_e')

    if st.button("鍵生成", key='recv_gen'):
        if p == q:
            st.error("p と q は異なる素数を選んでください。")
        else:
            n = p * q
            d = mod_inverse(e, phi)
            st.session_state.update({'n': n, 'e': e, 'd': d, 'done_recv': True})
            # 復号欄のデフォルト値としても使えるよう事前設定
            st.session_state['dec_n'] = str(n)
            st.session_state['dec_d'] = str(d) if d is not None else ""
            st.success("鍵生成完了。以下の値をコピーしてください。")

    if st.session_state.done_recv:
        # 鍵表示とコピーボタン
        for label, val in [("公開鍵 n", st.session_state.n),
                           ("公開鍵 e", st.session_state.e),
                           ("秘密鍵 d", st.session_state.d)]:
            col, btn = st.columns([3, 1])
            col.write(f"{label}: {val}")
            with btn:
                components.html(
                    f"<button style=\"border:none;background:none;padding:0;color:blue;cursor:pointer;\" onclick=\"navigator.clipboard.writeText('{val}')\">Copy</button>",
                    height=30
                )

        st.markdown("---")
        # 復号ステップ
        st.header("2. 復号（受信者）")
        st.caption("秘密鍵は (n, d) ですが、ここでは復号に必要な d を入力します。")
        d1, d2, d3 = st.columns(3)
        with d1:
            n_in = st.text_input("公開鍵 n", value=st.session_state.get('dec_n', "") or "", key='dec_n')
        with d2:
            d_in = st.text_input("秘密鍵 d", value=st.session_state.get('dec_d', "") or "", key='dec_d')
        with d3:
            c_in = st.text_area("暗号文 (Base64)", key='dec_c')

        if st.button("復号", key='dec_btn'):
            try:
                nv, dv = int(n_in), int(d_in)
                cb = base64.b64decode(c_in)
                size = (nv.bit_length() + 7) // 8
                # ブロックごとに復号して A(65) を足して文字に戻す
                msg = ''.join(
                    chr(pow(int.from_bytes(cb[i:i + size], 'big'), dv, nv) + 65)
                    for i in range(0, len(cb), size)
                )
                st.success(f"復号結果: {msg}")
            except ValueError:
                st.error("n や d が整数ではありません。")
            except binascii.Error:
                st.error("Base64 の形式が正しくありません。")
            except Exception as e:
                st.error(f"復号に失敗しました: {e}")

# ========== 送信者モード ==========
elif role == "送信者":
    st.header("1. 暗号化（送信者）")
    st.caption("受信者の公開鍵を入力してください。平文は A–Z のみ（最大5文字）。")
    s1, s2, s3 = st.columns(3)
    with s1:
        n_in = st.text_input("公開鍵 n", value=str(st.session_state.get('n') or ""), key='enc_n')
    with s2:
        e_in = st.text_input("公開鍵 e", value=str(st.session_state.get('e') or ""), key='enc_e')
    with s3:
        plain = st.text_input("平文 (A–Z 最大5文字)", max_chars=5, key='enc_msg')

    if st.button("暗号化", key='enc_btn'):
        try:
            nv, ev = int(n_in), int(e_in)

            # 入力検証: A–Z のみ
            plain_upper = (plain or "").upper()
            if not re.fullmatch(r"[A-Z]{1,5}", plain_upper):
                st.error("平文は A–Z のみ（1〜5文字）で入力してください。")
            else:
                size = (nv.bit_length() + 7) // 8
                # 1文字ずつ: A→0, B→1, ... Z→25 にマッピングして暗号化
                cb = b''.join(
                    pow(ord(c) - 65, ev, nv).to_bytes(size, 'big')
                    for c in plain_upper
                )
                b64 = base64.b64encode(cb).decode()
                st.subheader("暗号文 (Base64)")
                st.code(b64)
                st.session_state.cipher_str = b64
        except ValueError:
            st.error("n や e が整数ではありません。")
        except Exception as e:
            st.error(f"暗号化に失敗しました: {e}")

# ========== 一人で行うモード ==========
elif role == "一人で行う":
    st.header("1. 鍵生成 → 2. 暗号化 → 3. 復号")

    # --- 授業用の説明（流れの冒頭に配置） ---
    st.markdown("""
### RSAのカギの仕組み（授業用）
| 記号 | 役割 |
|------|------|
| p, q | 秘密の大きな素数 |
| n = p × q | カギの土台になる数 |
| e | 公開鍵の一部（φ(n) と互いに素） |
| d | 秘密鍵の一部（e の逆元） |

- 公開鍵 = (**n**, **e**)  
- 秘密鍵 = (**n**, **d**)  

> 教材上の注意: ここでは**パディングなしで1文字ごと**に暗号化します（体験用の簡略化）。
""")

    c1, c2, c3 = st.columns(3)
    with c1:
        p = st.selectbox("素数 p", primes, key='solo_p')
    with c2:
        q = st.selectbox("素数 q", primes, key='solo_q')
    with c3:
        phi1 = (p - 1) * (q - 1)
        e_list = [i for i in range(5001, 6000) if gcd(i, phi1) == 1 and i not in (p, q)]
        e = st.selectbox("公開鍵 e", e_list, key='solo_e')

    if st.button("鍵生成", key='solo_gen'):
        if p == q:
            st.error("p と q は異なる素数を選んでください。")
        else:
            n1 = p * q
            d1 = mod_inverse(e, phi1)
            st.session_state.update({'n': n1, 'e': e, 'd': d1, 'done_solo': True})
            # 後続欄の自動入力
            st.session_state['solo_enc_n'] = str(n1)
            st.session_state['solo_enc_e'] = str(e)
            st.session_state['solo_dec_n'] = str(n1)
            st.session_state['solo_dec_d'] = str(d1) if d1 is not None else ""
            st.success("鍵生成完了。以下の値をコピーしてください。")

    if st.session_state.done_solo:
        # 鍵表示とコピー
        for label, val in [("公開鍵 n", st.session_state.n),
                           ("公開鍵 e", st.session_state.e),
                           ("秘密鍵 d", st.session_state.d)]:
            col, btn = st.columns([3, 1])
            col.write(f"{label}: {val}")
            with btn:
                components.html(
                    f"<button style=\"border:none;background:none;padding:0;color:blue;cursor:pointer;\" onclick=\"navigator.clipboard.writeText('{val}')\">Copy</button>",
                    height=30
                )

        st.markdown("---")

        # 暗号化
        st.header("2. 暗号化")
        st.caption("平文は A–Z のみ（最大5文字）。")
        oc1, oc2, oc3 = st.columns(3)
        with oc1:
            n_enc = st.text_input("公開鍵 n", value=st.session_state.get('solo_enc_n', "") or "", key='solo_enc_n')
        with oc2:
            e_enc = st.text_input("公開鍵 e", value=st.session_state.get('solo_enc_e', "") or "", key='solo_enc_e')
        with oc3:
            plain1 = st.text_input("平文 (A–Z 最大5文字)", max_chars=5, key='solo_plain1')

        if st.button("暗号化", key='solo_enc_btn'):
            try:
                nv, ev = int(n_enc), int(e_enc)

                plain_upper = (plain1 or "").upper()
                if not re.fullmatch(r"[A-Z]{1,5}", plain_upper):
                    st.error("平文は A–Z のみ（1〜5文字）で入力してください。")
                else:
                    size = (nv.bit_length() + 7) // 8
                    cb = b''.join(
                        pow(ord(c) - 65, ev, nv).to_bytes(size, 'big')
                        for c in plain_upper
                    )
                    b64 = base64.b64encode(cb).decode()
                    st.subheader("暗号文 (Base64)")
                    st.code(b64)
                    st.session_state.cipher_str = b64
                    # 復号欄へも自動転送
                    st.session_state['solo_dec_c'] = b64
            except ValueError:
                st.error("n や e が整数ではありません。")
            except Exception as e:
                st.error(f"暗号化に失敗しました: {e}")

        st.markdown("---")

        # 復号
        st.header("3. 復号")
        st.caption("秘密鍵は (n, d) ですが、ここでは復号に必要な d を入力します。")
        dc1, dc2, dc3 = st.columns(3)
        with dc1:
            n_dec = st.text_input("公開鍵 n", value=st.session_state.get('solo_dec_n', "") or "", key='solo_dec_n')
        with dc2:
            d_dec = st.text_input("秘密鍵 d", value=st.session_state.get('solo_dec_d', "") or "", key='solo_dec_d')
        with dc3:
            ciph = st.text_area("暗号文 (Base64)", value=st.session_state.get('solo_dec_c', "") or "", key='solo_dec_c')

        if st.button("復号", key='solo_dec_btn'):
            try:
                nn, dd = int(n_dec), int(d_dec)
                cb = base64.b64decode(ciph)
                size = (nn.bit_length() + 7) // 8
                msg = ''.join(
                    chr(pow(int.from_bytes(cb[i:i + size], 'big'), dd, nn) + 65)
                    for i in range(0, len(cb), size)
                )
                st.success(f"復号結果: {msg}")
            except ValueError:
                st.error("n や d が整数ではありません。")
            except binascii.Error:
                st.error("Base64 の形式が正しくありません。")
            except Exception as e:
                st.error(f"復号に失敗しました: {e}")
