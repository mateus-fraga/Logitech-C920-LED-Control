#!/usr/bin/env python3
"""Interface Qt não bloqueante para Logitech C920 em Windows e Linux."""
import os
import re
import signal
import subprocess
import sys
from pathlib import Path
from PySide6.QtCore import QProcess, QTimer
from PySide6.QtWidgets import (QApplication, QDoubleSpinBox, QFormLayout,
    QGroupBox, QHBoxLayout, QLabel, QMainWindow, QMessageBox, QPushButton,
    QVBoxLayout, QWidget)

ROOT = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))

def backend():
    # No executável congelado, o backend é chamado pelo próprio launcher.
    if getattr(sys, 'frozen', False):
        return None
    if sys.platform == 'win32':
        return ROOT / 'windows' / 'c920_led_controle_v10.py'
    if sys.platform.startswith('linux'):
        return ROOT / 'linux' / 'c920_led_linux.py'
    raise RuntimeError('Sistema operacional não suportado')

class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Logitech C920 - Controle do LED')
        self.resize(480, 310)
        self.proc = None
        self.action = None
        self.stop_requested = False
        self.output = ''
        self.error_text = ''
        self.closing = False
        self.original_mode = None
        self.restore_mode = None
        self.blinking = False
        self.blink_stopping = False
        self.blink_next = 1
        self.blink_timer = QTimer(self)
        self.blink_timer.setSingleShot(True)
        self.blink_timer.timeout.connect(self.blink_tick)

        central = QWidget(self)
        self.setCentralWidget(central)
        main = QVBoxLayout(central)
        main.setSpacing(12)
        status = QGroupBox('Informações da câmera')
        form = QFormLayout(status)
        self.system = QLabel('Windows' if sys.platform == 'win32' else 'Linux')
        self.device = QLabel('Aguardando consulta...')
        self.mode = QLabel('Aguardando consulta...')
        form.addRow('Sistema:', self.system)
        form.addRow('Dispositivo:', self.device)
        form.addRow('Estado do LED:', self.mode)
        main.addWidget(status)

        controls = QGroupBox('Controle do LED')
        controls_layout = QVBoxLayout(controls)
        row = QHBoxLayout()
        self.on_btn = QPushButton('ON (Automático)')
        self.off_btn = QPushButton('OFF')
        self.blink_btn = QPushButton('BLINKING')
        for b in (self.on_btn, self.off_btn, self.blink_btn):
            row.addWidget(b)
        controls_layout.addLayout(row)
        interval_row = QHBoxLayout()
        interval_row.addWidget(QLabel('Intervalo (segundos):'))
        self.interval = QDoubleSpinBox()
        self.interval.setRange(0.2, 60.0)
        self.interval.setDecimals(2)
        self.interval.setSingleStep(0.1)
        self.interval.setValue(0.5)
        interval_row.addWidget(self.interval)
        controls_layout.addLayout(interval_row)
        self.stop_btn = QPushButton('Parar piscada')
        self.stop_btn.setEnabled(False)
        controls_layout.addWidget(self.stop_btn)
        main.addWidget(controls)

        footer = QHBoxLayout()
        self.message = QLabel('Pronto.')
        self.message.setWordWrap(True)
        footer.addWidget(self.message, 1)
        self.refresh_btn = QPushButton('Atualizar status')
        footer.addWidget(self.refresh_btn)
        main.addLayout(footer)

        self.on_btn.clicked.connect(lambda: self.confirm('automatico'))
        self.off_btn.clicked.connect(lambda: self.confirm('desligar'))
        self.blink_btn.clicked.connect(lambda: self.confirm('piscar-software'))
        self.stop_btn.clicked.connect(self.stop_blink)
        self.refresh_btn.clicked.connect(self.refresh)
        # O Qt desenha a janela antes de iniciar qualquer acesso ao hardware.
        QTimer.singleShot(400, self.refresh)

    def busy(self, state, blink=False):
        for widget in (self.on_btn, self.off_btn, self.blink_btn, self.refresh_btn, self.interval):
            widget.setEnabled(not state)
        self.stop_btn.setEnabled(state and blink)

    def refresh(self):
        if self.proc is not None or self.blinking:
            return
        self.start('status')

    def confirm(self, action):
        if self.proc is not None or self.blinking:
            return
        desc = {'automatico': 'ativar o LED em modo automático',
                'desligar': 'desligar o LED',
                'piscar-software': 'iniciar a piscada do LED'}[action]
        answer = QMessageBox.question(self, 'Confirmar alteração',
            f'Deseja {desc}?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        if answer == QMessageBox.StandardButton.Yes:
            if action == 'piscar-software':
                self.begin_blink()
            else:
                self.start(action)

    def begin_blink(self):
        m = re.search(r'^([0-3])\b', self.mode.text())
        if not m:
            QMessageBox.warning(self, 'Estado desconhecido',
                'Atualize o status antes de iniciar a piscada.')
            return
        self.original_mode = int(m.group(1))
        self.blinking = True
        self.blink_stopping = False
        self.blink_next = 1
        self.busy(True, True)
        self.message.setText('Piscada em execução. Clique em "Parar piscada" para interromper.')
        self.blink_tick()

    def blink_tick(self):
        if not self.blinking or self.blink_stopping or self.proc is not None:
            return
        action = 'ligar' if self.blink_next == 1 else 'desligar'
        self.blink_next = 1 - self.blink_next
        self.start(action, internal=True)

    def restore_blink(self):
        self.blink_timer.stop()
        if self.proc is not None:
            return
        mode = self.original_mode
        self.original_mode = None
        self.blinking = False
        self.blink_stopping = False
        self.message.setText('Restaurando estado anterior...')
        restore = {0:'desligar', 1:'ligar', 2:'piscar', 3:'automatico'}.get(mode, 'automatico')
        self.start(restore)


    def start(self, action, internal=False):
        try:
            script = backend()
            if script is not None and not script.is_file():
                raise FileNotFoundError(f'Controlador não encontrado: {script}')
        except Exception as exc:
            QMessageBox.warning(self, 'Controlador indisponível', str(exc))
            return
        self.action = action
        self.stop_requested = False
        self.output = ''
        self.error_text = ''
        proc = QProcess(self)
        proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        proc.setWorkingDirectory(str(Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else ROOT))
        args = ['--backend', 'windows' if sys.platform == 'win32' else 'linux', action] if getattr(sys, 'frozen', False) else ['-u', str(script), action]
        if action == 'piscar-software':
            args += ['--intervalo', str(self.interval.value())]
        proc.readyReadStandardOutput.connect(lambda p=proc: self.read_output(p))
        proc.started.connect(lambda p=proc: self.started(p))
        proc.errorOccurred.connect(lambda error, p=proc: self.process_error(p))
        proc.finished.connect(lambda code, status, p=proc: self.finished(p, code, status))
        self.proc = proc
        self.busy(True, self.blinking)
        if not self.blinking:
            self.message.setText('Consultando câmera...' if action == 'status' else 'Enviando comando...')
        proc.start(sys.executable, args)

    def started(self, proc):
        if proc is not self.proc:
            return
        if self.action != 'status':
            # Backends existentes ainda usam input(); a confirmação gráfica
            # já foi obtida antes de iniciar o processo.
            proc.write(b'yes\n')
            # Não fechar o canal antes de o backend consumir a confirmação.
        if self.action == 'piscar-software':
            self.message.setText('Piscada em execução. Clique em "Parar piscada" para interromper.')

    def read_output(self, proc):
        data = bytes(proc.readAllStandardOutput()).decode('utf-8', errors='replace')
        self.output = (self.output + data)[-16000:]

    def process_error(self, proc):
        if proc is self.proc:
            self.error_text = proc.errorString()

    def stop_blink(self):
        if not self.blinking or self.blink_stopping:
            return
        self.blink_stopping = True
        self.blink_timer.stop()
        self.stop_btn.setEnabled(False)
        self.message.setText('Parando piscada e restaurando estado anterior...')
        # O comando de SET em andamento termina normalmente; nenhum processo
        # precisa ser interrompido à força.
        if self.proc is None:
            self.restore_blink()

    def finished(self, proc, code, status):
        if proc is not self.proc:
            return
        self.read_output(proc)
        action = self.action
        output = self.output
        error_text = self.error_text
        self.proc = None
        self.action = None
        proc.deleteLater()
        if self.blinking:
            if code != 0:
                self.blink_stopping = True
                self.blink_timer.stop()
                QMessageBox.warning(self, 'Falha na piscada',
                    output[-2000:] or error_text or f'Código {code}')
            if self.blink_stopping:
                self.restore_blink()
            else:
                self.blink_timer.start(round(self.interval.value() * 1000))
            return
        self.busy(False)
        if action == 'status':
            device = re.search(r'/dev/video\d+', output)
            self.device.setText(device.group(0) if device else ('Logitech C920' if code == 0 else 'Não detectada'))
            mode = re.search(r'Modo atual:\s*([^\r\n]+)', output)
            self.mode.setText(mode.group(1).strip() if mode else 'Indisponível')
            self.message.setText('Status atualizado.' if code == 0 else 'Falha ao consultar a câmera.')
            if code != 0:
                QMessageBox.warning(self, 'Falha na consulta', output[-2000:] or error_text or str(code))
        elif code == 0:
            self.message.setText('Comando concluído.')
            QTimer.singleShot(250, self.refresh)
        else:
            self.message.setText('Não foi possível concluir o comando.')
            QMessageBox.warning(self, 'Erro no controle do LED', output[-2000:] or error_text or str(code))

    def closeEvent(self, event):
        if self.proc is not None or self.blinking:
            QMessageBox.information(self, 'Operação em execução',
                'Interrompa a piscada ou aguarde a operação terminar antes de fechar.')
            event.ignore()
        else:
            event.accept()

def main():
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    return app.exec()

if __name__ == '__main__':
    sys.exit(main())
