$ErrorActionPreference = "Stop"
$parts = Get-ChildItem "$PSScriptRoot\payload\part_*.txt" | Sort-Object Name
if (-not $parts) { throw "payload part files not found" }
$b64 = (($parts | ForEach-Object { Get-Content $_.FullName -Raw }) -join '') -replace '\s',''
$zip = Join-Path $PSScriptRoot "txtrpg_v19_github.zip"
[IO.File]::WriteAllBytes($zip, [Convert]::FromBase64String($b64))
$actual=(Get-FileHash $zip -Algorithm SHA256).Hash.ToLower()
$expected="b38098677bb22d509393600f3dbc72e29c60ff56658fefb24c800a93d4472759"
if ($actual -ne $expected) { throw "SHA256 mismatch: $actual" }
$dest=Join-Path $PSScriptRoot "game"
if (Test-Path $dest) { Remove-Item $dest -Recurse -Force }
Expand-Archive -LiteralPath $zip -DestinationPath $dest -Force
Write-Host "Restored successfully: $actual"
$launcher=Join-Path $dest "txtrpg_project\START_GAME.bat"
if (-not (Test-Path $launcher)) { throw "START_GAME.bat not found" }
Start-Process -FilePath $launcher -WorkingDirectory (Split-Path $launcher)
