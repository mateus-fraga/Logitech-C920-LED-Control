param([string]$InnoSetupPath)
$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path (Join-Path $PSScriptRoot '..'))
$python = 'py'
& $python -m venv .build-venv
if ($LASTEXITCODE -ne 0) { throw 'Falha ao criar ambiente virtual' }
$venv = Join-Path (Get-Location) '.build-venv\Scripts\python.exe'
& $venv -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw 'Falha ao atualizar pip' }
& $venv -m pip install -r requirements-build.txt
if ($LASTEXITCODE -ne 0) { throw 'Falha ao instalar dependencias' }
& $venv -m PyInstaller --noconfirm --clean --onedir --windowed --name C920LEDControl --paths . packaging\launcher.py
if ($LASTEXITCODE -ne 0) { throw 'Falha no PyInstaller' }
# Impede distribuir um executável sem as bibliotecas Qt/PySide6.
$qtCore = Join-Path (Get-Location) 'dist\C920LEDControl\_internal\PySide6\QtCore.pyd'
$qtWidgets = Join-Path (Get-Location) 'dist\C920LEDControl\_internal\PySide6\QtWidgets.pyd'
if (-not (Test-Path -LiteralPath $qtCore) -or -not (Test-Path -LiteralPath $qtWidgets)) {
  throw 'Build incompleto: PySide6 nao foi empacotado. Confira os imports do launcher e o log do PyInstaller.'
}
Write-Host 'PySide6 QtCore/QtWidgets presentes no pacote.'
# Validação funcional do bundle: o launcher importa ctypes, Qt e backend.
$exe = Join-Path (Get-Location) 'dist\C920LEDControl\C920LEDControl.exe'
& $exe --self-test
if ($LASTEXITCODE -ne 0) { throw "Falha no teste de dependencias do executavel (codigo $LASTEXITCODE)" }
Write-Host 'Teste do executavel empacotado aprovado (Qt, ctypes e backend).'

Write-Host 'Aplicativo pronto: dist\C920LEDControl\C920LEDControl.exe'
# Localiza o compilador Inno Setup mesmo em instalacoes por usuario,
# no PATH, em instalacoes personalizadas ou em versoes futuras.
function Find-InnoCompiler {
  param([string]$ExplicitPath)
  $candidates = New-Object 'System.Collections.Generic.List[string]'
  if ($ExplicitPath) { $candidates.Add($ExplicitPath) }
  if ($env:ISCC_PATH) { $candidates.Add($env:ISCC_PATH) }

  $cmd = Get-Command ISCC.exe -ErrorAction SilentlyContinue
  if ($cmd) { $candidates.Add($cmd.Source) }

  $roots = @($env:ProgramFiles, ${env:ProgramFiles(x86)}, $env:LOCALAPPDATA, $env:APPDATA)
  foreach ($root in $roots) {
    if (-not $root) { continue }
    foreach ($version in @('6', '7')) {
      $candidates.Add((Join-Path $root "Inno Setup $version\ISCC.exe"))
      $candidates.Add((Join-Path $root "Programs\Inno Setup $version\ISCC.exe"))
    }
  }

  # Instaladores podem registrar o caminho sob HKCU ou HKLM.
  foreach ($hive in @('HKCU:', 'HKLM:')) {
    foreach ($key in @('SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 6_is1',
                      'SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 6_is1',
                      'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 7_is1',
                      'SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 7_is1')) {
      $entry = Get-ItemProperty -LiteralPath "$hive\$key" -ErrorAction SilentlyContinue
      if ($entry -and $entry.InstallLocation) {
        $candidates.Add((Join-Path $entry.InstallLocation 'ISCC.exe'))
      }
    }
  }
  foreach ($candidate in $candidates) {
    if ($candidate -and (Test-Path -LiteralPath $candidate -PathType Leaf)) {
      return (Resolve-Path -LiteralPath $candidate).Path
    }
  }
  return $null
}

$iscc = Find-InnoCompiler -ExplicitPath $InnoSetupPath
if (-not $iscc) {
  Write-Warning 'ISCC.exe nao encontrado. O aplicativo foi compilado, mas o instalador ainda nao foi criado.'
  Write-Host 'Localize ISCC.exe e execute novamente informando o caminho:'
  Write-Host 'powershell -ExecutionPolicy Bypass -File .\windows\build_windows.ps1 -InnoSetupPath "C:\caminho\para\ISCC.exe"'
  exit 1
}
Write-Host "Compilador Inno Setup encontrado: $iscc"
& $iscc (Join-Path $PSScriptRoot 'installer.iss')
if ($LASTEXITCODE -ne 0) { throw "Falha ao criar instalador Inno Setup (codigo $LASTEXITCODE)" }
Write-Host 'Instalador pronto: release\C920_LED_Control_Setup_Windows.exe'
