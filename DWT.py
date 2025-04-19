import numpy as np
import pywt
import io
import zlib


class DWTSteganography:
    def __init__(self):
        self.marker = b"VSOSH"

    def _bytes_to_bits(self, data_bytes):
        return np.unpackbits(np.frombuffer(data_bytes, dtype=np.uint8))

    def _bits_to_bytes(self, bits):
        return np.packbits(bits).tobytes()

    def _dwt(self, channel):
        channel = np.asarray(channel, dtype=np.float32)
        rows, cols = channel.shape
        rows_pad = rows + (rows % 2)
        cols_pad = cols + (cols % 2)
        padded = np.zeros((rows_pad, cols_pad), dtype=channel.dtype)
        padded[:rows, :cols] = channel
        pywt.idwt2(pywt.dwt2(padded, 'haar'), 'haar')
        return

    def embed(self, image_ndarrays, file_stream: io.BufferedReader, password: str):
        file_data = zlib.compress(file_stream.read(), level=6)
        ext = file_stream.name.split('.')[-1]
        ext_bytes = ext.encode('utf-8')
        ext_len = len(ext_bytes).to_bytes(1, 'big')

        password_bytes = password.encode('utf-8')
        pass_len = len(password_bytes).to_bytes(1, 'big')

        full_data = self.marker + pass_len + password_bytes + ext_len + ext_bytes + file_data
        data_bits = self._bytes_to_bits(full_data)

        bit_cursor = 0
        bit_len = len(data_bits)
        modified_images = []

        for img in image_ndarrays:
            img = img
            height, width, _ = img.shape

            for channel_idx in range(3):
                channel = img[:, :, channel_idx]
                self._dwt(channel)
                flat = channel.reshape(-1)

                remaining = bit_len - bit_cursor
                chunk_len = min(flat.size, remaining)

                if chunk_len > 0:
                    bits = data_bits[bit_cursor:bit_cursor + chunk_len]
                    flat[:chunk_len] = (flat[:chunk_len] & 0b11111110) | bits
                    bit_cursor += chunk_len

            modified_images.append(img)

            if bit_cursor >= bit_len:
                break

        if bit_cursor < bit_len:
            raise ValueError(f"Недостаточно места. Требуется {bit_len} бит, встраивается {bit_cursor} бит.")

        return modified_images

    def extract(self, image_ndarrays, password: str):
        bit_list = []

        for img in image_ndarrays:
            for channel_idx in range(3):
                channel = img[:, :, channel_idx]
                self._dwt(channel)
                bit_list.append(channel.reshape(-1) & 1)

        all_bits = np.concatenate(bit_list)
        all_bytes = self._bits_to_bytes(all_bits)

        marker_pos = all_bytes.find(self.marker)
        if marker_pos == -1:
            raise ValueError("Маркер не найден.")

        start = marker_pos + len(self.marker)

        pass_len = all_bytes[start]
        start += 1
        stored_password = all_bytes[start:start + pass_len].decode('utf-8')
        start += pass_len

        if stored_password != password:
            raise ValueError("Неверный пароль.")

        ext_len = all_bytes[start]
        start += 1
        ext = all_bytes[start:start + ext_len].decode('utf-8')
        file_start = start + ext_len

        compressed_data = all_bytes[file_start:]
        clean_data = zlib.decompress(compressed_data)
        return clean_data, ext
