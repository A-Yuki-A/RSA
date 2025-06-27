import streamlit as st
import base64
import streamlit.components.v1 as components

# ---- Crypto のインポートとフォールバック ----
use_crypto = True
try:
                n_val, e_val = map(int, (n_in, e_in))
                size = (n_val.bit_length() + 7) // 8
                cb = b''.join(
                    pow(ord(c)-65, e_val, n_val).to_bytes(size,'big')
                    for c in plain
                )
                b64 = base64.b64encode(cb).decode()
                st.code(b64)
                components.html(f"""
<button onclick="navigator.clipboard.writeText(`{b64}`).then(()=>alert('コピーしました'));">Copy</button>
""", height=50)
                st.session_state.cipher_str = b64(f"""
<button onclick="navigator.clipboard.writeText(`{b64}`).then(()=>alert('コピーしました'));">Copy</button>
""", height=50)
                st.session_state.cipher_str = b64
        else:
            try:
                n_val, e_val = map(int, (n_in, e_in))
                size = (n_val.bit_length() + 7) // 8
                cb = b''.join(
                    pow(ord(c)-65, e_val, n_val).to_bytes(size,'big')
                    for c in plain
                )
                b64 = base64.b64encode(cb).decode()
                st.code(b64)
components.html(f"""
<button onclick="navigator.clipboard.writeText(`{b64}`).then(()=>alert('コピーしました'));">Copy</button>
""", height=50)
                st.session_state.cipher_str = b64
            except Exception:
                st.error("暗号化エラー。")

# --- 一人で行うモード ---
elif role == "一人で行う":
    st.header("1-3. 一人で体験")
    st.caption("p, q, e などを自身で入力して体験できます。")
    # 省略: 統合 UI...
