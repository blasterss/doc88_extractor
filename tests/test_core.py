"""Быстрые тесты чистых компонентов пакета."""

import json
import os
import tempfile
import unittest
from pathlib import Path

from doc88_extractor.compat.ebt_import import build_cfg
from doc88_extractor.core.coder import decode, encode
from doc88_extractor.core.config import Config
from doc88_extractor.core.gen_cfg import GenConfig
from doc88_extractor.infrastructure.file_system import safe_filename
from doc88_extractor.services.document_catalog import DocumentCatalog
from doc88_extractor.services.document_source import decode_main


class CodecTests(unittest.TestCase):
    def test_round_trip(self) -> None:
        source = "DOC88: тестовая строка"
        self.assertEqual(decode(encode(source)), source)

    def test_main_data_decoding(self) -> None:
        source = {"p_code": "123"}
        self.assertEqual(decode_main(encode(json.dumps(source))), source)


class DocumentConfigTests(unittest.TestCase):
    def test_build_and_parse_config(self) -> None:
        ph = [{"level": 1, "chunk_size": 455235, "p_swf": "63-20200101-file"}]
        pk = [
            {
                "level": 1,
                "width": "595",
                "height": "841",
                "headsize": "455235",
                "chunk_size": "3936",
                "p_swf": "63-20200101-file",
                "page": 1,
                "p_code": "123456",
            }
        ]

        config = build_cfg(ph, pk, doc_name="Тест")
        parsed = GenConfig(config)

        self.assertEqual(parsed.p_name, "Тест")
        self.assertEqual(parsed.p_count, 1)
        self.assertEqual(parsed.ph_num(1), 1)
        self.assertIn("getebt-", parsed.ph(1).url)
        self.assertIn("getebt-", parsed.pk(1).url)

    def test_local_ebt_defaults_dimensions(self) -> None:
        ph = [{"level": 1, "chunk_size": 12, "p_swf": "63-20200101-file"}]
        pk = [
            {
                "level": 1,
                "headsize": 12,
                "chunk_size": 34,
                "p_swf": "63-20200101-file",
                "page": 1,
                "p_code": "42",
            }
        ]
        parsed = GenConfig(build_cfg(ph, pk))
        self.assertIn("-612-858-", parsed.pageids[0])


class InfrastructureTests(unittest.TestCase):
    def test_config_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "config.json")
            config = Config(path)
            config.clean = False
            config.save()
            self.assertFalse(Config(path).clean)

    def test_catalog_rebuild(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            item = Path(directory, "123")
            item.mkdir()
            item.joinpath("index.json").write_text(
                json.dumps({"p_code": "123", "p_name": "Документ"}),
                encoding="utf-8",
            )
            DocumentCatalog(directory).rebuild_index()
            index = json.loads(Path(directory, "indexs.json").read_text(encoding="utf-8"))
            self.assertEqual(index, {"123": "Документ"})

    def test_safe_filename(self) -> None:
        self.assertEqual(safe_filename("a:b?.pdf"), "a：b？.pdf")


if __name__ == "__main__":
    unittest.main()
