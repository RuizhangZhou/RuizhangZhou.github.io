#import "theme.typ": *

#header(
  "Ruizhang Zhou",
  "Full-stack AI Platform Engineer - Streaming chat / Token & cost governance / Multi-tenant security / SSO",
  [#link("mailto:ruizhang.zhou@mail.com")[ruizhang.zhou\@mail.com] | #link("https://github.com/RuizhangZhou")[GitHub] | #link("https://linkedin.com/in/ruizhang-zhou/")[LinkedIn] | #link("https://ruizhangzhou.github.io")[Website]]
)

#section-title("Experience")
*Software Engineer (AI Platform) - Full-time Position, KIconnect - RWTH IT Center* \
09/2024 - Present (14 months)

- Chat pipeline (ASP.NET Core 9 + Semantic Kernel + Azure AI Inference/OpenAI): streaming responses, title generation, strict role alternation, content-filter handling (reasoning / think tags).
- Tokenization and costing: unified token counting (OpenAI, Llama 3, Gemma 3, Mistral, Qwen, DeepSeek); Python.NET bridge; image tokenization for VLMs; detailed cost events including cached tokens; reporting with heatmaps and metrics.
- Admin UI (Vue 3 + Inertia): model and deployment management, parameters (temperature / top-p / penalties), system prompts, quotas; soft-delete and restore; auto-deactivation on credential removal.
- Documents and context: upload and extraction via Microsoft KernelMemory; per-deployment and per-model token guardrails; on-demand inclusion of document text and images; daily cleanup with Hangfire.
- Security and compliance: Shibboleth SSO; MongoDB CSFLE (local master key) for API keys; EU data-processing region; tenant and role checks.
- Realtime and resilience: SignalR broadcasting (live UI), resilient HTTP via Polly, NLog; DevOps context with Traefik and Nomad; embedded Python runtime setup.

#section-title("Education")
*RWTH Aachen University - M.Sc. Computer Science* \
October 2022 - June 2024 | Final Grade: 2.5 (Good)
- Focus: Generative AI, Large Language Models, Machine Learning
- Master's Thesis: [Topic related to LLM/GenAI applications]
- Relevant Coursework: Deep Learning, Natural Language Processing, Knowledge Representation, Distributed Systems, Software Engineering

*RWTH Aachen University - B.Sc. Computer Science* \
October 2019 - September 2022 | Final Grade: 2.2 (Good)
- Focus: Software Engineering, Algorithms and Data Structures, Database Systems
- Bachelor's Thesis: [Topic related to software development/systems]
- Relevant Coursework: Object-Oriented Programming, Web Technologies, Computer Networks, Operating Systems

*Tongji University - B.A. German Language and Literature* \
September 2014 - August 2018
- Strong foundation in German language proficiency, enabling effective communication in German-speaking work environments
- Cross-cultural competence and linguistic skills applied in academic and professional contexts

#section-title("Selected previous roles")
*Research Assistant (Part-time), RWTH Chair of Embedded Software* \
August 2023 - March 2024 (8 months)
- Maintained and enhanced CPM Remote Web Application for remote laboratory management
- Implemented real-time data visualizations and monitoring dashboards using modern web frameworks
- Improved CI/CD pipelines for automated testing and deployment
- Technologies: JavaScript/TypeScript, Web APIs, Docker, GitLab CI/CD

*Research Assistant (Part-time), RWTH Chair of DBIS (Database and Information Systems)* \
July 2023 - March 2024 (9 months)
- Conducted research on Large Language Models (LLM), Graph Neural Networks (GNN), and Knowledge Graph integration
- Designed and executed experiments on GPU cluster infrastructure for model training and evaluation
- Developed and deployed LLaMA / Ollama-based chat platform for research purposes
- Technologies: Python, PyTorch, Transformers, CUDA, Ollama, REST APIs

#section-title("Tech Stack")
C\# / .NET 9, ASP.NET Core, MongoDB (CSFLE), Semantic Kernel, Azure AI Inference, OpenAI .NET, Microsoft.ML.Tokenizers, pythonnet, SkiaSharp, Hangfire, SignalR, Vue 3, Inertia.js, Vite, NLog, Traefik, Nomad, KernelMemory.

