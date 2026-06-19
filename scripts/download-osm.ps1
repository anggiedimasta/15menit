$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$OutDir = Join-Path $Root "data\osm"
$File = Join-Path $OutDir "java-latest.osm.pbf"
$Url = "https://download.geofabrik.de/asia/indonesia/java-latest.osm.pbf"

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

if (Test-Path $File) {
    $sizeMb = [math]::Round((Get-Item $File).Length / 1MB, 1)
    Write-Host "Existing file: $File (${sizeMb} MB)"
    Write-Host "Delete file to force re-download"
    exit 0
}

Write-Host "Downloading $Url ..."
Invoke-WebRequest -Uri $Url -OutFile $File -UseBasicParsing
$sizeMb = [math]::Round((Get-Item $File).Length / 1MB, 1)
Write-Host "Saved ${sizeMb} MB at $(Get-Date -Format o)"
