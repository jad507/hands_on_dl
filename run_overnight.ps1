$env:PYTHONUNBUFFERED = "1"
$env:PYTHONUTF8 = "1"

# Activate the LancasterClaude venv
& "D:\Users\jad507\PycharmProjects\LancasterClaude\.venv\Scripts\Activate.ps1"

# Ensure Deno is on PATH (needed by yt-dlp for YouTube JS extraction)
$denoDir = "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\DenoLand.Deno_Microsoft.Winget.Source_8wekyb3d8bbwe"
if (Test-Path $denoDir) {
    $env:PATH = "$denoDir;$env:PATH"
    Write-Host "Deno: $((& "$denoDir\deno.exe" --version 2>&1)[0])"
} else {
    Write-Host "WARNING: Deno not found at expected path - yt-dlp may hit bot detection"
}

python download_playlist.py 2>&1 | tee logs/download.log
if ($LASTEXITCODE -ne 0) {
    Write-Host "download_playlist.py failed (exit $LASTEXITCODE) - stopping"
    exit 1
}

python audio_pipeline/diarize.py 2>&1 | tee logs/diarize.log
if ($LASTEXITCODE -ne 0) {
    Write-Host "diarize.py failed (exit $LASTEXITCODE) - stopping"
    exit 1
}

python audio_pipeline/transcribe.py 2>&1 | tee logs/transcribe.log
if ($LASTEXITCODE -ne 0) {
    Write-Host "transcribe.py failed (exit $LASTEXITCODE) - stopping"
    exit 1
}

python audio_pipeline/align.py 2>&1 | tee logs/align.log
if ($LASTEXITCODE -ne 0) {
    Write-Host "align.py failed (exit $LASTEXITCODE) - stopping"
    exit 1
}

python audio_pipeline/group_speakers.py 2>&1 | tee logs/group_speakers.log
if ($LASTEXITCODE -ne 0) {
    Write-Host "group_speakers.py failed (exit $LASTEXITCODE) - stopping"
    exit 1
}

Write-Host "All steps complete."