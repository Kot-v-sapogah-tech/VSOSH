from gostcrypto.gostcipher.gost_34_12_2015 import GOST34122015Kuznechik as kuznechik


class KuznechikCipher:
    def __init__(self):
        pass

    def _normalize_key(self, key: bytes) -> bytes:
        """Дополняет ключ до 32 байт нулями, если он короче"""
        if len(key) > 32:
            raise ValueError("Ключ не должен превышать 32 байта.")
        return key.ljust(32, b'\x00')

    def _pad(self, data: bytes) -> bytes:
        """PKCS#7 padding"""
        pad_len = 16 - (len(data) % 16)
        return data + bytes([pad_len] * pad_len)

    def _unpad(self, data: bytes) -> bytes:
        """Удаление PKCS#7 padding"""
        pad_len = data[-1]
        if pad_len < 1 or pad_len > 16:
            raise ValueError("Неверная длина паддинга.")
        return data[:-pad_len]

    def encrypt(self, key: bytes, plaintext: bytes) -> bytes:
        norm_key = self._normalize_key(key)
        cipher = kuznechik(norm_key)
        padded = self._pad(plaintext)
        return b''.join(cipher.encrypt(padded[i:i+16]) for i in range(0, len(padded), 16))

    def decrypt(self, key: bytes, ciphertext: bytes) -> bytes:
        norm_key = self._normalize_key(key)
        cipher = kuznechik(norm_key)
        decrypted = b''.join(cipher.decrypt(ciphertext[i:i+16]) for i in range(0, len(ciphertext), 16))
        return self._unpad(decrypted)

