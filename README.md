# Ruizhang Zhou — Resume + Personal Site (Starter)

This repo contains:

- `resume/` — Typst sources for **English** and **German** CVs.
- `index.html` — a minimal homepage linking to the generated PDFs.
- GitHub Actions workflow to compile PDFs and publish everything to **GitHub Pages**.

## How to use

1. Ensure your repository is named `<username>.github.io` (for you: `RuizhangZhou.github.io`) and **Pages** is enabled with **GitHub Actions** as the build source.
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
