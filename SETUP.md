# Self-generating profile setup

## Local portrait regeneration

The committed `portrait.svg` is already generated from the supplied portrait.
To regenerate it, put the source image at `assets/portrait-source.jpg` and run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/generate_portrait.py
```

The portrait generator uses `rembg` when available and falls back to a lightweight
background-removal pass for the supplied gray-wall photograph. The ASCII stage is
fixed at 90 columns with bilateral filtering, CLAHE around 3.0, and the `(v/255)^1.7`
darkening curve.

## GitHub stats

No personal access token is required. GitHub Actions provides `GITHUB_TOKEN` to the
workflow. The stats job pins its contribution window to whole UTC days and queries
public repositories only.

Run **Actions → refresh stats → Run workflow** once after pushing. The scheduled job
then refreshes the generated SVGs every night and commits only when their bytes change.

## Manual profile settings

GitHub does not expose profile bio and pinned-repository configuration through the
workflow used here. Set those manually in the GitHub profile UI.
