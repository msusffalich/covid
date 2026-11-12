# Global Brain / Global Pulse — OpenAI migration ledger
## Migration decision record — 2026-11-12
User requested complete replacement of Anthropic with OpenAI and verification before revocation.
Credential decision: create new Global Pulse key in selected Personal / Default project;
approved destination backend/.env, ignored by Git. Replacement key tested live: completed / OK.
Scope: research, legacy cluster synthesis, Nexo facts and analysis, trends, orchestration and Actions.
Single approved delivery stage, implementation and validation together; no extra agent architecture.
Direct Responses over HTTPS preserves existing custom orchestration; research's single LangChain
invocation removed rather than upgrading its obsolete dependency stack. Existing endpoints,
JSON shapes, source policies, local persistence, retries and SSE progress remain.

### Capability assessment (all guidance sections reviewed)
- Model selection: gpt-4.1-mini verified available; OPENAI_MODEL configurable; no legacy OpenAI model.
- Instruction file naming: no instruction files changed.
- Responses: native /v1/responses replaces Anthropic messages in all workloads.
- Streaming: retain SSE progress; JSON buffered before validation/persistence; no token streaming.
- WebSocket: not needed for single-shot JSON synthesis; HTTP retained.
- Privacy/ZDR/residency: stateless store:false; no server-side conversations; this does not imply ZDR.
  No specific residency/ZDR requirement supplied; no regional or extended-cache opt-in.
- Processing tiers: standard; synchronous published daily cycle cannot wait 24h for Batch;
  Priority, Flex and reserved capacity not introduced under provider replacement.
- Caching: fixed instruction prefix before request data; stable workload cache keys for GPT-4.1;
  no extended retention, later-model breakpoints or diagnostics (not supported by chosen model).
- State management/instruction persistence: each independent request resends full instructions;
  checkpoints and session state remain local; no previous_response_id.
- Reasoning/encrypted items/effort/preservation/summaries: non-reasoning GPT-4.1 model;
  no multi-turn reasoning replay or exposed reasoning in current product.
- Verbosity: no unsupported verbosity parameter; existing prompts determine output length.
- Output limits: preserve 8192 research, 16000 Nexo, 900 cluster, 500 trends.
- Assistant phases: no assistant message replay in these single-turn workflows.
- Compaction: no growing conversation; not applicable.
- Structured output: JSON mode for research/clusters/trends; forced function for existing Nexo
  schema including open analysis objects, strict:false; existing validators retained.
- Tool choice: force entregar_resultado in Nexo as before; function only returns data,
  performs no effects. Search remains application-controlled Tavily/DuckDuckGo.
- Tool search/additional tools/parallel/programmatic calls/model-aligned interfaces:
  no model-selected executable tool loop; no tool redesign or concurrency introduced.

### Validation and rollout coverage
Mock HTTP transport: authorization/endpoint, model override, limits, JSON/function outputs,
incomplete/error/refusal paths. Existing pipeline suites cover publish/checkpoints/citations.
Live: exercise actual research transport and Nexo facts/analysis plus legacy clusters/trends,
without publishing test artifacts. Complete existing suite to run before handoff.
Production: GitHub Actions must receive OPENAI_API_KEY and updated committed code;
Git Credential Manager authenticated outside sandbox; OPENAI_API_KEY secret configured securely in Actions. Do not revoke
Anthropic until remote daily cycle and any deployed research backend use OpenAI successfully.

Validation: 17 unittest checks + 7 existing functional pipeline checks passed. All five live OpenAI routes passed (research, Nexo facts, Nexo analysis, cluster, trends). Responses JSON mode requires system instructions inside input messages; verified live. Remote rollout and daily workflow verification pending.

Production verification: first run 43256780163 passed tests and live OpenAI auth, then exposed missing estado in a real trend JSON response. Fixed with strict JSON Schema requiring bilingual resumen/estado and local shape validation inside the fallback boundary. Added malformed-output coverage. All five live route checks passed again. Railway confirmed successful static-only deployment, no provider variables or research backend in production.
