# Re-run one model's phase 1 over the whole corpus into a scratch output root,
# so the result can be diffed against the committed corpus without touching it.
#
# Why this exists: plans/windows_environment_upgrade_status.md section 3 found that
# re-running gemma-4-4b on one meeting today produces four public comments where the
# committed corpus (June 2026) has five. One meeting, one model is an anecdote. This
# script turns it into a number by re-running every meeting, and compare_corpus_runs.py
# reports the delta.
#
# The scratch root is redirected with HODL_OUTPUTS_ROOT, so downloads/llm_outputs is
# never opened for writing. Verify with `git status downloads/` afterwards.
#
# Usage:
#   .\run_repro_check.ps1                      # gemma-4-4b, phase 1, all meetings
#   .\run_repro_check.ps1 -Model ministral-8b
#   .\run_repro_check.ps1 -Limit 20            # smaller first pass
#
# Resumable: the pipeline's own per-meeting SKIP logic means re-invoking after an
# interruption picks up where it stopped.

param(
    [string]$Model = "gemma-4-4b",
    [int]$Limit = 0,
    [string]$Tag = ""
)

$ErrorActionPreference = "Continue"
$env:PYTHONUNBUFFERED = "1"
$env:PYTHONUTF8 = "1"

$venv = if ($env:HODL_VENV) { $env:HODL_VENV }
        else { Join-Path (Split-Path $PSScriptRoot -Parent) "LancasterClaude\.venv" }
$activate = Join-Path $venv "Scripts\Activate.ps1"
if (Test-Path $activate) {
    & $activate
} else {
    Write-Warning "No venv at $activate - using whatever python is on PATH. Set HODL_VENV to override."
}

& (Join-Path $PSScriptRoot "load_env.ps1")

if (-not $Tag) { $Tag = Get-Date -Format "yyyy-MM-dd" }
$scratch = Join-Path $PSScriptRoot "downloads\repro_check\$Tag"
$env:HODL_OUTPUTS_ROOT = $scratch
New-Item -ItemType Directory -Force -Path $scratch | Out-Null

$logDir = Join-Path $PSScriptRoot "logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log = Join-Path $logDir "repro_check_${Model}_${Tag}.log"

Write-Host "=== reproducibility check ==="
Write-Host "  model        $Model"
Write-Host "  scratch root $scratch"
Write-Host "  log          $log"
Write-Host "  started      $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host ""

$limitArg = if ($Limit -gt 0) { "--limit $Limit" } else { "" }
cmd /c "python llm_classify_human_themes.py --model $Model --phase 1 $limitArg 2>&1" |
    Tee-Object -FilePath $log

Write-Host ""
Write-Host "=== finished $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ==="
Write-Host "Next: python compare_corpus_runs.py --rerun `"$scratch\$Model\phase1_public_comments`" --model $Model"
