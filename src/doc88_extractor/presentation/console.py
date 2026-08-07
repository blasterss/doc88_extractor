"""Общие операции интерактивного консольного интерфейса."""


def confirm(prompt: str = "") -> bool:
    """Запрашивает подтверждение в формате Y/n."""
    prompts = {
        "": "Продолжить? (Y/n): ",
        "exists": "Каталог уже существует. Продолжить? (Y/n): ",
        "down": "Загрузить документ вместо извлечения предпросмотра? (Y/n): ",
    }
    try:
        return input(prompts.get(prompt, prompt)).strip().lower() == "y"
    except KeyboardInterrupt:
        return False


def wait_for_enter() -> None:
    """Ожидает Enter, не превращая прерывание в исключение."""
    try:
        input("Нажмите Enter для выхода...")
    except KeyboardInterrupt:
        pass
