$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
uv sync --group dev
uv run pyinstaller build.spec --noconfirm --clean
Copy-Item "$root\dist\plugin.exe" "$root\com.tmbk.streamdock.autocad.sdPlugin\plugin.exe" -Force
Write-Host "plugin.exe copied into the .sdPlugin folder"
