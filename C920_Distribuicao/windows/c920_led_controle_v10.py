"""Controle experimental do LED Logitech C920 no Windows via Kernel Streaming.
Comandos: status, desligar, ligar, piscar, piscar-software, automatico. Escrita exige confirmacao.
"""
import ctypes as ct
from ctypes import wintypes as wt
import sys
import uuid
import time
import signal

VIDPID = 'vid_046d&pid_08e5'
CAMERA_CATEGORY = 'e5323777-f976-4f5b-9b55-b94699c46e44'
TOPOLOGY_SET = '720d4ac0-7533-11d0-a5d6-28db04c10000'
LOGITECH_XU = 'ffe52d21-8030-4e2c-82d9-f587d00540bd'
LED_SELECTOR = 9
IOCTL_KS_PROPERTY = 0x002F0003
GET = 0x00000001
BASICSUPPORT = 0x00000200
TOPOLOGY_FLAG = 0x10000000
INVALID = ct.c_void_p(-1).value

class GUID(ct.Structure):
    _fields_ = [('Data1', wt.DWORD), ('Data2', wt.WORD), ('Data3', wt.WORD), ('Data4', ct.c_ubyte * 8)]
    @classmethod
    def parse(cls, value):
        return cls.from_buffer_copy(uuid.UUID(value).bytes_le)

class IFACE(ct.Structure):
    _fields_ = [('cbSize', wt.DWORD), ('InterfaceClassGuid', GUID), ('Flags', wt.DWORD), ('Reserved', ct.c_size_t)]

class PROP(ct.Structure):
    _fields_ = [('Set', GUID), ('Id', wt.ULONG), ('Flags', wt.ULONG)]

class NODE_PROP(ct.Structure):
    _fields_ = [('Property', PROP), ('NodeId', wt.ULONG), ('Reserved', wt.ULONG)]

def init_api():
    s = ct.WinDLL('setupapi', use_last_error=True)
    k = ct.WinDLL('kernel32', use_last_error=True)
    s.SetupDiGetClassDevsW.argtypes = [ct.POINTER(GUID), wt.LPCWSTR, wt.HWND, wt.DWORD]
    s.SetupDiGetClassDevsW.restype = ct.c_void_p
    s.SetupDiEnumDeviceInterfaces.argtypes = [ct.c_void_p, ct.c_void_p, ct.POINTER(GUID), wt.DWORD, ct.POINTER(IFACE)]
    s.SetupDiEnumDeviceInterfaces.restype = wt.BOOL
    s.SetupDiGetDeviceInterfaceDetailW.argtypes = [ct.c_void_p, ct.POINTER(IFACE), ct.c_void_p, wt.DWORD, ct.POINTER(wt.DWORD), ct.c_void_p]
    s.SetupDiGetDeviceInterfaceDetailW.restype = wt.BOOL
    s.SetupDiDestroyDeviceInfoList.argtypes = [ct.c_void_p]
    s.SetupDiDestroyDeviceInfoList.restype = wt.BOOL
    k.CreateFileW.argtypes = [wt.LPCWSTR, wt.DWORD, wt.DWORD, ct.c_void_p, wt.DWORD, wt.DWORD, ct.c_void_p]
    k.CreateFileW.restype = ct.c_void_p
    k.CloseHandle.argtypes = [ct.c_void_p]
    k.CloseHandle.restype = wt.BOOL
    k.DeviceIoControl.argtypes = [ct.c_void_p, wt.DWORD, ct.c_void_p, wt.DWORD, ct.c_void_p, wt.DWORD, ct.POINTER(wt.DWORD), ct.c_void_p]
    k.DeviceIoControl.restype = wt.BOOL
    return s, k

