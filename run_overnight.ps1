python audio_pipeline/diarize.py 2>&1 | tee logs/diarize.log
if ($LASTEXITCODE -eq 0) {
    python audio_pipeline/transcribe.py 2>&1 | tee logs/transcribe.log
} else {
    Write-Host "diarize.py failed (exit $LASTEXITCODE) - transcribe.py not started"
}
