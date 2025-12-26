#import "theme.typ": *

#header(
  "Ruizhang Zhou",
  "KI/ML-Ingenieur & Full-stack-Entwickler - Produktive LLM-Systeme, Deep-Learning-Forschung, Datenpipelines, Mandantenfähige Plattformen",
  [#link("mailto:ruizhang.zhou@mail.com")[ruizhang.zhou\@mail.com] | #link("https://github.com/RuizhangZhou")[GitHub] | #link("https://linkedin.com/in/ruizhang-zhou/")[LinkedIn] | #link("https://ruizhangzhou.github.io")[Website]]
)

#section-title("Erfahrung")
*Software Engineer (AI Platform) - Vollzeitstelle* | KIconnect - RWTH IT Center | 09/2024 - heute

- *Chat-Pipeline:* ASP.NET Core 9 + Semantic Kernel + Azure AI Inference/OpenAI; Streaming-Antworten, Titelgenerierung, strikte Rollenfolge, Content-Filter-Handling.
- *Tokenisierung & Kosten:* Einheitliche Tokenerfassung (OpenAI, Llama 3, Gemma 3, Mistral, Qwen, DeepSeek); Python.NET-Bridge; Bild-Tokenisierung für VLMs; detaillierte Kostenereignisse inkl. Caching-Tokens; Reporting mit Heatmaps.
- *Admin-UI:* Vue 3 + Inertia; Modell-/Deploymentverwaltung, Parameter-Tuning, System-Prompts, Quoten; Soft-Delete/Restore; automatische Deaktivierung.
- *Dokumente & Kontext:* Upload/Extraktion via KernelMemory; Token-Guardrails je Deployment/Modell; On-Demand-Einbindung; tägliche Cleanup-Jobs (Hangfire).
- *Sicherheit & Compliance:* Shibboleth-SSO; MongoDB CSFLE (lokaler Master-Key); EU-Datenregion; Mandanten-/Rollenprüfungen.
- *Echtzeit & Stabilität:* SignalR-Broadcasting (Live-UI), resiliente HTTP-Pipelines (Polly), NLog; DevOps mit Traefik/Nomad; eingebettete Python-Runtime.

#line(length: 100%, stroke: 0.5pt)

#section-title("Ausbildung")
*M.Sc. Informatik* | RWTH Aachen University | Okt. 2022 - Jun. 2024
- Masterarbeit: #link("https://github.com/RuizhangZhou/ScenarioGenerationAI")[AI-Based Generation of Testing Scenarios for Motion Planners on Connected and Automated Vehicles]
- Schwerpunkt KI/ML: Deep Learning, NLP, Large Language Models, Wissensrepräsentation

*B.Sc. Informatik* | RWTH Aachen University | Okt. 2019 - Sep. 2022

*B.A. Germanistik* | Tongji Universität | Sep. 2014 - Aug. 2018

#line(length: 100%, stroke: 0.5pt)

#section-title("Ausgewählte frühere Tätigkeiten")
*Wissenschaftliche Hilfskraft (Teilzeit)* | RWTH Lehrstuhl Embedded Software | Aug. 2023 - Mär. 2024 (8 Monate)
- Wartung/Weiterentwicklung der CPM Remote Web-Anwendung für Remote-Laborverwaltung
- Echtzeit-Datenvisualisierungen und Monitoring-Dashboards mit modernen Web-Frameworks
- Verbesserung der CI/CD-Pipelines für automatisiertes Testen/Deployment
- *Tech:* JavaScript/TypeScript, Web-APIs, Docker, GitLab CI/CD

*Wissenschaftliche Hilfskraft (Teilzeit)* | RWTH Lehrstuhl DBIS | Jul. 2023 - Mär. 2024 (9 Monate)
- Forschung zu LLM, GNN und Knowledge-Graph-Integration
- Experimente auf GPU-Cluster-Infrastruktur für Modelltraining/-evaluierung
- Entwicklung/Deployment einer LLaMA/Ollama-basierten Chat-Plattform für Forschungszwecke
- *Tech:* Python, PyTorch, Transformers, CUDA, Ollama, REST-APIs

#line(length: 100%, stroke: 0.5pt)

#section-title("Tech-Stack")
C\# / .NET 9, ASP.NET Core, MongoDB (CSFLE), Semantic Kernel, Azure AI Inference, OpenAI .NET, Microsoft.ML.Tokenizers, pythonnet, SkiaSharp, Hangfire, SignalR, Vue 3, Inertia.js, Vite, NLog, Traefik, Nomad, KernelMemory.

