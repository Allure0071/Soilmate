"""Install the supplied adapter into ignored local storage; never execute archive code."""
import argparse
import hashlib
import json
import shutil
import tarfile
import tempfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / 'backend/model_profiles/soilmate-qwen3-8b.json'

def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''): value.update(chunk)
    return value.hexdigest()

def install(archive, destination):
    profile = json.loads(PROFILE.read_text())
    destination = Path(destination).resolve()
    if destination.exists():
        if digest(destination / 'adapter/adapter_model.safetensors') == profile['adapter_sha256'] and digest(destination / 'adapter/adapter_config.json') == profile['adapter_config_sha256']:
            return destination
        raise ValueError('目标目录已存在且校验不匹配，未覆盖。')
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.soilmate-adapter-', dir=destination.parent))
    try:
        with tarfile.open(archive, 'r:gz') as bundle:
            total = 0
            for item in bundle.getmembers():
                path = PurePosixPath(item.name)
                if path.is_absolute() or '..' in path.parts or item.issym() or item.islnk(): raise ValueError('压缩包包含不安全路径或链接。')
                if item.isdir(): continue
                if not item.isfile(): raise ValueError('压缩包包含不支持的文件类型。')
                if item.name.startswith('runs/8b_sft/adapter_final/'):
                    relative = Path('adapter') / path.relative_to('runs/8b_sft/adapter_final')
                elif item.name.startswith('evaluation/'):
                    relative = Path(*path.parts)
                else: continue
                total += item.size
                if total > 600 * 1024 * 1024: raise ValueError('解压大小超过本模型包上限。')
                target = staging / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                with bundle.extractfile(item) as source, target.open('wb') as output: shutil.copyfileobj(source, output)
        if digest(staging/'adapter/adapter_model.safetensors') != profile['adapter_sha256'] or digest(staging/'adapter/adapter_config.json') != profile['adapter_config_sha256']:
            raise ValueError('适配器与已审核模型包校验值不一致。')
        (staging/'manifest.json').write_text(json.dumps(profile, ensure_ascii=False, indent=2)+'\n')
        staging.rename(destination)
        return destination
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('archive', type=Path)
    parser.add_argument('--destination', type=Path, default=ROOT/'data/models/soilmate-qwen3-8b')
    args = parser.parse_args()
    print(install(args.archive, args.destination))
