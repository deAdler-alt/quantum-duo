import os, json, base64, numpy as np

try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import hashes
    AES_AVAILABLE = True
except Exception:
    AES_AVAILABLE = False

def has_aes():
    return AES_AVAILABLE

def bits_to_key_bytes(bits):
    L = len(bits) - (len(bits) % 8)
    bits = bits[:L]
    byts = []
    for i in range(0, L, 8):
        byte = 0
        for b in bits[i:i+8]:
            byte = (byte << 1) | int(b)
        byts.append(byte)
    return bytes(byts) if byts else b"\x00"

def derive_key_sha256(key_material: bytes) -> bytes:
    if not AES_AVAILABLE:
        return key_material
    h = hashes.Hash(hashes.SHA256())
    h.update(key_material)
    return h.finalize()

def xor_bytes(data: bytes, key: bytes) -> bytes:
    if not key:
        return data
    k = np.frombuffer(key, dtype=np.uint8)
    d = np.frombuffer(data, dtype=np.uint8)
    out = np.empty_like(d)
    n = len(d)
    m = len(k)
    for i in range(n):
        out[i] = d[i] ^ k[i % m]
    return out.tobytes()

def json_encrypt_xor(obj, key_bytes: bytes) -> bytes:
    data = json.dumps(obj, separators=(',',':')).encode("utf-8")
    return xor_bytes(data, key_bytes)

def json_decrypt_xor(enc: bytes, key_bytes: bytes):
    data = xor_bytes(enc, key_bytes).decode("utf-8")
    return json.loads(data)

def aes_ctr_encrypt(plaintext: bytes, key32: bytes) -> bytes:
    if not AES_AVAILABLE:
        raise RuntimeError("AES not available")
    nonce = os.urandom(16)
    cipher = Cipher(algorithms.AES(key32), modes.CTR(nonce))
    enc = cipher.encryptor().update(plaintext) + cipher.encryptor().finalize()
    return nonce + enc

def aes_ctr_decrypt(blob: bytes, key32: bytes) -> bytes:
    if not AES_AVAILABLE:
        raise RuntimeError("AES not available")
    nonce, ct = blob[:16], blob[16:]
    cipher = Cipher(algorithms.AES(key32), modes.CTR(nonce))
    pt = cipher.decryptor().update(ct) + cipher.decryptor().finalize()
    return pt

def to_base64_str(b: bytes) -> str:
    return base64.b64encode(b).decode("ascii")

def from_base64_str(s: str) -> bytes:
    return base64.b64decode(s.encode("ascii"))
