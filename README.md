# Resume + Personal Site (Starter)

This repo contains:

- `resume/` — Typst sources for **English** and **German** CVs.
- `index.html` — a minimal homepage linking to the generated PDFs.
- GitHub Actions workflow to compile PDFs and publish everything to **GitHub Pages**.

## How to use

1. Ensure your repository is named `<username>.github.io` (for me: `RuizhangZhou.github.io`) and **Pages** is enabled with **GitHub Actions** as the build source.
2. Commit these files and push to `main` (or `master`).
3. The workflow will install Typst, compile `resume/cv_en.typ` → `Resume_EN.pdf` and `resume/cv_de.typ` → `Lebenslauf_DE.pdf`, and publish the whole repo as a site.
4. Edit the Typst files any time; pushing updates will rebuild PDFs automatically.

## Where to edit

- `resume/cv_en.typ` and `resume/cv_de.typ`: core content.
- `resume/theme.typ`: small style helpers.
- `index.html`: homepage text and links.

## Tips

- Prefer concise bullet points with **action → impact**.
- Keep each CV **1 page** if possible.
- For a GUI builder alternative, try **Reactive Resume** or **FlowCV** and then drop exported PDFs into the repo.

## New Feature: Automated Referral Engine

This repository now includes a simple automated referral engine implementation to demonstrate the principle described in GitHub Issue #162: *Why a Single Automated Referral Engine Outperforms Adding Ten New Products*.

### Location

- `referral_engine/engine.py`: Core referral engine logic.
- `referral_engine/test_engine.py`: Unit tests for the referral engine.

### Usage

The referral engine tracks users, their referrals, and rewards referrers with a fixed credit amount when referees convert (e.g., make their first paid month).

Example usage:

```python
from referral_engine.engine import ReferralEngine

engine = ReferralEngine()
engine.add_referral("user1", "user2")
engine.record_conversion("user2")
print(engine.get_rewards("user1"))  # Outputs: 10
```

### Running Tests

Run the tests with:

```bash
python3 -m unittest referral_engine/test_engine.py
```

This feature illustrates the leverage and efficiency of a single automated referral engine compared to managing multiple products.
