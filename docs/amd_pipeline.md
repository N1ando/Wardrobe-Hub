# AMD / Gemma Benchmark Pipeline

How the AMD evidence in [`docs/amd_proof/`](amd_proof/) was produced, and how to
reproduce it. The harness lives in `tools/amd_benchmark/` and is standalone —
the production API uses its own Gemma stack (`backend/app/ai/`, fallback ladder
vLLM → Fireworks → cache → template).

FitOS uses a **deterministic recommendation engine** for the final size
decision. Gemma is used only for language-heavy tasks: explaining
recommendation JSON, mining fit signals from reviews, and parsing messy seller
size charts. No model is trained or fine-tuned.

## AMD / vLLM setup

```txt
AMD Developer Cloud GPU instance
  -> ROCm
  -> vLLM
  -> google/gemma-2-2b-it (served as "fitos-gemma")
  -> OpenAI-compatible endpoint: http://localhost:8000/v1
```

Connection tests:

```bash
curl http://localhost:8000/v1/models
curl http://localhost:8000/v1/chat/completions -H "Content-Type: application/json" \
  -d '{"model":"fitos-gemma","messages":[{"role":"user","content":"Reply with exactly: FitOS AMD vLLM Gemma works."}],"temperature":0,"max_tokens":30}'
```

## Review-mining benchmark

```bash
# local keyword fallback (no LLM needed)
python -m tools.amd_benchmark.batch_analysis --mode local

# against AMD-hosted Gemma
python -m tools.amd_benchmark.batch_analysis --mode amd-vllm \
  --input data/sample/reviews.sample.json --output data/processed/review_analysis.amd.json

# the 240-review throughput benchmark
python -m tools.amd_benchmark.batch_analysis --mode amd-vllm \
  --input data/sample/reviews.benchmark.240.json --output data/processed/review_analysis.amd.240.json
```

**Measured result: 240 reviews / 39.97s / 6.0 reviews-per-second** on AMD
Developer Cloud (ROCm + vLLM + Gemma). The input set is synthetic and the
client is sequential (one request at a time): the number is **functional
execution proof** — the pipeline running end-to-end on AMD hardware — not a
tuned-throughput claim. Request batching / async clients are future work.
Headline line for dashboard/deck:

> Review analysis: 240 reviews / 39.97s on AMD MI300X (vLLM + ROCm, sequential client)

Per-review output shape: `{"fit_verdict": "small|large|tts|none", "areas":
["waist"], "severity": 1-3, "quote": "..."}`, aggregated into per-product
`pct_small` / `pct_tts` / `pct_large` + top complaint areas.

## Size-chart parser

```bash
python -m tools.amd_benchmark.chart_parser --mode local
python -m tools.amd_benchmark.chart_parser --mode amd-vllm \
  --input data/sample/raw_size_charts.sample.json --output data/processed/parsed_size_charts.amd.json
```

Normalizes messy seller chart text (mixed units, missing columns) into
structured cm JSON with `unit_detected`, `missing_fields`, and `warnings`.

## Files

- `tools/amd_benchmark/` — the harness (LLM client with guardrails + template
  fallback, review miner, chart parser, SQLite ingest) and its
  `requirements.txt`.
- `data/sample/` — benchmark inputs (240-review set, sample charts).
- `data/processed/` — runtime output location (`*.example.json` committed as
  local-mode references; AMD-run outputs regenerate on each run).
- `docs/amd_proof/` — the **canonical captured evidence** from the AMD runs.
- Environment template: the "AMD benchmark harness" section of `.env.example`.

## Proof index (docs/amd_proof/)

| File(s) | Proves |
|---|---|
| `amd_system.txt`, `rocm_smi.txt` | The instance is an AMD GPU box; ROCm sees the GPU |
| `vllm_server_log_tail.txt`, `vllm_models*.json` | vLLM served Gemma as `fitos-gemma` |
| `amd_llm_hello.txt`, `vllm_gemma_test.json`, `amd_llm_explain_test.txt` | Gemma answered through the OpenAI-compatible endpoint, including a recommendation explanation |
| `rocm_smi_review_mining.txt`, `review_analysis_amd_7.json`, `review_analysis_amd_240.json`, `amd_review_mining_benchmark.txt` | Review mining ran on the AMD GPU; the 240-review throughput benchmark |
| `rocm_smi_chart_parser.txt`, `parsed_size_charts_amd.json` | Size-chart parsing ran on the AMD GPU |

Note: `amd_system.txt` mentions DigitalOcean — AMD Developer Cloud GPU
instances run on DigitalOcean infrastructure. The `rocm-smi` captures confirm
the AMD GPU underneath.
