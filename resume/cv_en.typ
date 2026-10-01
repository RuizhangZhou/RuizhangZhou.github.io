#import "theme.typ": *

#header(
  "Ruizhang Zhou",
  "Applied AI / AI Platform Engineer - Production LLM Systems · Backend & Infrastructure · ML Engineering",
  [#link("mailto:ruizhang.zhou@mail.com")[ruizhang.zhou\@mail.com] | #link("https://github.com/RuizhangZhou")[GitHub] | #link("https://linkedin.com/in/ruizhang-zhou/")[LinkedIn] | #link("https://ruizhangzhou.github.io")[Website]]
)

#section-title("Experience")
*Software Engineer (AI Platform)* | KI:connect - RWTH IT Center | 09/2024 - Present

- Contribute to OpenAI-compatible Chat Completions and Responses APIs, including raw request forwarding and streaming behavior
- Work on model-specific token estimation, usage and cost metering, cache-write pricing, and quota handling
- Develop ASP.NET Core services and Vue 3 admin interfaces; investigate application, provider, and deployment issues
- *Tech:* C\#/.NET, ASP.NET Core, Vue 3, MongoDB, SignalR, OpenAI-compatible APIs

#line(length: 100%, stroke: 0.5pt)

#section-title("Education")
*M.Sc. Computer Science* | RWTH Aachen University | Oct. 2022 - Jun. 2024
- Master's Thesis: #link("https://github.com/RuizhangZhou/ScenarioGenerationAI")[AI-Based Generation of Testing Scenarios for Motion Planners on Connected and Automated Vehicles ↗]
  - Implemented TimeGAN and Diffusion-TS models to generate realistic vehicle trajectory data for autonomous vehicle testing
  - Processed real-world driving datasets (inD, rounD, exiD) and evaluated generated trajectories
- Focus on AI/ML: Deep Learning, NLP, Large Language Models, Knowledge Representation

*B.Sc. Computer Science* | RWTH Aachen University | Oct. 2019 - Sep. 2022

*B.A. German Language and Literature* | Tongji University | Sep. 2014 - Aug. 2018

#line(length: 100%, stroke: 0.5pt)

#section-title("Selected previous roles")
*Research Assistant (Part-time)* | RWTH Chair of Embedded Software | Aug. 2023 - Mar. 2024
- Maintained CPM Remote Web Application for autonomous vehicle algorithm testing with real-time visualizations
- *Tech:* TypeScript, Angular, Docker, GitLab CI/CD

*Research Assistant (Part-time)* | RWTH Chair of DBIS | Jul. 2023 - Mar. 2024
- Research on medical imaging AI: combined BLIP vision-language model with LLMs for chest X-ray report generation
- Investigated Knowledge Graph integration with GNNs (GCN, GAT, GraphSAGE) to improve medical domain understanding
- Set up LLM serving with Ollama; built FastAPI REST service and end-to-end LLM chat platform
- *Tech:* Python, PyTorch, Transformers, PyG, BLIP, CUDA, Ollama, FastAPI, vLLM

#line(length: 100%, stroke: 0.5pt)

#section-title("Projects")
#link("https://github.com/RuizhangZhou/CompatBench")[*CompatBench - OpenAI-compatible API tests* ↗] | Independent open-source project
- Python CLI for testing streaming, tool calls, structured output, usage, and error behavior; produces reproducible reports

#link("https://github.com/RuizhangZhou/llm-gateway")[*LLM Gateway - Task-aware model routing* ↗] | Independent open-source project
- Routes jobs across discovered models with provider fallback and safe pre-output streaming failover

#link("https://github.com/RuizhangZhou/talkecho")[*TalkEcho - Meeting subtitles and translation* ↗] | Personal fork
