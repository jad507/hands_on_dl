Get-Content .env | Where-Object {
    $_ -and $_ -notmatch '^\s*#'
} | ForEach-Object {
    $name, $value = $_ -split '=', 2
    Set-Item -Path "Env:$name" -Value $value
}