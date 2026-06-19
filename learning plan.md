## Plan: AI Learning Workspace Roadmap

Build a Python-first learning system that progresses from fundamentals to practical use cases to reusable libraries, then composes those libraries into apps. The approach is to standardize a compact core stack, reorganize your workspace by learning maturity, and follow a 12-week sequence that repeatedly converts experiments into tested reusable modules.

**Steps**
1. Establish a default core stack and constraints for all new learning work. Includes uv for environment/package workflow, Ruff + Pyright + Pytest for quality, and script-first reproducibility before notebooks. This is the baseline for every later phase.
2. Define learning lanes by maturity and enforce where work belongs: fundamentals (concept drills), experiments (rapid probing), use-cases (problem-focused mini projects), reusable-libs (shared modules), apps (composed deliverables), evals (quality benchmarks), data (datasets/artifacts), archive (retired references).
3. Consolidate AI/ML/data tools into a deliberate “one primary per layer” policy to prevent framework sprawl. Data: Polars + DuckDB + Parquet/PyArrow. LLM providers: direct SDK usage first (OpenAI/Anthropic/Google), local model path via Ollama. Retrieval: Chroma now, evaluate Qdrant/pgvector next. Orchestration: choose one after SDK mastery (LangGraph or LlamaIndex workflows).
4. Reclassify current workspace assets into the new lanes. Keep existing demos/tutorials as seed material but treat third-party tutorial copies as reference-only, then progressively promote useful patterns into reusable-libs and apps.
5. Implement reusable call patterns as the main learning deliverable in reusable-libs: provider adapter layer, structured output contracts, retries/timeouts, embedding/index/search interfaces, and evaluation harness glue. This enables app composition without provider-coupled rewrites.
6. Build one capstone app by composing reusable modules (depends on steps 1-5). Expose both CLI and API paths, backed by the same library contracts, and validate using eval datasets and regression checks.
7. Run verification on every phase (parallel with steps 3-6): tests, retrieval quality checks, latency/cost tracking, and smoke checks for local and hosted models.

**Relevant files**
- c:/Users/wrightm/OneDrive - Amphenol TCS/Development/sandbox-personal/sandbox-matt/tutorials/real-python/open-ai/function_assistant.py — reuse as structured-output + function/tool-calling pattern reference.
- c:/Users/wrightm/OneDrive - Amphenol TCS/Development/sandbox-personal/sandbox-matt/tutorials/real-python/openrouter/ask_auto_model.py — reuse as provider routing/client abstraction seed.
- c:/Users/wrightm/OneDrive - Amphenol TCS/Development/sandbox-personal/sandbox-matt/tutorials/real-python/vectors-embeddings/car_data_etl.py — reuse ingestion and transformation ideas for data contracts.
- c:/Users/wrightm/OneDrive - Amphenol TCS/Development/sandbox-personal/sandbox-matt/tutorials/real-python/vectors-embeddings/chroma_utils.py — reuse vector indexing/retrieval utility patterns.
- c:/Users/wrightm/OneDrive - Amphenol TCS/Development/sandbox-personal/sandbox-matt/tutorials/real-python/vectors-embeddings/api.py — reuse service boundary pattern when promoting modules into apps.
- c:/Users/wrightm/OneDrive - Amphenol TCS/Development/sandbox-personal/sandbox-matt/scripts/setup-venv.ps1 — retain as environment bootstrap starting point; align with uv workflow over time.

**Verification**
1. Each new module has at least one unit test and one integration smoke test, executed through Pytest.
2. Data flow checks: deterministic transforms from raw to Parquet and schema assertions on key metadata fields.
3. Retrieval checks: fixed question set with expected source-document relevance thresholds.
4. LLM checks: prompt regression set for structured outputs and failure-path behavior (timeouts/retries).
5. App checks: CLI and API both exercise the same reusable library functions and return consistent outputs.

**Decisions**
- Included scope: learning roadmap, stack recommendation, folder architecture, progression path, and migration strategy from current workspace.
- Excluded scope: immediate file move/rename implementation, dependency pinning specifics, and final framework lock-in between LangGraph vs LlamaIndex.
- Default strategy: start framework-light (direct SDK + reusable adapters), then adopt one orchestration framework only after stable reusable contracts exist.

**Further Considerations**
1. Orchestration framework decision point (Week 9): Option A LangGraph for explicit state-machine style control, Option B LlamaIndex workflows for retrieval-centric pipelines. Recommendation: choose the one best aligned with your capstone app shape, not popularity.
2. Vector backend decision point (Week 6): Option A stay on Chroma for local learning speed, Option B move to Qdrant/pgvector for production-like behavior. Recommendation: benchmark on one identical dataset before switching.
3. Notebook policy: Option A notebooks only for exploratory analysis, Option B mixed notebook/script workflow. Recommendation: keep notebooks exploratory only; promote anything reusable to scripts/modules with tests.
