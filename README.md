# Ruizhang Zhou — Personal Site

This repository contains my portfolio and CV source files. The site focuses on applied AI and AI platform engineering: production LLM systems, backend and infrastructure work, and ML engineering.

## Site structure

- `index.html`: introduction and selected work, including KI:connect, [TalkEcho](https://github.com/RuizhangZhou/talkecho), [LLM Gateway](https://github.com/RuizhangZhou/llm-gateway), and my master's thesis.
- `ml-ai-engineer.html`: AI platform work, operations, and related projects; smaller API experiments such as [CompatBench](https://github.com/RuizhangZhou/CompatBench) are linked as supplementary work.
- `fullstack-engineer.html`, `data-engineer.html`, `ml-research.html`: supporting experience.
- `blog.html`: GitHub Issues-backed blog with title/date search and pagination.
- `resume/cv_en.typ` and `resume/cv_de.typ`: English and German CV sources.

## Build and publish

The GitHub Actions workflow in `.github/workflows/build.yml` compiles the Typst sources into `Resume_EN.pdf` and `Lebenslauf_DE.pdf`, then publishes the site through GitHub Pages. The PDFs are generated during the build and are not stored in this repository.

To check the CVs locally with Typst installed:

```sh
typst compile resume/cv_en.typ Resume_EN.pdf
typst compile resume/cv_de.typ Lebenslauf_DE.pdf
```

The HTML pages can be opened locally in a browser. Keep claims about work outcomes and publications tied to evidence that can be shared publicly.
