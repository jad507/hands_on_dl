# The controlled chunk-framing experiment.
#
# Runs phase 1 over the same small corpus five times, changing nothing but where
# the batch boundaries fall. See chunk_experiment.py for the design and for what
# each condition is and is not evidence of.
#
#   A   size 3, offset 0    baseline, the corpus setting
#   A2  size 3, offset 0    the SAME setting again -- the control. Measures
#                           run-to-run non-determinism on this machine, in this
#                           session, with this model file, which is the honest
#                           floor for the effect below.
#   B   size 3, offset 1    every boundary after the first moves; blocks untouched
#   C   size 1              no batch context at all
#   D   size 5              more context
#
# Each condition writes to its own output root, so nothing in downloads/llm_outputs
# is touched. Verify with `git status downloads/llm_outputs` afterwards.
#
# Resumable: the pipeline's per-meeting SKIP logic means re-invoking after an
# interruption picks up where it stopped. To force a condition to re-run, delete
# its directory under downloads\chunk_experiment\runs.
#
# Usage:
#   python chunk_experiment.py select --n 12     # build the corpus first
#   .\run_chunk_experiment.ps1
#   .\run_chunk_experiment.ps1 -Model ministral-8b -Conditions A,A2,B
#   python chunk_experiment.py analyse

param(
    [string]$Model = "gemma-4-4b",
    [string]$Conditions = "A,A2,B,C,D"
)

$ErrorActionPreference = "Continue"
$env:PYTHONUNBUFFERED = "1"
$env:PYTHONUTF8 = "1"

$venv = if ($env:HODL_VENV) { $env:HODL_VENV }
        else { Join-Path (Split-Path $PSScriptRoot -Parent) "LancasterClaude\.venv" }
$activate = Join-Path $venv "Scripts\Activate.ps1"
if (Test-Path $activate) { & $activate }
else { Write-Warning "No venv at $activate - using whatever python is on PATH." }

& (Join-Path $PSScriptRoot "load_env.ps1")

$root    = Join-Path $PSScriptRoot "downloads\chunk_experiment"
$corpus  = Join-Path $root "corpus"
$runs    = Join-Path $root "runs"
$logDir  = Join-Path $PSScriptRoot "logs"
New-Item -ItemType Directory -Force -Path $runs, $logDir | Out-Null

if (-not (Test-Path $corpus)) {
    Write-Error "No scratch corpus at $corpus. Run: python chunk_experiment.py select --n 12"
    exit 1
}
$nMeetings = (Get-ChildItem -Path $corpus -Filter *.json | Measure-Object).Count
if ($nMeetings -eq 0) {
    Write-Error "Scratch corpus at $corpus is empty."
    exit 1
}

# The corpus is fixed for every condition; only the chunking changes.
$env:HODL_COMMENTS_DIR = $corpus

$spec = @{
    "A"  = @{ Name = "A_size3_off0";         Size = 3; Offset = 0 }
    "A2" = @{ Name = "A2_size3_off0_repeat"; Size = 3; Offset = 0 }
    "B"  = @{ Name = "B_size3_off1";         Size = 3; Offset = 1 }
    "C"  = @{ Name = "C_size1";              Size = 1; Offset = 0 }
    "D"  = @{ Name = "D_size5";              Size = 5; Offset = 0 }
}

$want = $Conditions -split "," | ForEach-Object { $_.Trim() }
$results = [System.Collections.Generic.List[PSCustomObject]]::new()

Write-Host "=== controlled chunk-framing experiment ==="
Write-Host "  model      $Model"
Write-Host "  corpus     $corpus  ($nMeetings meetings)"
Write-Host "  conditions $($want -join ', ')"
Write-Host "  started    $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

foreach ($key in $want) {
    if (-not $spec.ContainsKey($key)) {
        Write-Warning "unknown condition '$key' - skipping"
        continue
    }
    $c    = $spec[$key]
    $name = $c.Name
    $env:HODL_OUTPUTS_ROOT = Join-Path $runs $name
    New-Item -ItemType Directory -Force -Path $env:HODL_OUTPUTS_ROOT | Out-Null

    $log   = Join-Path $logDir "chunk_exp_${name}_${Model}.log"
    $start = Get-Date
    Write-Host ""
    Write-Host "=== $name  (chunk-size $($c.Size), offset $($c.Offset))  started $($start.ToString('HH:mm:ss')) ==="

    cmd /c "python llm_classify_human_themes.py --model $Model --phase 1 --chunk-size $($c.Size) --chunk-offset $($c.Offset) 2>&1" |
        Tee-Object -FilePath $log

    $exit    = $LASTEXITCODE
    $elapsed = (Get-Date) - $start
    $dur     = "{0:hh\:mm\:ss}" -f $elapsed
    if ($exit -ne 0) { Write-Host "WARNING: $name exited $exit after $dur -- continuing" }
    else             { Write-Host "=== $name done in $dur ===" }

    $results.Add([PSCustomObject]@{
        Condition = $name
        ChunkSize = $c.Size
        Offset    = $c.Offset
        Status    = $(if ($exit -eq 0) { "ok" } else { "exit $exit" })
        Elapsed   = $dur
    })
}

Write-Host ""
Write-Host "=== Summary  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ==="
$results | Format-Table -AutoSize
Write-Host "Next: python chunk_experiment.py analyse"
