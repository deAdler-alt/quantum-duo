import numpy as np, json

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

def xor_bytes(data: bytes, key: bytes) -> bytes:
    if not key:
        return data
    k = np.frombuffer(key, dtype=np.uint8)
    d = np.frombuffer(data, dtype=np.uint8)
    out = np.empty_like(d)
    for i in range(len(d)):
        out[i] = d[i] ^ k[i % len(k)]
    return out.tobytes()

def json_encrypt(obj, key_bytes: bytes) -> bytes:
    data = json.dumps(obj, separators=(',',':')).encode("utf-8")
    return xor_bytes(data, key_bytes)

def json_decrypt(enc: bytes, key_bytes: bytes):
    data = xor_bytes(enc, key_bytes).decode("utf-8")
    return json.loads(data)
