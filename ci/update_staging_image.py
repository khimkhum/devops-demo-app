"""Update only the staging digest in this lab's Kustomize manifest."""

import argparse
from pathlib import Path
import re


def update_staging_image(root: Path, repository: str, digest: str) -> bool:
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
        raise ValueError("Expected a lowercase sha256 image digest")
    target = root / "overlays/staging/kustomization.yaml"
    text = target.read_text(encoding="utf-8")
    pattern = re.compile(
        r"(?m)^(  - name: " + re.escape(repository)
        + r"\n    digest: )(sha256:[0-9a-f]{64})$"
    )
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise ValueError("Expected exactly one matching staging image entry")
    if matches[0].group(2) == digest:
        return False
    updated = pattern.sub(lambda match: match.group(1) + digest, text)
    target.write_text(updated, encoding="utf-8")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("gitops_root", type=Path)
    parser.add_argument("repository")
    parser.add_argument("digest")
    args = parser.parse_args()
    try:
        changed = update_staging_image(args.gitops_root, args.repository, args.digest)
    except (ValueError, OSError) as error:
        parser.exit(1, f"Cannot update staging image: {error}\n")
    print("Staging digest updated." if changed else "Staging digest already matches.")


if __name__ == "__main__":
    main()
