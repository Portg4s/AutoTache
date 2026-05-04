param(
    [switch]$NoVenv
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..")
$LogsDir = Join-Path $ProjectRoot "logs"
$Timestamp = Get-Date -Format "yyyy-MM-dd_HHmm"
$LogPath = Join-Path $LogsDir "autotache_$Timestamp.log"

New-Item -ItemType Directory -Path $LogsDir -Force | Out-Null
Set-Location $ProjectRoot

$PythonExecutable = "python"
if (-not $NoVenv) {
    $VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
    $VenvScripts = Join-Path $ProjectRoot ".venv\Scripts"
    if (Test-Path $VenvPython) {
        $env:VIRTUAL_ENV = Join-Path $ProjectRoot ".venv"
        $env:PATH = "$VenvScripts;$env:PATH"
        $PythonExecutable = $VenvPython
    }
}

"AutoTache start: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Out-File -FilePath $LogPath -Encoding utf8
"Project root: $ProjectRoot" | Out-File -FilePath $LogPath -Encoding utf8 -Append
"& $PythonExecutable -m autotache_jobs --debug" | Out-File -FilePath $LogPath -Encoding utf8 -Append
"" | Out-File -FilePath $LogPath -Encoding utf8 -Append

& $PythonExecutable -m autotache_jobs --debug *>&1 | Out-File -FilePath $LogPath -Encoding utf8 -Append
$ExitCode = $LASTEXITCODE

"" | Out-File -FilePath $LogPath -Encoding utf8 -Append
"AutoTache end: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Out-File -FilePath $LogPath -Encoding utf8 -Append
"Exit code: $ExitCode" | Out-File -FilePath $LogPath -Encoding utf8 -Append

Write-Host "AutoTache termine. Log: $LogPath"
exit $ExitCode
