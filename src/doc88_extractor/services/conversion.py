"""Преобразование страниц SWF/SVG и объединение итогового PDF."""

import gc
import os
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from ..core.config import Config
from ..core.gen_cfg import GenConfig
from ..infrastructure.file_system import ospath, safe_filename
from ..infrastructure.logging_utils import write_log


def _safe_rmtree(path: str | Path) -> None:
    try:
        shutil.rmtree(path)
    except PermissionError:
        print("Не удалось удалить открытый временный каталог.")
    except FileNotFoundError:
        pass


class DocumentConverter:
    """Выполняет вызовы внешних конвертеров для одного документа."""

    def __init__(self, config: Config) -> None:
        self.config = config

    def fix_display_rect(self, page: int, width: str, height: str) -> None:
        subprocess.run(
            [
                "java", "-jar", "ffdec/ffdec.jar", "-header",
                "-set", "width", f"{width}px", "-set", "height", f"{height}px",
                f"{self.config.swf_path}{page}.swf",
                f"{self.config.swf_path}{page}.swf",
            ],
            capture_output=True,
            text=True,
        )

    def divide_swfs(self, group_count: int) -> None:
        """Распределяет SWF по рабочим каталогам конвертеров."""
        source = ospath(self.config.swf_path)
        files = sorted(
            (name for name in os.listdir(source) if name.endswith(".swf")),
            key=lambda name: int(name[:-4]),
        )
        for index, name in enumerate(files):
            group = ospath(f"{self.config.swf_path}{index % group_count}/")
            os.makedirs(group, exist_ok=True)
            shutil.copy(os.path.join(source, name), os.path.join(group, name))

    def swf_to_svg(self, group_id: int) -> None:
        self._export_group(group_id, "svg")

    def swf_to_pdf(self, group_id: int) -> None:
        self._export_group(group_id, "pdf")

    def _export_group(self, group_id: int, output_format: str) -> None:
        source = ospath(f"{self.config.swf_path}{group_id}")
        if not os.path.isdir(source) or not os.listdir(source):
            return
        destination_root = (
            self.config.svg_path if output_format == "svg" else self.config.pdf_path
        )
        destination = f"{destination_root}{group_id}/"
        command = [
            "java", "-jar", "ffdec/ffdec.jar", "-format", f"frame:{output_format}",
        ]
        if output_format == "pdf":
            command.extend(["-zoom", str(self.config.pdf_scale)])
        command.extend(["-select", "1", "-export", "frame", destination, str(source)])
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            write_log(f"Ошибка экспорта {output_format.upper()}: {result.stderr or result.stdout}")

        try:
            for name in os.listdir(ospath(destination)):
                nested = ospath(f"{destination}{name}")
                if not os.path.isdir(nested):
                    continue
                source_name = "1.svg" if output_format == "svg" else "frames.pdf"
                shutil.move(
                    ospath(f"{destination}{name}/{source_name}"),
                    ospath(f"{destination_root}{name[:-4]}.{output_format}"),
                )
        except FileNotFoundError as error:
            write_log(f"Не удалось экспортировать группу {group_id}: {error}")
        finally:
            _safe_rmtree(ospath(destination))
            _safe_rmtree(source)

    def svg_to_pdf(self, page: int) -> None:
        result = subprocess.run(
            [
                "./svg2pdf",
                f"{self.config.svg_path}{page}.svg",
                f"{self.config.pdf_path}{page}.pdf",
            ],
            text=True,
            capture_output=True,
        )
        if result.returncode != 0:
            write_log(f"Ошибка SVG → PDF: {result.stderr or result.stdout}")

    def merge_pdf(self, destination: str) -> None:
        result = subprocess.run(
            [
                "./presse", "merge", f"{self.config.pdf_path}*.pdf",
                "--optimize", "-o", destination,
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr or result.stdout)


def convert(document: GenConfig, config: Config) -> str:
    """Координирует параллельное преобразование и возвращает путь к PDF."""
    workers = config.convert_workers
    converter = DocumentConverter(config)
    if config.fix_displayrect:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            for page, page_id in enumerate(document.pageids, start=1):
                parts = page_id.split("-")
                executor.submit(converter.fix_display_rect, page, parts[1], parts[2])

    converter.divide_swfs(workers)
    action = converter.swf_to_svg if config.swf2svg else converter.swf_to_pdf
    with ThreadPoolExecutor(max_workers=workers) as executor:
        for group in range(workers):
            executor.submit(action, group)

    if config.swf2svg:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            for page in range(1, document.p_count + 1):
                executor.submit(converter.svg_to_pdf, page)

    destination = config.o_dir_path + safe_filename(document.p_name) + ".pdf"
    converter.merge_pdf(str(ospath(destination)))
    gc.collect()
    print(f"Преобразование завершено. Файл сохранён: {destination}")
    return destination
