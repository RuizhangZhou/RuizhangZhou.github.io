
#import "theme.typ": *

#header(
  "Ruizhang Zhou",
  "Full‑stack AI‑Plattform‑Ingenieur – Streaming • Token/Cost Governance • Compliance • Reliability",
  "Aachen · ruizhang.zhou@mail.com · github.com/RuizhangZhou · linkedin.com/in/ruizhang-zhou/"
)

#section-title("Kurzprofil")
Entwicklung eines sicheren, mandantenfähigen LLM‑Assistenzsystems mit Streaming, Kosten-/Token‑Tracking, Dokumenteinbindung und SSO. Fokus auf robuste Text/Vision‑Tokenisierung, Admin‑UI und Betriebszuverlässigkeit.

#section-title("Erfahrung")
*Software Engineer (AI Platform), KIconnect – RWTH IT Center/PDSLLabs, Aachen* \
09/2024 – heute

- Chat‑Pipeline (ASP.NET Core 9 + Semantic Kernel + Azure AI Inference/OpenAI): Streaming‑Antworten, Titelgenerierung, strikte Rollenfolge, Content‑Filter‑Handling (Reasoning/think‑Tags).
- Tokenisierung & Kosten: Einheitliche Token‑Zählung (OpenAI, Llama 3, Gemma 3, Mistral, Qwen, DeepSeek); Python.NET‑Brücke; Bild‑Tokenisierung für VLMs; detaillierte Kostenereignisse inkl. Caching‑Tokens; Reporting mit Heatmaps/Kennzahlen.
- Admin‑UI (Vue 3 + Inertia): Modell‑/Deployment‑Verwaltung, Parameter (Temperature/Top‑P/Penalties), Reasoning‑Effort (o1/o3‑mini), System‑Prompts, Quoten; Soft‑Delete/Restore; Auto‑Deaktivierung bei Credential‑Löschung.
- Dokumente & Kontext: Upload/Extraktion via Microsoft KernelMemory; Token‑Grenzprüfung je Deployment/Modell; On‑Demand‑Einbindung von Dokumenttexten/Bildern; tägliche Aufräumjobs mit Hangfire.
- Sicherheit & Compliance: Shibboleth‑SSO; MongoDB CSFLE (lokaler Master‑Key) für API‑Keys; EU‑Datenregion; Mandanten‑/Rollen‑Checks.
- Echtzeit & Stabilität: SignalR‑Broadcasting (Streaming‑UI), resiliente HTTP‑Pipelines (Polly), NLog; DevOps‑Kontext mit Traefik/Nomad; Embedded‑Python Runtime Setup.

#section-title("Ausbildung")
- RWTH Aachen University — Master Informatik (GenAI, LLM), Note 2,5 (2022.10–2024.06).
- RWTH Aachen University — Bachelor Informatik, Note 2,2 (2019.10–2022.09).
- Tongji Universität — Bachelor Germanistik (2014.09–2018.08).

#section-title("Ausgewählte frühere Tätigkeiten")
- Wissenschaftlicher Hilfskraft — RWTH Lehrstuhl Embedded Software (2023.08–2024.03): Wartung CPM Remote Web App; Echtzeit‑Visualisierungen; CI/CD.
- Wissenschaftlicher Hilfskraft — RWTH Lehrstuhl DBIS (2023.07–2024.03): LLM/GNN/Knowledge Graph Forschung; GPU‑Cluster‑Experimente; LLaMA/Ollama Chatplattform.

#section-title("Tech‑Stack")
C#/.NET 9, ASP.NET Core, MongoDB (CSFLE), Semantic Kernel, Azure AI Inference, OpenAI .NET, Microsoft.ML.Tokenizers, pythonnet, SkiaSharp, Hangfire, SignalR, Vue 3, Inertia.js, Vite, NLog, Traefik, Nomad, KernelMemory.
