#!/usr/bin/env python3
"""Controle experimental do LED Logitech C920 no Linux (uvcvideo/UVCIOC_CTRL_QUERY).

Testado somente em modo leitura no Kubuntu 26.04, C920 046d:08e5.
Alterações físicas ainda requerem validação.
"""
import argparse
import ctypes
import math
import os
import sys
import time
from pathlib import Path

UNIT, SELECTOR = 11, 9
GET_CUR, GET_LEN, GET_INFO, SET_CUR = 0x81, 0x85, 0x86, 0x01
MODES = {0: 'Desligado', 1: 'Ligado', 2: 'Piscando (nativo)', 3: 'Automático'}
ACTIONS = {'desligar': 0, 'ligar': 1, 'automatico': 3, 'piscar': 2}

class UvcXuControlQuery(ctypes.Structure):
    _fields_ = [('unit', ctypes.c_uint8), ('selector', ctypes.c_uint8),
                ('query', ctypes.c_uint8), ('size', ctypes.c_uint16),
                ('data', ctypes.POINTER(ctypes.c_uint8))]

def iowr(type_char, nr, size):
    return (3 << 30) | (size << 16) | (ord(type_char) << 8) | nr

UVCIOC_CTRL_QUERY = iowr('u', 0x21, ctypes.sizeof(UvcXuControlQuery))
libc = ctypes.CDLL(None, use_errno=True)
libc.ioctl.argtypes = [ctypes.c_int, ctypes.c_ulong, ctypes.c_void_p]
libc.ioctl.restype = ctypes.c_int

def query(fd, code, data):
    buf = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
    req = UvcXuControlQuery(UNIT, SELECTOR, code, len(data),
                            ctypes.cast(buf, ctypes.POINTER(ctypes.c_uint8)))
    if libc.ioctl(fd, UVCIOC_CTRL_QUERY, ctypes.byref(req)) < 0:
        err = ctypes.get_errno()
        raise OSError(err, os.strerror(err))
    return bytes(buf)

def read_state(fd):
    size = int.from_bytes(query(fd, GET_LEN, b'\0\0'), 'little')
    if size != 5:
        raise RuntimeError(f'Controle retornou {size} bytes; esperados 5. Nenhuma escrita permitida.')
    info = query(fd, GET_INFO, b'\0')[0]
    if not info & 1:
        raise RuntimeError('Controle não anuncia suporte à leitura.')
    state = query(fd, GET_CUR, bytes(size))
    if state[1] not in MODES:
        raise RuntimeError(f'Modo inesperado: {state[1]}. Nenhuma escrita permitida.')
    return state, info

def set_mode(fd, original, mode):
    payload = bytearray(original)
    payload[1] = mode
    query(fd, SET_CUR, bytes(payload))

def find_c920_devices():
    """Identifica interfaces de vídeo associadas ao USB VID:PID 046d:08e5."""
    found = []
    for entry in sorted(Path('/sys/class/video4linux').glob('video[0-9]*')):
        try:
            device = (entry / 'device').resolve()
            for parent in (device, *device.parents):
                vendor = parent / 'idVendor'
                product = parent / 'idProduct'
                if vendor.is_file() and product.is_file():
                    if vendor.read_text().strip().lower() == '046d' and product.read_text().strip().lower() == '08e5':
                        index_file = entry / 'index'
                        index = int(index_file.read_text().strip()) if index_file.exists() else 999
                        found.append((index, int(entry.name[5:]), '/dev/' + entry.name))
                    break
        except (OSError, ValueError):
            continue
    return [path for _, _, path in sorted(found)]


def select_device(override):
    if override:
        return override
    candidates = find_c920_devices()
    if not candidates:
        raise RuntimeError('Logitech C920 (046d:08e5) não encontrada. Use --dispositivo /dev/videoN se necessário.')
    # Não selecionar silenciosamente uma de várias webcams C920.
    usb_parents = set()
    for path in candidates:
        entry = Path('/sys/class/video4linux') / Path(path).name / 'device'
        try:
            for parent in (entry.resolve(), *entry.resolve().parents):
                if (parent / 'idVendor').is_file() and (parent / 'idProduct').is_file():
                    usb_parents.add(str(parent))
                    break
        except OSError:
            pass
    if len(usb_parents) > 1:
        raise RuntimeError('Mais de uma C920 encontrada. Informe --dispositivo /dev/videoN.')
    return candidates[0]


