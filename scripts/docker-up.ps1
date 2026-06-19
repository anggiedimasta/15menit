# Start 15menit Docker services (PostGIS + optional Valhalla).
# Usage:
#   .\scripts\docker-up.ps1              # PostGIS only
#   .\scripts\docker-up.ps1 -Routing     # PostGIS + Valhalla (first build ~30-60 min)

param(
    [switch]$Routing
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

Write-Host "Starting PostGIS (db)..."
docker compose up -d db

Write-Host "Waiting for PostGIS to accept connections..."
$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    docker compose exec -T db pg_isready -U fifteenmenit -d fifteenmenit 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $ready = $true
        break
    }
    Start-Sleep -Seconds 2
}
if (-not $ready) {
    Write-Error "PostGIS did not become ready within 60s. Check: docker compose logs db"
}

Write-Host "Applying alembic migrations..."
Push-Location apps\api
try {
    alembic upgrade head
} finally {
    Pop-Location
}

if ($Routing) {
    New-Item -ItemType Directory -Force -Path (Join-Path $Root "data\valhalla") | Out-Null
    Write-Host "Starting Valhalla (profile routing)..."
    Write-Host "First run downloads Java OSM and builds tiles - expect 30-60 min."
    docker compose --profile routing up -d valhalla
}

Write-Host ""
docker compose ps
if ($Routing) {
    Write-Host ""
    Write-Host "Valhalla status: curl http://localhost:8002/status"
    Write-Host "When ready, set ROUTING_MODE=auto (or valhalla) in .env"
}
