
#import "theme.typ": *

#header(
  "Ruizhang Zhou",
  "Full‑stack AI Platform Engineer — Streaming • Token/Cost Governance • Compliance • Reliability",
  "Aachen · ruizhang.zhou@mail.com · github.com/RuizhangZhou · linkedin.com/in/ruizhang-zhou/"
)

#section-title("Summary")
Building a secure, multi‑tenant LLM assistant with streaming, cost/token tracking, document ingestion, and SSO. Emphasis on robust text/vision tokenization, admin UI, and operational reliability.

#section-title("Experience")
*Software Engineer (AI Platform), KIconnect – RWTH IT Center/PDSLLabs, Aachen* \
09/2024 – Present

- Chat pipeline (ASP.NET Core 9 + Semantic Kernel + Azure AI Inference/OpenAI): streaming responses, title generation, strict role alternation, content‑filter handling (reasoning/think tags).
- Tokenization & costing: unified token counting (OpenAI, Llama 3, Gemma 3, Mistral, Qwen, DeepSeek); Python.NET bridge; image tokenization for VLMs; detailed cost events incl. cached tokens; reporting with heatmaps/metrics.
- Admin UI (Vue 3 + Inertia): models/deployments, parameters (temperature/top‑p/penalties), reasoning effort (o1/o3‑mini), system prompts, quotas; soft‑delete/restore; auto‑deactivation on credential removal.
- Documents & context: upload/extraction via Microsoft KernelMemory; per‑deployment/model token guardrails; on‑demand inclusion of document text/images; daily cleanup with Hangfire.
- Security & compliance: Shibboleth SSO; MongoDB CSFLE (local master key) for API keys; EU data‑processing region; tenant/role checks.
- Realtime & resilience: SignalR broadcasting (live UI), resilient HTTP (Polly), NLog; DevOps context with Traefik/Nomad; embedded Python runtime setup.

#section-title("Education")
- RWTH Aachen University — M.Sc. Computer Science (GenAI, LLM), Grade 2.5 (2022.10–2024.06).
- RWTH Aachen University — B.Sc. Computer Science, Grade 2.2 (2019.10–2022.09).
- Tongji University — B.A. German Language & Literature (2014.09–2018.08).

#section-title("Selected previous roles")
- Research Assistant — RWTH Chair of Embedded Software (2023.08–2024.03): CPM Remote Web App maintenance; real‑time visualizations; CI/CD.
- Research Assistant — RWTH Chair of DBIS (2023.07–2024.03): LLM/GNN/Knowledge Graph research; GPU cluster experiments; LLaMA/Ollama chat platform.

#section-title("Tech Stack")
C#/.NET 9, ASP.NET Core, MongoDB (CSFLE), Semantic Kernel, Azure AI Inference, OpenAI .NET, Microsoft.ML.Tokenizers, pythonnet, SkiaSharp, Hangfire, SignalR, Vue 3, Inertia.js, Vite, NLog, Traefik, Nomad, KernelMemory.
