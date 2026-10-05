$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$pluginName = "com.tmbk.streamdock.autocad.sdPlugin"
$source = Join-Path $root $pluginName
$target = Join-Path $env:APPDATA "HotSpot\StreamDock\plugins\$pluginName"

if (-not (Test-Path (Join-Path $source "plugin.exe"))) {
    throw "plugin.exe missing: run scripts\build.ps1 first"
}

Get-Process -Name "StreamDock" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 1
if (Test-Path $target) { Remove-Item $target -Recurse -Force }
Copy-Item $source $target -Recurse -Force
Write-Host "Installed to $target"

$app = Get-ChildItem "$env:LOCALAPPDATA\Programs", "$env:ProgramFiles", "${env:ProgramFiles(x86)}" -Recurse -Filter "StreamDock.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($app) { Start-Process $app.FullName } else { Write-Host "Start Stream Dock manually" }
