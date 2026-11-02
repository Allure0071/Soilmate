"""Copy bundled synthetic SQLite fixtures into data/ without replacing local databases."""
from pathlib import Path
from shutil import copy2

root = Path(__file__).resolve().parents[1]
destination = root / "data"
destination.mkdir(exist_ok=True)
for name in ("soil.sqlite", "soil_1km.sqlite"):
    source = root / "sample-data" / name
    target = destination / name
    if target.exists():
        print(f"Kept existing {target}")
    else:
        copy2(source, target)
        print(f"Installed synthetic sample {target}")
