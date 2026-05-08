# Load environment variables from personal.env
$envFile = Join-Path $PSScriptRoot "personal.env"
Get-Content $envFile | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]*)\s*=\s*(.*)\s*$') {
        [System.Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), 'Process')
    }
}

Write-Host "Loaded: ANTHROPIC_API_KEY, ANTHROPIC_MODEL=$env:ANTHROPIC_MODEL"
