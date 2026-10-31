# Logitech C920 — LED Control (Windows e Linux)

Controle experimental do LED físico da Logitech C920 (`046d:08e5`) usando Python e o driver nativo do sistema: Kernel Streaming no Windows ou `uvcvideo`/UVC no Linux. **Não desativa a captura de vídeo.**

## Menu interativo

Execute na pasta principal do projeto:

**Windows (PowerShell):**

```powershell
py .\c920_led.py
```

**Linux:**

```bash
python3 c920_led.py
```

O terminal consulta e apresenta o status antes das opções (exemplo Linux; valores variam):

```text
=== Logitech C920 | Controle do LED ===

--- Status atual da camera ---
Logitech C920 | Linux UVC | /dev/video0 | unidade 11 | seletor 9
Estado bruto: 01 03 01 00 03
Modo atual: 3 Automatico

--- Opcoes ---
1 - ON
2 - OFF
3 - BLINKING
Selecione uma opcao (1 a 3):
```

- **1 — ON:** envia o modo ligado (`1`).
- **2 — OFF:** envia o modo desligado (`0`).
- **3 — BLINKING:** solicita um intervalo em segundos (por exemplo, `0.5`) e alterna os modos ligado e desligado pelo software. O intervalo é o tempo **em cada estado**; aceita de `0.2` a `60` segundos.

Antes da escrita, o controlador solicita confirmação e aceita `yes`, `YES`, `y` ou `Y`. Qualquer outra resposta cancela a alteração. Durante o modo BLINKING, o terminal não imprime continuamente o estado do LED e informa que **Ctrl+C interrompe a piscada e libera o terminal**. O programa tenta restaurar o modo anterior quando a piscada termina.

O menu executa uma ação por vez. Após ON ou OFF, execute o programa novamente para escolher outra ação.

## Comandos diretos (opcionais)

O menu não remove a interface de linha de comando existente:

```bash
python3 c920_led.py status
python3 c920_led.py desligar
python3 c920_led.py ligar
python3 c920_led.py automatico
python3 c920_led.py piscar-software --intervalo 0.5
```

No Windows, use `py .\c920_led.py` em vez de `python3 c920_led.py`.

## Estrutura

```text
Logitech-C920-LED-Control/
├── c920_led.py                   # Menu e detecção de sistema
├── windows/
│   └── c920_led_controle_v10.py  # Backend Windows
├── linux/
│   └── c920_led_linux.py         # Backend Linux
└── README.md
```

## Compatibilidade e limites

- **Windows:** leitura e desligamento físico já observados em uma C920 específica.
- **Linux:** leitura do controle UVC confirmada no Kubuntu 26.04 LTS; escrita e piscada ainda precisam de confirmação física.
- A opção BLINKING utiliza alternância por software, pois o modo piscante nativo (`2`) não produziu piscada visível na C920 testada.
- O Linux precisa permitir acesso ao dispositivo `/dev/video*` correspondente à webcam.
- Outras revisões da C920 podem ter parâmetros ou comportamento diferentes.
- Desligar o indicador luminoso **não** interrompe a transmissão de vídeo; respeite a privacidade de outras pessoas.

Projeto independente, não oficial da Logitech.
