"""Устанавливает внешние конвертеры при сборке контейнера."""

from doc88_extractor.core.config import Config
from doc88_extractor.toolchain.binary_tools import BinaryToolManager
from doc88_extractor.toolchain.ffdec_manager import FFDecManager


def main() -> None:
    config = Config()
    config.check_update = False
    ffdec = FFDecManager(config)
    binaries = BinaryToolManager(config)
    if not ffdec.install():
        raise SystemExit("Не удалось установить ffdec")
    for name in ("presse", "svg2pdf"):
        if not binaries.install(name):
            raise SystemExit(f"Не удалось установить {name}")


if __name__ == "__main__":
    main()
