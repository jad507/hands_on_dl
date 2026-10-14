$env:PYTHONUNBUFFERED = "1"
$env:PYTHONUTF8 = "1"

# Virtualenv location is machine-specific. Override with HODL_VENV if yours differs.
$venv = if ($env:HODL_VENV) { $env:HODL_VENV }
        else { Join-Path (Split-Path $PSScriptRoot -Parent) "LancasterClaude\.venv" }
$activate = Join-Path $venv "Scripts\Activate.ps1"
if (Test-Path $activate) {
    & $activate
} else {
    Write-Warning "No venv at $activate - using whatever python is on PATH. Set HODL_VENV to override."
}

# Loads HODL_MODELS_ROOT and friends; the Python scripts need it to find weights.
& (Join-Path $PSScriptRoot "load_env.ps1")

$results = [System.Collections.Generic.List[PSCustomObject]]::new()

function Run-Model($name) {
    $log   = "logs\llm_classify_$name.log"
    $start = Get-Date
    Write-Host ""
    Write-Host "=== $name  started $($start.ToString('yyyy-MM-dd HH:mm:ss')) ==="
    cmd /c "python llm_classify_human_themes.py --model $name 2>&1" | Tee-Object -FilePath $log
    $exit    = $LASTEXITCODE
    $elapsed = (Get-Date) - $start
    $dur     = "{0:hh\:mm\:ss}" -f $elapsed
    if ($exit -ne 0) {
        Write-Host "WARNING: $name exited with code $exit after $dur -- continuing"
    } else {
        Write-Host "=== $name done in $dur ==="
    }
    $script:results.Add([PSCustomObject]@{
        Model   = $name
        Status  = $(if ($exit -eq 0) { "ok" } else { "exit $exit" })
        Elapsed = $dur
    })
}

# --- llama_cpp models, comfortably within A2000 12 GB ---
# Run-Model "qwen3.5-9b-q4"
# Run-Model "qwen3.5-9b-q5"
# Run-Model "qwen3.5-9b-q6"
# Run-Model "deepseek-r1-7b"
# Run-Model "gemma-4-4b"
# Run-Model "ministral-8b"

# --- llama_cpp models, tight on A2000 12 GB -- may OOM at init ---
Run-Model "qwen3.5-9b-q8"     # ~11.2 GB estimated
Run-Model "phi-4"              # ~11.0 GB estimated
Run-Model "deepseek-r1-14b"      # ~11.6 GB estimated -- most likely to fail

# --- too large for A2000 12 GB (remote 80 GB card) ---
# Run-Model "llama-4-scout"      # ~59 GB weights

# --- non-llama_cpp backends (require transformers / TensorRT-LLM) ---
# Run-Model "gemma-4-31b"        # transformers, remote 80 GB card
# Run-Model "llama-3.1-nvfp4"   # TensorRT-LLM / vLLM with NVFP4
# Run-Model "ministral-8b-hf"   # transformers

Write-Host ""
Write-Host "=== Summary  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ==="
$results | Format-Table -AutoSize
