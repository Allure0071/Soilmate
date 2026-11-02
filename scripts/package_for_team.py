"""Create a small source archive with synthetic map fixtures, without local data."""
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


root = Path(__file__).resolve().parents[1]
target = root / "releases" / "soil-frontend-team-source.zip"
target.parent.mkdir(exist_ok=True)
excluded_dirs = {"node_modules", "dist", ".npm-cache", "audit", "__pycache__", ".venv", "tiles"}
sources = [root / name for name in (".gitignore", "AGENTS.md", "README.md", "团队接收说明.md", "vite.config.js")]
for directory in (".agents", "backend", "frontend", "scripts", "sample-data", "product"):
    sources.extend(p for p in (root / directory).rglob("*")
                   if p.is_file() and not set(p.relative_to(root).parts).intersection(excluded_dirs)
                   and not p.name.startswith(".env")
                   and (directory == "sample-data" or p.suffix not in
                        {".pyc", ".log", ".sqlite", ".sqlite3", ".db", ".pem", ".key", ".pfx"}))
with ZipFile(target, "w", ZIP_DEFLATED) as archive:
    for path in sorted(sources):
        archive.write(path, path.relative_to(root).as_posix())
print(f"Created {target} with {len(sources)} files ({target.stat().st_size} bytes)")
