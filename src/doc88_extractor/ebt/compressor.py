
"""Модуль сжатия/распаковки SWF.

Предназначен для объединения и декодирования файлов .ebt (PH/PK) формата doc88
в единый SWF-файл.
"""

import struct
import zlib

from ..infrastructure.file_system import read_bytes, write_bytes


class Compressor:
    """Обработчик SWF: распаковывает EBT PH/PK и объединяет их в SWF."""

    def process_swf(self, file_ebt: str, file_ebt_pk: str, path: str) -> None:
        """Читает файлы PH и PK, объединяет их в SWF и сохраняет по указанному пути."""
        ph = self._decompress_ebt_ph(read_bytes(file_ebt))
        pk = self._decompress_ebt_pk(read_bytes(file_ebt_pk))
        swf = self._makeup(ph, pk)
        # Устанавливаем количество кадров равным 1
        swf[19] = 1  # Возможно, позиция может отличаться.
        # TODO: Установить корректные размеры кадра.
        # Освобождаем промежуточные буферы, чтобы уменьшить пиковое потребление памяти.
        del ph, pk
        write_bytes(swf, path)
        del swf

    @staticmethod
    def _makeup(ebt_ph: bytearray, ebt_pk: bytearray) -> bytearray:
        """Объединяет данные PH и PK и записывает длину файла в заголовок."""
        buff = bytearray()
        buff.extend(ebt_ph)
        buff.extend(ebt_pk)
        buff.extend(struct.pack("<BBBB", 64, 0, 0, 0))
        buff[4:8] = struct.pack("<I", len(buff))
        return buff

    @staticmethod
    def _decompress_ebt_ph(data: bytes) -> bytearray:
        """Распаковывает данные EBT PH, пропуская первые 40 байт заголовка."""
        buff = bytearray()
        try:
            buff.extend(zlib.decompress(data[40:]))
            buff[4:8] = struct.pack("<I", len(buff))
        except zlib.error:
            return bytearray()
        return buff

    @staticmethod
    def _decompress_ebt_pk(data: bytes) -> bytes:
        """Распаковывает данные EBT PK, пропуская первые 32 байта заголовка."""
        try:
            return zlib.decompress(data[32:])
        except zlib.error:
            return b""


def make_swf(file_ebt: str, file_ebt_pk: str, path: str) -> None:
    """Вспомогательная функция для объединения файлов PH/PK в SWF."""
    Compressor().process_swf(file_ebt, file_ebt_pk, path)
