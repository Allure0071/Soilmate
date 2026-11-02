# Start the project-local Ollama service on loopback.
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$ollamaExe = Join-Path $projectRoot 'tools\ollama\runtime\ollama.exe'
$modelDir = Join-Path $projectRoot 'tools\ollama\models'
if (-not (Test-Path -LiteralPath $ollamaExe)) { throw "Ollama executable not found: $ollamaExe" }
New-Item -ItemType Directory -Force -Path $modelDir | Out-Null
try {
  $existing = Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/tags' -TimeoutSec 2
  Write-Output "Ollama already running. Models: $($existing.models.name -join ', ')"
  exit 0
} catch { }
$env:OLLAMA_MODELS = $modelDir
$env:OLLAMA_HOST = '127.0.0.1:11434'
$process = Start-Process -FilePath $ollamaExe -ArgumentList 'serve' -WorkingDirectory (Split-Path -Parent $ollamaExe) -WindowStyle Hidden -PassThru
for ($attempt = 0; $attempt -lt 12; $attempt++) {
  Start-Sleep -Milliseconds 500
  try {
    $status = Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/tags' -TimeoutSec 2
    Write-Output "Ollama running on 127.0.0.1:11434 (PID $($process.Id)). Models: $($status.models.name -join ', ')"
    exit 0
  } catch { }
}
throw "Ollama did not start. Process ID: $($process.Id)"
