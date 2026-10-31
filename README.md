# Logitech C920 LED Control — Distribuição Windows e Linux

Projeto de empacotamento baseado na GUI v4. **Não contém executáveis compilados**: os builds devem ser realizados no sistema de destino. O aplicativo inclui Python e PySide6 ao ser compilado com PyInstaller; não precisa de Python no computador onde será instalado.

## Windows 10/11 — instalador EXE

1. Instale Python 3.11–3.13 (com o launcher `py`) e [Inno Setup 6](https://jrsoftware.org/isinfo.php) no **computador de compilação**.
2. Abra PowerShell na raiz do projeto e execute `powershell -ExecutionPolicy Bypass -File .\windows\build_windows.ps1`.
3. Encontre o instalador em `release\C920_LED_Control_Setup_Windows.exe`.
4. Execute o instalador no Windows de destino; o app será instalado para o usuário atual, com atalho no Menu Iniciar e desinstalador.

Se Inno Setup não estiver instalado, o script gera somente `dist\C920LEDControl\C920LEDControl.exe` e suas bibliotecas. **Não distribua apenas o EXE dessa pasta**: o modo `onedir` exige todos os arquivos adjacentes.

## Kubuntu/Ubuntu/Debian — instalador DEB

No **Linux de compilação** (preferencialmente mesma versão ou mais antiga que a distribuição de destino):

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip dpkg-dev build-essential
bash linux/build_linux.sh
sudo apt install ./release/c920-led-control_0.4.0_$(dpkg --print-architecture).deb
```

Abra **Logitech C920 LED Control** no menu de aplicativos ou execute `c920-led-control`. Para remover: `sudo apt remove c920-led-control`.

O `.deb` é específico à arquitetura e às bibliotecas do Linux onde foi compilado. Para Fedora, Arch e outras distribuições, o binário `dist/c920-led-control/` pode ser distribuído com os cuidados usuais de compatibilidade do sistema; o `.deb` não é instalável nativamente nelas.

## Funções

- **ON**: modo automático `3` (LED acompanha atividade da webcam).
- **OFF**: modo `0`.
- **BLINKING**: alternância via comandos curtos, intervalo ajustável; botão para parar e tentar restaurar estado anterior.
- Status e detecção de câmera, sem alterar o driver UVC.

## Observações

- A compilação não foi testada em máquinas Windows/Linux reais neste ambiente. Teste o instalador em máquina de teste antes de distribuir.
- Em Linux, o usuário deve ter permissão de acesso ao `/dev/video*` (em geral, grupo `video` ou ACL de sessão). **Não execute a GUI com sudo**.
- No Windows, o driver padrão `usbvideo.sys` continua necessário.
- Desligar o LED **não desliga a captura de vídeo**. Respeite a privacidade de todos os envolvidos.
- Para distribuição pública, adicione informações reais do mantenedor, licença do projeto e avalie assinatura digital do instalador Windows.


## Correcao da deteccao do Inno Setup

O script agora busca ISCC.exe no PATH, em instalacoes por usuario, em Program Files e no registro do Windows. Se o Inno Setup estiver em um caminho personalizado, informe:

```powershell
powershell -ExecutionPolicy Bypass -File .\windows\build_windows.ps1 -InnoSetupPath "C:\caminho\Inno Setup 6\ISCC.exe"
```

O pacote foi reduzido para conter apenas fontes e scripts. As pastas `.build-venv`, `build` e `dist` serao recriadas na compilacao.


## Correção de empacotamento PySide6

O `packaging/launcher.py` importa explicitamente `PySide6.QtCore` e
`PySide6.QtWidgets`, pois a interface real é carregada via `runpy.run_path()`
e não seria detectada automaticamente pela análise do PyInstaller.
O script Windows agora verifica se `QtCore.pyd` e `QtWidgets.pyd` estão
presentes antes de gerar o instalador. **É necessário recompilar e reinstalar**;
a instalação antiga não é corrigida apenas substituindo o ZIP.


## Correção v5: ctypes ausente no executável Windows

O launcher anterior usava `runpy.run_path` para executar os backends,
impedindo a análise de imports pelo PyInstaller. O novo launcher importa
a GUI e o backend do sistema estaticamente. Recompile **do zero** usando
`windows/build_windows.ps1` e reinstale o instalador gerado.
Não copie apenas o EXE: o modo `--onedir` depende da pasta `_internal`.


## Correção de distribuição (v6)

No modo compilado, o aplicativo executa `C920LEDControl.exe --backend windows <acao>`
(ou `c920-led-control --backend linux <acao>`). Não é necessário nem correto
procurar arquivos `.py` dentro de `_internal`. O launcher importa o backend
estaticamente, e o PyInstaller o inclui no executável. O script Windows testa
`--self-test` antes de chamar o Inno Setup. Esse teste não acessa a webcam.

Após compilar, teste o aplicativo na pasta `dist` e depois instale o novo setup.
A validação completa de ON/OFF/BLINKING exige a webcam real.
