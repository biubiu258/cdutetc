# -*- encoding: utf-8 -*-
# 外部变量/注释开始
# 外部变量/注释结束
"""
@File    :   encrypt.py    
@Author  :   Guesser
@Modify Time      @Version    @Description
------------      --------    -----------
2025/11/1 23:45    1.0         密码加密,RSA
"""
from Crypto.PublicKey import RSA


PUBLIC_KEY_PEM = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC17rFm4GmSDoC+vR/qSCnT0fMh
byqr55tsR6PBjc7l/SLC56xRnKtZGY7OA23PKJ6oIB4qC53tMH+PtwQTbq62cChv
WtROaRAFup6lrwStpTZ81yS1om/bUSDMlbZDFgS9IZxrfYOm+PJLQ5GOqYinb5PD
M6paIJkUk9TrERfnsQIDAQAB
-----END PUBLIC KEY-----"""


# === 还原 n, e ===
key = RSA.import_key(PUBLIC_KEY_PEM)
n = key.n
e = key.e

# === JSBN 的原始加密逻辑 ===
chunk_size = 126
HEX = "0123456789abcdef"


def js_pack_block(s_bytes):
    digits = []
    i = 0
    while i < len(s_bytes):
        lo = s_bytes[i]
        hi = s_bytes[i + 1] if i + 1 < len(s_bytes) else 0
        digits.append(lo + (hi << 8))
        i += 2
    x = 0
    base = 1 << 16
    for i, w in enumerate(digits):
        x += w * (base ** i)
    return x


def js_c(d):
    t = ""
    for _ in range(4):
        t = HEX[d & 0xF] + t
        d >>= 4
    return t


def js_u(x):
    if x == 0:
        return "0000"
    base = 1 << 16
    digits = []
    while x:
        digits.append(x & (base - 1))
        x >>= 16
    i = len(digits) - 1
    while i > 0 and digits[i] == 0:
        i -= 1
    return "".join(js_c(digits[j]) for j in range(i, -1, -1))


def js_encrypt_string(s):
    b = bytearray(s.encode("utf-8"))
    while len(b) % chunk_size != 0:
        b.append(0)
    out = []
    for off in range(0, len(b), chunk_size):
        block = bytes(b[off:off + chunk_size])
        x = js_pack_block(block)
        y = pow(x, e, n)
        out.append(js_u(y))
    return " ".join(out)
