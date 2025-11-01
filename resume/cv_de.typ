#import "theme.typ": *

#header(
  "Ruizhang Zhou",
  "Full-stack KI-Plattform-Ingenieur - Streaming-Chat / Token- und Kosten-Governance / Mandantensicherheit / SSO",
  [#link("mailto:ruizhang.zhou@mail.com")[ruizhang.zhou\@mail.com] | #link("https://github.com/RuizhangZhou")[GitHub] | #link("https://linkedin.com/in/ruizhang-zhou/")[LinkedIn] | #link("https://ruizhangzhou.github.io")[Website]]
)

#section-title("Erfahrung")
*Software Engineer (AI Platform) - Vollzeitstelle, KIconnect - RWTH IT Center* \
09/2024 - heute (14 Monate)

- Chat-Pipeline (ASP.NET Core 9 + Semantic Kernel + Azure AI Inference/OpenAI): Streaming-Antworten, Titelgenerierung, strikte Rollenfolge, Handling von Content-Filtern (Reasoning- / Think-Tags).
- Tokenisierung und Kosten: Einheitliche Tokenerfassung (OpenAI, Llama 3, Gemma 3, Mistral, Qwen, DeepSeek); Python.NET-Bridge; Bild-Tokenisierung für VLMs; detaillierte Kostenereignisse inklusive Caching-Tokens; Reporting mit Heatmaps und Kennzahlen.
- Admin-Oberfläche (Vue 3 + Inertia): Modell- und Deploymentverwaltung, Parameter (Temperature / Top-p / Penalties), System-Prompts, Quoten; Soft-Delete und Restore; automatische Deaktivierung bei Credential-Entzug.
- Dokumente und Kontext: Upload und Extraktion via Microsoft KernelMemory; Token-Grenzprüfung je Deployment und Modell; bedarfsgerechte Einbindung von Dokumenttexten und Bildern; tägliche Aufräumjobs mit Hangfire.
- Sicherheit und Compliance: Shibboleth-SSO; MongoDB CSFLE (lokaler Master-Key) für API-Schlüssel; EU-Datenregion; Mandanten- und Rollenprüfungen.
- Echtzeit und Stabilität: SignalR-Broadcasting (Streaming-UI), resiliente HTTP-Pipelines via Polly, NLog; DevOps-Kontext mit Traefik und Nomad; Setup einer eingebetteten Python-Runtime.

#section-title("Ausbildung")
*RWTH Aachen University - M.Sc. Informatik* \
Oktober 2022 - Juni 2024 | Abschlussnote: 2,5 (Gut)
- Schwerpunkt: Generative KI, Large Language Models, Machine Learning
- Masterarbeit: [Thema im Bereich LLM/GenAI-Anwendungen]
- Relevante Module: Deep Learning, Natural Language Processing, Wissensrepräsentation, Verteilte Systeme, Software Engineering

*RWTH Aachen University - B.Sc. Informatik* \
Oktober 2019 - September 2022 | Abschlussnote: 2,2 (Gut)
- Schwerpunkt: Software Engineering, Algorithmen und Datenstrukturen, Datenbanksysteme
- Bachelorarbeit: [Thema im Bereich Softwareentwicklung/Systeme]
- Relevante Module: Objektorientierte Programmierung, Web-Technologien, Rechnernetze, Betriebssysteme

*Tongji Universität - B.A. Germanistik* \
September 2014 - August 2018
- Fundierte Deutschkenntnisse, die effektive Kommunikation in deutschsprachigen Arbeitsumgebungen ermöglichen
- Interkulturelle Kompetenz und sprachliche Fähigkeiten in akademischen und beruflichen Kontexten

#section-title("Ausgewählte frühere Tätigkeiten")
*Wissenschaftliche Hilfskraft (Teilzeit), RWTH Lehrstuhl Embedded Software* \
August 2023 - März 2024 (8 Monate)
- Wartung und Weiterentwicklung der CPM Remote Web-Anwendung für Remote-Laborverwaltung
- Implementierung von Echtzeit-Datenvisualisierungen und Monitoring-Dashboards mit modernen Web-Frameworks
- Verbesserung der CI/CD-Pipelines für automatisiertes Testen und Deployment
- Technologien: JavaScript/TypeScript, Web-APIs, Docker, GitLab CI/CD

*Wissenschaftliche Hilfskraft (Teilzeit), RWTH Lehrstuhl DBIS (Datenbanken und Informationssysteme)* \
Juli 2023 - März 2024 (9 Monate)
- Forschung zu Large Language Models (LLM), Graph Neural Networks (GNN) und Knowledge-Graph-Integration
- Entwurf und Durchführung von Experimenten auf GPU-Cluster-Infrastruktur für Modelltraining und -evaluierung
- Entwicklung und Deployment einer LLaMA / Ollama-basierten Chat-Plattform für Forschungszwecke
- Technologien: Python, PyTorch, Transformers, CUDA, Ollama, REST-APIs

#section-title("Tech-Stack")
C\# / .NET 9, ASP.NET Core, MongoDB (CSFLE), Semantic Kernel, Azure AI Inference, OpenAI .NET, Microsoft.ML.Tokenizers, pythonnet, SkiaSharp, Hangfire, SignalR, Vue 3, Inertia.js, Vite, NLog, Traefik, Nomad, KernelMemory.