def main():
    parser = argparse.ArgumentParser(description='Controle do LED Logitech C920 no Linux')
    parser.add_argument('acao', nargs='?', default='status',
                        choices=['status', 'desligar', 'ligar', 'automatico', 'piscar', 'piscar-software'])
    parser.add_argument('--dispositivo', default=None, help='Opcional: /dev/videoN (por padrão, detectar C920 automaticamente)')
    parser.add_argument('--intervalo', type=float, default=0.5, help='Segundos por estado (0.2 a 60)')
    parser.add_argument('--duracao', type=float, default=0, help='Segundos totais; 0 = até Ctrl+C')
    args = parser.parse_args()
    if not (math.isfinite(args.intervalo) and 0.2 <= args.intervalo <= 60):
        parser.error('--intervalo deve estar entre 0.2 e 60 segundos')
    if not (math.isfinite(args.duracao) and 0 <= args.duracao <= 86400):
        parser.error('--duracao deve estar entre 0 e 86400 segundos')

    fd = None
    try:
        device = select_device(args.dispositivo)
        print(f'Logitech C920 | Linux UVC | {device} | unidade {UNIT} | seletor {SELECTOR}')
        fd = os.open(device, os.O_RDWR | getattr(os, 'O_CLOEXEC', 0))
        original, info = read_state(fd)
        print('Estado bruto:', original.hex(' '))
        print(f'Modo atual: {original[1]} {MODES[original[1]]}')
        if args.acao == 'status':
            print('Somente leitura. Nenhuma alteração realizada.')
            return 0
        if not info & 2:
            raise RuntimeError('Controle não anuncia suporte à escrita.')
        if args.acao == 'piscar-software':
            print(f'Piscada por software: alternância dos modos 1 e 0 a cada {args.intervalo:g} s.')
            print('O modo original será restaurado ao terminar, quando possível.')
        else:
            target = ACTIONS[args.acao]
            if original[1] == target:
                print('O controle já reporta o modo solicitado.')
                return 0
            print(f'Modo solicitado: {target} {MODES[target]}')
        if input('Confirmar alteracao? (yes/y): ').strip().lower() not in ('yes', 'y'):
            print('Cancelado. Nenhuma alteração realizada.')
            return 0
        if args.acao != 'piscar-software':
            set_mode(fd, original, target)
            after, _ = read_state(fd)
            print('Estado após SET:', after.hex(' '))
            print(f'Modo reportado: {after[1]} {MODES[after[1]]}')
            if after[1] != target:
                print('ATENÇÃO: o dispositivo não confirmou o modo solicitado.')
                return 2
            print('SET aceito. Confirme visualmente o comportamento físico do LED.')
            return 0

        print('Piscada em execução. Pressione CTRL + C para parar e liberar o terminal.', flush=True)
        start = time.monotonic()
        state = 1
        error = False
        try:
            while args.duracao == 0 or time.monotonic() - start < args.duracao:
                set_mode(fd, original, state)
                state = 1 - state
                sleep_time = args.intervalo
                if args.duracao:
                    sleep_time = min(sleep_time, max(0, args.duracao - (time.monotonic() - start)))
                time.sleep(sleep_time)
        except KeyboardInterrupt:
            print('\nInterrompido pelo usuário.')
        except OSError as exc:
            print(f'Falha durante a piscada: {exc}', file=sys.stderr)
            error = True
        finally:
            print('Restaurando modo original...')
            try:
                set_mode(fd, original, original[1])
                print('Comando de restauração enviado.')
            except OSError as exc:
                print(f'ATENÇÃO: falha na restauração: {exc}', file=sys.stderr)
                error = True
        return 2 if error else 0
    except (OSError, RuntimeError, EOFError) as exc:
        print(f'Erro: {exc}', file=sys.stderr)
        return 2
    finally:
        if fd is not None:
            os.close(fd)

if __name__ == '__main__':
    sys.exit(main())
