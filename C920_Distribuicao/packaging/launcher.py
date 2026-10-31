"""Entrada estática para o PyInstaller: GUI e backends analisáveis."""
import sys
from pathlib import Path

# Os imports explícitos são fundamentais: runpy.run_path() não permite que
# o PyInstaller descubra as dependências dos scripts carregados dinamicamente.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import c920_led_gui

if sys.platform == 'win32':
    from windows import c920_led_controle_v10 as platform_backend
elif sys.platform.startswith('linux'):
    from linux import c920_led_linux as platform_backend
else:
    platform_backend = None


def main():
    # Verificação de imports para o build, sem acesso ao hardware.
    if len(sys.argv) > 1 and sys.argv[1] == '--self-test':
        import ctypes
        from PySide6.QtCore import QProcess
        from PySide6.QtWidgets import QApplication
        return 0 if platform_backend is not None else 3
    if len(sys.argv) > 1 and sys.argv[1] == '--backend':
        if len(sys.argv) < 4:
            raise SystemExit('Uso: --backend <windows|linux> <acao>')
        platform = 'windows' if sys.platform == 'win32' else 'linux'
        if sys.argv[2] != platform or platform_backend is None:
            raise SystemExit('Backend incompatível com o sistema operacional')
        sys.argv = [platform_backend.__file__, *sys.argv[3:]]
        return platform_backend.main()
    return c920_led_gui.main()


if __name__ == '__main__':
    sys.exit(main())
