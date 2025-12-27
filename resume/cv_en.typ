#import "theme.typ": *

#header(
  "Ruizhang Zhou",
  "AI/ML Engineer & Full-stack Developer - Production LLM systems, Deep Learning research, Data pipelines, Multi-tenant platforms",
  [#link("mailto:ruizhang.zhou@mail.com")[ruizhang.zhou\@mail.com] | #link("https://github.com/RuizhangZhou")[GitHub] | #link("https://linkedin.com/in/ruizhang-zhou/")[LinkedIn] | #link("https://ruizhangzhou.github.io")[Website]]
)

#section-title("Experience")
#role("Software Engineer (AI Platform)", "KIconnect — RWTH IT Center", "09/2024–Present")

- Built a production multi‑tenant AI platform (ASP.NET Core + Vue 3) with real‑time LLM streaming, admin controls, and enterprise SSO.
- Implemented unified tokenization and cost accounting (text + vision) across model families, enabling per‑tenant quotas and heatmap reporting.
- Secured sensitive data with MongoDB CSFLE and tenant/role guardrails; integrated moderation and image handling.
- Improved operability and resilience with SignalR streaming, Hangfire jobs, and Polly retries on Nomad/Traefik.
- Tech: C#/.NET, Vue 3, MongoDB, Semantic Kernel, Azure/OpenAI

#section-title("Education")
*M.Sc. Computer Science* | RWTH Aachen University | Oct. 2022 - Jun. 2024
- Master's Thesis: #link("https://github.com/RuizhangZhou/ScenarioGenerationAI")[AI-Based Generation of Testing Scenarios for Motion Planners on Connected and Automated Vehicles]
- Focus on AI/ML: Deep Learning, NLP, Large Language Models, Knowledge Representation

*B.Sc. Computer Science* | RWTH Aachen University | Oct. 2019 - Sep. 2022

*B.A. German Language and Literature* | Tongji University | Sep. 2014 - Aug. 2018

#section-title("Previous Roles")
#role("Research Assistant — Chair of Embedded Software", "RWTH Aachen University", "08/2023–03/2024")
- Enhanced remote lab web app with real‑time visualizations and CI/CD automation.
- Tech: TypeScript, Angular, Docker, GitLab

#role("Research Assistant — Chair of DBIS", "RWTH Aachen University", "07/2023–03/2024")
- Deployed LLaMA on GPU cluster, exposed via FastAPI; built end‑to‑end LLM chat platform for internal research.
- Tech: Python, PyTorch, Ollama, vLLM, FastAPI

#section-title("Tech Stack")
C\# / .NET 9, ASP.NET Core, MongoDB (CSFLE), Semantic Kernel, Azure AI Inference, OpenAI .NET, Microsoft.ML.Tokenizers, pythonnet, SkiaSharp, Hangfire, SignalR, Vue 3, Inertia.js, Vite, NLog, Traefik, Nomad, KernelMemory.