def paths(s):
    g = GUID.parse(CAMERA_CATEGORY)
    h = s.SetupDiGetClassDevsW(ct.byref(g), None, None, 0x12)
    if h == INVALID:
        return []
    found = []
    try:
        i = 0
        while True:
            inf = IFACE()
            inf.cbSize = ct.sizeof(inf)
            if not s.SetupDiEnumDeviceInterfaces(h, None, ct.byref(g), i, ct.byref(inf)):
                break
            i += 1
            needed = wt.DWORD()
            s.SetupDiGetDeviceInterfaceDetailW(h, ct.byref(inf), None, 0, ct.byref(needed), None)
            if not needed.value:
                continue
            buf = ct.create_string_buffer(needed.value)
            ct.cast(buf, ct.POINTER(wt.DWORD))[0] = 8 if ct.sizeof(ct.c_void_p) == 8 else 6
            if s.SetupDiGetDeviceInterfaceDetailW(h, ct.byref(inf), buf, len(buf), ct.byref(needed), None):
                p = ct.wstring_at(ct.addressof(buf) + 4)
                if VIDPID in p.lower():
                    found.append(p)
    finally:
        s.SetupDiDestroyDeviceInfoList(h)
    return found

def request(k, h, guid, selector, flags, node=None, outlen=512):
    prop = PROP(GUID.parse(guid), selector, flags)
    req = prop if node is None else NODE_PROP(prop, node, 0)
    buf = ct.create_string_buffer(outlen)
    returned = wt.DWORD()
    ct.set_last_error(0)
    ok = k.DeviceIoControl(h, IOCTL_KS_PROPERTY, ct.byref(req), ct.sizeof(req), buf, outlen, ct.byref(returned), None)
    return (buf.raw[:returned.value], None) if ok else (None, ct.get_last_error())

SET = 0x00000002
TARGET_NODE = 7

def write_led(k, h, original, mode):
    """KS SET: KSP_NODE no buffer de entrada; valor em lpOutBuffer.

    IOCTL_KS_PROPERTY segue a convencao KS: a estrutura KSPROPERTY/KSP_NODE
    e passada como entrada e o valor da propriedade em buffer separado.
    """
    prop = PROP(GUID.parse(LOGITECH_XU), LED_SELECTOR, SET | TOPOLOGY_FLAG)
    req = NODE_PROP(prop, TARGET_NODE, 0)
    payload = bytearray(original)
    payload[1] = mode
    data = ct.create_string_buffer(bytes(payload), len(payload))
    returned = wt.DWORD()
    ct.set_last_error(0)
    ok = k.DeviceIoControl(h, IOCTL_KS_PROPERTY,
                           ct.byref(req), ct.sizeof(req),
                           data, len(payload), ct.byref(returned), None)
    return None if ok else ct.get_last_error()

