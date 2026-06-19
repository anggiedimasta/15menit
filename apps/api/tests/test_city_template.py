import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_city_template_generates_manifest() -> None:
    result = subprocess.run(
        ["bun", "scripts/add-city.ts", "cities/bandung.yaml"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    manifest = ROOT / "data" / "cities" / "bandung" / "manifest.json"
    assert manifest.exists()
    assert '"city": "bandung"' in manifest.read_text(encoding="utf-8")
