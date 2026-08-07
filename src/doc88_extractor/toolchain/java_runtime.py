"""Проверка доступности среды выполнения Java."""

import os
import subprocess


class JavaRuntime:
    """Находит Java в PATH или JAVA_HOME."""

    @staticmethod
    def available() -> bool:
        try:
            result = subprocess.run(
                ["java", "-version"], capture_output=True, text=True
            )
            if result.returncode == 0:
                return True
        except FileNotFoundError:
            pass

        if os.name != "nt":
            print("Java не найдена. Установите Java 17 и добавьте её в PATH.")
            return False
        java_home = os.environ.get("JAVA_HOME", "")
        java = os.path.join(java_home, "bin", "java.exe")
        if not java_home or not os.path.isfile(java):
            print("Java не найдена в PATH и JAVA_HOME.")
            return False
        os.environ["PATH"] = os.pathsep.join([
            os.path.join(java_home, "bin"),
            os.environ.get("PATH", ""),
        ])
        print("Java найдена через JAVA_HOME; рекомендуется добавить её в PATH.")
        return True
