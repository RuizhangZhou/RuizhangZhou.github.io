#import "theme.typ": *

#header(
  "Ruizhang Zhou",
  "Full-stack AI Platform Engineer - Streaming chat / Token & cost governance / Multi-tenant security / SSO",
  [#link("mailto:ruizhang.zhou@mail.com")[ruizhang.zhou\@mail.com] | #link("https://github.com/RuizhangZhou")[GitHub] | #link("https://linkedin.com/in/ruizhang-zhou/")[LinkedIn] | #link("https://ruizhangzhou.github.io")[Website]]
)

#section-title("Experience")
*Software Engineer (AI Platform) - Full-time Position* | KIconnect - RWTH IT Center | 09/2024 - Present (14 months)

- *Chat Pipeline:* ASP.NET Core 9 + Semantic Kernel + Azure AI Inference/OpenAI; streaming responses, title generation, strict role alternation, content-filter handling.
- *Tokenization & Costing:* Unified token counting (OpenAI, Llama 3, Gemma 3, Mistral, Qwen, DeepSeek); Python.NET bridge; image tokenization for VLMs; detailed cost events incl. cached tokens; reporting with heatmaps.
- *Admin UI:* Vue 3 + Inertia; model/deployment management, parameter tuning, system prompts, quotas; soft-delete/restore; auto-deactivation.
- *Documents & Context:* Upload/extraction via KernelMemory; per-deployment/per-model token guardrails; on-demand inclusion; daily cleanup jobs (Hangfire).
- *Security & Compliance:* Shibboleth SSO; MongoDB CSFLE (local master key); EU data region; tenant/role checks.
- *Realtime & Resilience:* SignalR broadcasting (live UI), resilient HTTP (Polly), NLog; DevOps with Traefik/Nomad; embedded Python runtime.

#line(length: 100%, stroke: 0.5pt)

#section-title("Education")
*M.Sc. Computer Science* | RWTH Aachen University | Oct. 2022 - Jun. 2024 | Grade: 2.5
- Master's Thesis: #link("https://github.com/RuizhangZhou/ScenarioGenerationAI")[AI-Based Generation of Testing Scenarios for Motion Planners on Connected and Automated Vehicles]
- Focus on AI/ML: Deep Learning, NLP, Large Language Models, Knowledge Representation

*B.Sc. Computer Science* | RWTH Aachen University | Oct. 2019 - Sep. 2022 | Grade: 2.2

*B.A. German Language and Literature* | Tongji University | Sep. 2014 - Aug. 2018

#line(length: 100%, stroke: 0.5pt)

#section-title("Selected previous roles")
*Research Assistant (Part-time)* | RWTH Chair of Embedded Software | Aug. 2023 - Mar. 2024 (8 months)
- Maintained/enhanced CPM Remote Web Application for remote laboratory management
- Real-time data visualizations and monitoring dashboards using modern web frameworks
- Improved CI/CD pipelines for automated testing/deployment
- *Tech:* JavaScript/TypeScript, Web APIs, Docker, GitLab CI/CD

*Research Assistant (Part-time)* | RWTH Chair of DBIS | Jul. 2023 - Mar. 2024 (9 months)
- Research on LLM, GNN, and Knowledge Graph integration
- Experiments on GPU cluster infrastructure for model training/evaluation
- Developed/deployed LLaMA/Ollama-based chat platform for research purposes
- *Tech:* Python, PyTorch, Transformers, CUDA, Ollama, REST APIs

#line(length: 100%, stroke: 0.5pt)

#section-title("Tech Stack")
C\# / .NET 9, ASP.NET Core, MongoDB (CSFLE), Semantic Kernel, Azure AI Inference, OpenAI .NET, Microsoft.ML.Tokenizers, pythonnet, SkiaSharp, Hangfire, SignalR, Vue 3, Inertia.js, Vite, NLog, Traefik, Nomad, KernelMemory.

