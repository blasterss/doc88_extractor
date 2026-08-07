"""Консольная точка входа приложения."""

import argparse
from collections.abc import Sequence

from ..core.config import Config
from .interaction import run


def build_parser() -> argparse.ArgumentParser:
    """Создаёт парсер аргументов командной строки."""
    parser = argparse.ArgumentParser(
        prog="doc88-extractor",
        description="Извлечение предпросмотра документов DOC88 в PDF.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="сохранить промежуточные файлы и включить режим отладки",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Разбирает аргументы и запускает приложение."""
    args = build_parser().parse_args(argv)
    return run(Config(), debug=args.debug)
