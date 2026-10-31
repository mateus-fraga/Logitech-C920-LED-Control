# Logitech C920 LED Control

Aplicativo com interface gráfica para controlar o LED de atividade da webcam **Logitech C920** no Windows e no Linux.

## 📥 Download e instalação (usuários)

**Não é necessário instalar Python, PySide6, PyInstaller ou Inno Setup para usar uma versão já compilada.**

Acesse a página oficial de versões do projeto:

**[Baixar pelo GitHub Releases](https://github.com/mateus-fraga/Logitech-C920-LED-Control/releases)**

Abra a versão mais recente e procure a seção **Assets** (Arquivos). Escolha o arquivo correspondente ao seu sistema. **Os nomes abaixo são exemplos previstos pelo projeto; confirme os arquivos efetivamente publicados na página.** Se não houver instaladores disponíveis em Assets, ainda será necessário publicá-los.

### Windows 10/11

1. Acesse **[Releases](https://github.com/mateus-fraga/Logitech-C920-LED-Control/releases)**.
2. Na versão mais recente, em **Assets**, baixe o instalador Windows, por exemplo `C920_LED_Control_Setup_Windows.exe`.
3. Execute o arquivo baixado e siga o assistente de instalação.
4. Abra **Logitech C920 LED Control** pelo Menu Iniciar.

O instalador foi projetado para criar um atalho no Menu Iniciar e permitir a desinstalação pelos aplicativos instalados do Windows. O aplicativo utiliza o driver padrão da webcam (`usbvideo.sys`).

> **Atenção:** baixe o **instalador** publicado em Releases. O arquivo `C920LEDControl.exe` da pasta de compilação `dist` não deve ser distribuído sozinho: ele depende da pasta `_internal` e dos demais arquivos do build `onedir`.

### Linux — Kubuntu, Ubuntu e Debian

1. Acesse **[Releases](https://github.com/mateus-fraga/Logitech-C920-LED-Control/releases)**.
2. Na seção **Assets**, baixe o pacote `.deb` compatível com sua arquitetura, por exemplo `c920-led-control_0.4.0_amd64.deb`.
3. Abra a pasta onde o arquivo foi baixado e instale pelo gerenciador de pacotes ou pelo terminal:

   ```bash
   sudo apt install ./c920-led-control_0.4.0_amd64.deb
   ```

   Substitua o nome no comando pelo **nome exato do arquivo baixado**.
4. Abra **Logitech C920 LED Control** pelo menu de aplicativos do KDE/GNOME ou execute `c920-led-control`.

Para remover:

```bash
sudo apt remove c920-led-control
```

**Permissões:** o usuário precisa ter acesso ao dispositivo `/dev/video*`, normalmente concedido pelo grupo `video` ou por ACL da sessão. **Não execute a interface gráfica com `sudo`.** Pacotes `.deb` não são instaláveis nativamente em Fedora ou Arch; não há instruções de instalação prontas para essas distribuições neste projeto.

## Funcionalidades

- **ON (Automático):** modo `3`; o LED acompanha a atividade da webcam.
- **OFF:** modo `0`; desliga o LED.
- **BLINKING:** alterna o LED com intervalo configurável.
- **Parar piscada:** interrompe a alternância e tenta restaurar o estado anterior.
- **Status:** consulta o estado e a detecção da câmera.

**Aviso de privacidade:** desligar o LED **não interrompe a captura de vídeo**. Respeite a privacidade das pessoas envolvidas.

---

## 🛠️ Compilação a partir do código-fonte (desenvolvedores)

Esta seção é **somente para quem deseja criar os instaladores**. Usuários finais devem baixar os arquivos em **GitHub Releases**, conforme explicado acima. O projeto-fonte não inclui necessariamente binários já compilados.

### Gerar o instalador Windows

No computador de compilação, instale Python compatível com o projeto e [Inno Setup 6](https://jrsoftware.org/isinfo.php). Na raiz do projeto, execute no PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\windows\build_windows.ps1
```

Instalador esperado:

```text
release\C920_LED_Control_Setup_Windows.exe
```

Se o Inno Setup estiver instalado em um caminho personalizado:

```powershell
powershell -ExecutionPolicy Bypass -File .\windows\build_windows.ps1 -InnoSetupPath "C:\caminho\Inno Setup 6\ISCC.exe"
```

Se o script gerar apenas `dist\C920LEDControl\C920LEDControl.exe`, ainda não há um instalador completo. Não distribua esse `.exe` isoladamente.

### Gerar o pacote Linux `.deb`

No Linux de compilação (preferencialmente uma versão igual ou mais antiga que a de destino):

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip dpkg-dev build-essential
bash linux/build_linux.sh
```

Pacote esperado, sujeito à versão e arquitetura:

```text
release/c920-led-control_0.4.0_amd64.deb
```

O pacote é específico à arquitetura e pode depender da compatibilidade das bibliotecas do Linux usado na compilação.

### Antes de publicar no GitHub Releases

1. Compile cada instalador no sistema operacional correspondente.
2. Teste a abertura do aplicativo e as funções **ON, OFF, BLINKING e Parar piscada** com uma Logitech C920 real.
3. Confirme a instalação e a desinstalação em uma máquina de teste.
4. Crie uma versão na aba **Releases** do GitHub e anexe os instaladores à seção **Assets**.

**Estado de validação:** a existência de scripts de build não comprova que os instaladores estejam publicados ou testados. A validação funcional completa exige a webcam real. Para distribuição pública, inclua licença, informações do mantenedor e considere assinatura digital do instalador Windows.
