# Load environment variables from .env into the current PowerShell process.
#
# Three sharp edges the previous version had, none of which announced themselves:
#   1. It did not strip surrounding quotes, so HF_TOKEN="hf_abc" became the
#      literal string "hf_abc" WITH quotes and HuggingFace returned 401 for a
#      token that looked correct in every printout.
#   2. It did not trim whitespace, so a trailing space became part of the value.
#   3. Start-Service ssh-agent needs Administrator and threw in a normal shell,
#      aborting the rest of the pipeline when $ErrorActionPreference is 'Stop'.

$envFile = Join-Path $PSScriptRoot ".env"

if (-not (Test-Path $envFile)) {
    Write-Warning "No .env found at $envFile. Copy .env.example to .env and fill it in."
    return
}

$loaded = @()

Get-Content $envFile | ForEach-Object {
    # key=value, ignoring blank lines and comments. Value may be empty.
    if ($_ -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$') {
        $name  = $matches[1].Trim()
        $value = $matches[2].Trim()

        # Strip one layer of matching surrounding quotes, if present.
        if ($value.Length -ge 2) {
            if (($value.StartsWith('"') -and $value.EndsWith('"')) -or
                ($value.StartsWith("'") -and $value.EndsWith("'"))) {
                $value = $value.Substring(1, $value.Length - 2)
            }
        }

        [System.Environment]::SetEnvironmentVariable($name, $value, 'Process')
        $loaded += $name
    }
}

Write-Host "Loaded $($loaded.Count) variable(s) from .env: $($loaded -join ', ')"

# HODL_MODELS_ROOT is required by every LLM script; fail loudly and early here
# rather than after a model load somewhere downstream.
if (-not $env:HODL_MODELS_ROOT) {
    Write-Warning "HODL_MODELS_ROOT is not set. LLM scripts will not find model weights. See .env.example."
} elseif (-not (Test-Path $env:HODL_MODELS_ROOT)) {
    Write-Warning "HODL_MODELS_ROOT points at a path that does not exist: $env:HODL_MODELS_ROOT"
}

# ssh-agent needs Administrator. Start it only if it is not already running, and
# never let a failure here abort the caller.
$svc = Get-Service ssh-agent -ErrorAction SilentlyContinue
if ($null -eq $svc) {
    Write-Host "ssh-agent service not present; skipping."
} elseif ($svc.Status -ne 'Running') {
    try {
        Start-Service ssh-agent -ErrorAction Stop
        Write-Host "Started ssh-agent."
    } catch {
        Write-Host "Could not start ssh-agent (needs Administrator); continuing."
    }
}
