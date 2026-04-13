from __future__ import annotations

from pathlib import Path
import json
import shutil
import subprocess


def main() -> None:
    manifest = json.loads(Path("data/cn_major_cities.json").read_text(encoding="utf-8"))
    output_dir = Path("offline-seed/cn-major-v1")
    output_dir.mkdir(parents=True, exist_ok=True)

    for tier_name in ("base_tier", "mega_city_tier"):
        dist = manifest[tier_name]["dist"]
        for city in manifest[tier_name]["cities"]:
            subprocess.run(
                [
                    "python3",
                    "create_map_poster.py",
                    "--city",
                    city,
                    "--country",
                    "China",
                    "--distance",
                    str(dist),
                    "--theme",
                    "terracotta",
                ],
                check=True,
            )

    for file_path in Path("cache").glob("*"):
        if file_path.is_file():
            shutil.copy2(file_path, output_dir / file_path.name)


if __name__ == "__main__":
    main()
