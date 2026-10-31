#!/usr/bin/env python3
"""Menu multiplataforma para o LED da Logitech C920.

Sem argumentos: menu 1/2/3. Com argumentos: encaminha comandos antigos.
"""
import math
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def backend():
    if sys.platform == 'win32':
        script = ROOT / 'windows' / 'c920_led_controle_v10.py'
    elif sys.platform.startswith('linux'):
        script = ROOT / 'linux' / 'c920_led_linux.py'
    else:
        raise RuntimeError(f'Sistema operacional nao suportado: {sys.platform}')
    if not script.is_file():
        raise FileNotFoundError(f'Arquivo necessario nao encontrado: {script}')
    return script


def intervalo():
    while True:
        valor = input('Intervalo em segundos (ex.: 0.5): ').strip().replace(',', '.')
        try:
            numero = float(valor)
        except ValueError:
            print('Digite um numero valido, por exemplo 0.5.')
            continue
        if math.isfinite(numero) and 0.2 <= numero <= 60:
            return numero
        print('O intervalo deve estar entre 0.2 e 60 segundos.')


def main():
    try:
        script = backend()
    except (RuntimeError, FileNotFoundError) as exc:
        print(f'Erro: {exc}', file=sys.stderr)
        return 2

    if len(sys.argv) > 1:
        return subprocess.run([sys.executable, str(script), *sys.argv[1:]]).returncode

    print('\n=== Logitech C920 | Controle do LED ===', flush=True)
    print('\n--- Status atual da camera ---', flush=True)
    consulta = subprocess.run(
        [sys.executable, str(script), 'status'],
        capture_output=True, text=True, errors='replace'
    )
    if consulta.returncode == 0:
        for linha in consulta.stdout.splitlines():
            if not linha.startswith('Somente leitura.'):
                print(linha)
    else:
        print('Nao foi possivel consultar o status do LED.')
        if consulta.stderr.strip():
            print(consulta.stderr.strip())
        elif consulta.stdout.strip():
            print(consulta.stdout.strip())
    print('\n--- Opcoes ---')
    print('1 - ON')
    print('2 - OFF')
    print('3 - BLINKING')
    while True:
        try:
            escolha = input('Selecione uma opcao (1 a 3): ').strip()
            if escolha in ('1', '2', '3'):
                break
            print('Opcao invalida. Escolha 1, 2 ou 3.')
        except (EOFError, KeyboardInterrupt):
            print('\nOperacao cancelada.')
            return 0

    comando = {'1': 'ligar', '2': 'desligar', '3': 'piscar-software'}[escolha]
    args = [sys.executable, str(script), comando]
    if escolha == '3':
        try:
            args.extend(['--intervalo', str(intervalo())])
        except (EOFError, KeyboardInterrupt):
            print('\nOperacao cancelada.')
            return 0
    print()
    try:
        return subprocess.run(args).returncode
    except KeyboardInterrupt:
        # O backend restaura o modo anterior ao receber Ctrl+C.
        print('\nInterrompido. Terminal liberado.')
        return 130


if __name__ == '__main__':
    sys.exit(main())
