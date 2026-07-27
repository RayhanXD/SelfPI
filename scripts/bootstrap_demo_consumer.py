"""Recreate the local demo-consumer app (gitignored; not part of SelfPI commits)."""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "demo-consumer"

BILLING = '''"""Tiny Stripe-using Python app — SelfPI local demo consumer (gitignored from SelfPI)."""

from __future__ import annotations

import stripe

# True call sites — SelfPI demo bump renames source → payment_method
charge = stripe.Charge.create(source="tok_123")


def charge_customer(customer_card: str) -> object:
    return stripe.Charge.create(source=customer_card)


# False positive trap — in a comment, should not score as a real site
# stripe.Charge.create(source="tok_comment")


def main() -> None:
    print("selfpi-demo-consumer — sample Stripe Charge.create call sites")
    print("Run SelfPI Bump spec → Open PR to rewrite source= → payment_method=")


if __name__ == "__main__":
    main()
'''

README = """# selfpi-demo-consumer

Local throwaway Stripe consumer used by SelfPI end-to-end demos.

- Scanned via `REPO_PATH` / watched API `repo_path`
- PRs open against `RayhanXD/selfpi-demo-consumer` on GitHub
- **Not** part of the SelfPI monorepo — parent `.gitignore` excludes this directory

```bash
# Create empty repo on GitHub, install the SelfPI App on it, then:
git remote add origin https://github.com/RayhanXD/selfpi-demo-consumer.git
git push -u origin main
```
"""


def bootstrap(*, force: bool = False) -> Path:
    if DEST.exists() and any(DEST.iterdir()) and not force:
        print(f"Already exists: {DEST} (pass --force to recreate files)")
        return DEST

    DEST.mkdir(parents=True, exist_ok=True)
    (DEST / "billing.py").write_text(BILLING)
    (DEST / "requirements.txt").write_text("stripe>=8.0.0\n")
    (DEST / "README.md").write_text(README)
    (DEST / ".gitignore").write_text(".venv/\n__pycache__/\n*.pyc\n.env\n.DS_Store\n")

    git_dir = DEST / ".git"
    if not git_dir.exists():
        subprocess.run(["git", "init", "-b", "main"], cwd=DEST, check=True)
        subprocess.run(["git", "add", "."], cwd=DEST, check=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial selfpi-demo-consumer with Stripe call sites"],
            cwd=DEST,
            check=True,
        )
        subprocess.run(
            [
                "git",
                "remote",
                "add",
                "origin",
                "https://github.com/RayhanXD/selfpi-demo-consumer.git",
            ],
            cwd=DEST,
            check=False,
        )
    print(f"Ready: {DEST}")
    return DEST


def main() -> None:
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--force", action="store_true")
    args = p.parse_args()
    bootstrap(force=args.force)


if __name__ == "__main__":
    main()