def main():
    if sys.platform != 'win32':
        print('Execute no Windows.'); return 2
    if hasattr(signal, 'SIGBREAK'):
        signal.signal(signal.SIGBREAK, lambda signum, frame: (_ for _ in ()).throw(KeyboardInterrupt()))
    import argparse
    parser = argparse.ArgumentParser(description='C920 LED: consulta ou muda modo com confirmacao (KS SET buffer separado).')
    parser.add_argument('acao', nargs='?', choices=('status','desligar','ligar','piscar','piscar-software','automatico'), default='status')
    parser.add_argument('--intervalo', type=float, default=0.5, help='Segundos por estado no piscar-software (padrao: 0.5; minimo: 0.2)')
    parser.add_argument('--duracao', type=float, default=0, help='Tempo total de piscada em segundos; 0 = ate Ctrl+C')
    args = parser.parse_args()
    if args.acao == 'piscar-software' and (not 0.2 <= args.intervalo <= 60 or not 0 <= args.duracao <= 86400):
        parser.error('Use --intervalo entre 0.2 e 60 e --duracao entre 0 e 86400.')
    print('Logitech C920 | KS XU LED | v9 | no 7 | seletor 9')
    s, k = init_api()
    devices = paths(s)
    if len(devices) != 1:
        print('Esperada exatamente 1 interface de camera; encontradas:', len(devices)); return 2
    h = k.CreateFileW(devices[0], 0x80000000 | (0x40000000 if args.acao != 'status' else 0),
                      3, None, 3, 0, None)
    if h == INVALID:
        print('Falha CreateFileW:', ct.get_last_error()); return 2
    try:
        current, err = request(k, h, LOGITECH_XU, LED_SELECTOR, GET | TOPOLOGY_FLAG, TARGET_NODE, 32)
        if err is not None or current is None:
            print('GET falhou:', err); return 2
        print('Estado bruto:', current.hex(' ').upper())
        if len(current) != 5:
            print('Comprimento inesperado; nenhuma alteracao.'); return 2
        if current[1] not in (0,1,2,3):
            print('Modo inesperado no byte 1; nenhuma alteracao.'); return 2
        names = ['Desligado','Ligado','Piscando','Automatico']
        print('Modo atual:', current[1], names[current[1]])
        if args.acao == 'status':
            print('Somente leitura. Para alterar: desligar, piscar ou automatico.'); return 0
        target = {'desligar': 0, 'ligar': 1, 'piscar': 2, 'automatico': 3, 'piscar-software': 1}[args.acao]
        if args.acao != 'piscar-software' and current[1] == target:
            print('Ja esta no modo solicitado.'); return 0
        if args.acao == 'piscar-software':
            print(f'Piscar por software: alternar 1 (ligado) e 0 (desligado) a cada {args.intervalo:g} s.')
            print('Modo 1 ainda nao foi validado fisicamente nesta webcam.')
            print('O modo original sera restaurado ao terminar, quando possivel.')
        else:
            print('Novo valor proposto:', (current[:1]+bytes([target])+current[2:]).hex(' ').upper())
        print('Sera enviado um unico SET no controle LED. Outros bytes serao preservados.')
        confirm = input('Confirmar alteracao? (yes/y): ').strip().lower()
        if confirm not in ('yes', 'y'):
            print('Cancelado, sem escrita.'); return 0
        if args.acao == 'piscar-software':
            print('Piscada em execucao. Pressione CTRL + C para parar e liberar o terminal.', flush=True)
            inicio = time.monotonic()
            ultimo_erro = None
            try:
                estado = 1
                while args.duracao == 0 or time.monotonic() - inicio < args.duracao:
                    ultimo_erro = write_led(k, h, current, estado)
                    if ultimo_erro is not None:
                        print(f'Falha ao escrever modo {estado}: Win32 {ultimo_erro}')
                        break
                    estado = 1 - estado
                    tempo = args.intervalo
                    if args.duracao:
                        tempo = min(tempo, max(0, args.duracao - (time.monotonic() - inicio)))
                    time.sleep(tempo)
            except KeyboardInterrupt:
                print('\nInterrompido pelo usuario.')
            finally:
                print('Restaurando modo original...')
                erro_restore = write_led(k, h, current, current[1])
                if erro_restore is not None:
                    print('ATENCAO: falha na restauracao (Win32):', erro_restore)
                    print('Execute: py .\\c920_led_controle_v10.py automatico')
                else:
                    print('Comando de restauracao enviado.')
            return 2 if ultimo_erro is not None or erro_restore is not None else 0
        err = write_led(k, h, current, target)
        if err is not None:
            print('SET falhou (Win32):', err); return 2
        print('SET aceito pelo Windows. Consultando novamente...')
        after, err = request(k, h, LOGITECH_XU, LED_SELECTOR, GET | TOPOLOGY_FLAG, TARGET_NODE, 32)
        if err is not None or after is None:
            print('Nao foi possivel confirmar por GET:', err); return 2
        print('Estado apos SET:', after.hex(' ').upper())
        print('Modo reportado:', names[after[1]] if len(after)==5 and after[1]<4 else 'desconhecido')
        if len(after) == 5 and after[1] != target:
            print('AVISO: o dispositivo nao confirmou o modo solicitado.')
            return 2
        return 0
    finally:
        k.CloseHandle(h)

if __name__ == '__main__':
    sys.exit(main())
