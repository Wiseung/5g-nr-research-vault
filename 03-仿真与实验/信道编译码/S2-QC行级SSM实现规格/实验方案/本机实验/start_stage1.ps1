param([int]$Batch = 64, [int]$DiagnosticFrames = 256)
$ErrorActionPreference = 'Stop'
$experimentRoot = $PSScriptRoot
$pythonPath = Join-Path $experimentRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw 'Missing local .venv. See README.md for environment setup.'
}
$runName = [TimeZoneInfo]::ConvertTimeBySystemTimeZoneId([DateTime]::UtcNow, 'China Standard Time').ToString('yyyyMMdd-HHmmss') + '-stage1'
$runPath = Join-Path $experimentRoot ('results/' + $runName)
New-Item -ItemType Directory -Path $runPath | Out-Null
$launchArgs = @('-B', '-u', 'run_local.py', '--mode', 'stage1', '--output', ('results/' + $runName), '--batch', $Batch, '--diagnostic-frames', $DiagnosticFrames)
$experimentProcess = Start-Process -FilePath $pythonPath -ArgumentList $launchArgs -WorkingDirectory $experimentRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $runPath 'stdout.log') -RedirectStandardError (Join-Path $runPath 'stderr.log')
$launch = @{pid=$experimentProcess.Id; run_id=$runName; output=$runPath; arguments=$launchArgs; stage='chain_validation_only'}
$launch | ConvertTo-Json -Depth 4 | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $runPath 'launch.json')
$launch | ConvertTo-Json -Depth 4
