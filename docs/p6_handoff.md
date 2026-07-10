# P6 AI / AMD Handoff

## Branch

feat/ai-infra

## P6 Scope

P6 owns the AI infrastructure side of FitOS / Wardrobe-Hub.

This includes:

- Fireworks LLM client for live explanation generation
- AMD Developer Cloud proof
- ROCm + vLLM + Gemma serving
- Review-mining batch using AMD-hosted Gemma
- Size-chart parser using AMD-hosted Gemma
- Review analysis DB ingest proof
- AMD proof files for README, deck, and demo

This work does not train or fine-tune any model.

FitOS uses a deterministic recommendation engine for the final size decision. Gemma is used only for language-heavy tasks:

1. Explaining recommendation JSON
2. Mining fit signals from reviews
3. Parsing messy seller size charts

## Completed Work

- Fireworks LLM client setup
- Shopper-facing explanation generation
- Template fallback when LLM output is bad
- Guardrail for bad / non-shopper-facing LLM output
- AMD Developer Cloud instance tested
- ROCm / GPU proof captured
- vLLM served Gemma on AMD Developer Cloud
- Review miner ran against AMD-hosted Gemma
- 240-review benchmark captured
- Review analysis output generated
- Review analysis ingested into SQLite
- Size-chart parser created
- Size-chart parser ran against AMD-hosted Gemma
- AMD proof files captured in docs/amd_proof

## Main Files

backend/ai/llm_client.py  
backend/ai/batch_analysis.py  
backend/ai/chart_parser.py  
scripts/ingest_review_analysis.py  
requirements-ai.txt  
.env.example  

data/sample/reviews.sample.json  
data/sample/reviews.benchmark.240.json  
data/sample/raw_size_charts.sample.json  

data/processed/review_analysis.example.json  
data/processed/review_analysis.amd.json  
data/processed/review_analysis.amd.240.json  
data/processed/parsed_size_charts.example.json  
data/processed/parsed_size_charts.amd.json  
data/processed/fitos_ai_demo.sqlite  

docs/amd_proof/

## 1. LLM Explanation Client

Main file:

backend/ai/llm_client.py

Purpose:

Takes recommendation JSON from the deterministic recommender and returns a clean shopper-facing explanation.

Example usage:

from backend.ai.llm_client import explain_recommendation

explanation = explain_recommendation(recommendation_json)

Example output:

We recommend size L with 87% confidence based on your measurements, fit preference, and the garment size chart. Review signals show this item runs small in shoulders, so the recommendation accounts for that fit risk.

Important behavior:

If the model returns bad output, reasoning text, markdown analysis, or non-shopper-facing text, the client rejects it and falls back to a clean template explanation.

This prevents the demo from breaking.

## 2. Review Mining Batch

Main file:

backend/ai/batch_analysis.py

Purpose:

Classifies product reviews into fit signals and aggregates them into review analysis JSON.

Per-review output shape:

{
  "fit_verdict": "small",
  "areas": ["waist"],
  "severity": 2,
  "quote": "The waist is a bit tight..."
}

Aggregated output includes:

- product_id
- total_reviews
- pct_small
- pct_large
- pct_tts
- top_issues_json
- classified_reviews
- analysis_mode
- updated_at

Local fallback command:

py -m backend.ai.batch_analysis --mode local

AMD vLLM command:

python -m backend.ai.batch_analysis --mode amd-vllm --input data/sample/reviews.sample.json --output data/processed/review_analysis.amd.json

240-review benchmark command:

python -m backend.ai.batch_analysis --mode amd-vllm --input data/sample/reviews.benchmark.240.json --output data/processed/review_analysis.amd.240.json

Benchmark result:

Input reviews: 240  
Products analyzed: 3  
Elapsed seconds: 39.9668  
Reviews/sec: 6.0050  
Backend: AMD Developer Cloud + ROCm + vLLM + Gemma  

Use this line in dashboard / deck:

Review analysis: 240 reviews / 39.97s on AMD MI300X (vLLM + ROCm)

## 3. Size Chart Parser

Main file:

backend/ai/chart_parser.py

Purpose:

Takes messy seller size chart text and normalizes it into structured JSON with cm measurements.

Input:

data/sample/raw_size_charts.sample.json

Outputs:

data/processed/parsed_size_charts.example.json  
data/processed/parsed_size_charts.amd.json  

Local fallback command:

py -m backend.ai.chart_parser --mode local

AMD vLLM command:

python -m backend.ai.chart_parser --mode amd-vllm --input data/sample/raw_size_charts.sample.json --output data/processed/parsed_size_charts.amd.json

Expected output shape:

{
  "product_id": "jeans_001",
  "category": "jeans",
  "unit_detected": "inch",
  "sizes": [
    {
      "label": "30",
      "waist": 76.2,
      "hips": 96.5,
      "inseam": 78.7
    }
  ],
  "missing_fields": ["chest", "bust", "length", "sleeve", "shoulder"],
  "warnings": ["Converted inches to cm"],
  "parser_backend": "amd-vllm"
}

## 4. DB Ingest

Main file:

scripts/ingest_review_analysis.py

Purpose:

Reads review analysis JSON and inserts or updates product review-analysis rows into SQLite.

Run:

py scripts\ingest_review_analysis.py

Verify rows:

py -c "import sqlite3; conn = sqlite3.connect('data/processed/fitos_ai_demo.sqlite'); rows = conn.execute('SELECT product_id, total_reviews, pct_small, pct_large, pct_tts, analysis_mode FROM review_analysis').fetchall(); [print(row) for row in rows]; conn.close()"

Expected products:

- jeans_001
- shirt_001
- dress_001

## 5. AMD / vLLM Setup Summary

The AMD setup used:

AMD Developer Cloud GPU Droplet  
ROCm  
vLLM image/container  
google/gemma-2-2b-it  
served model name: fitos-gemma  
OpenAI-compatible endpoint: http://localhost:8000/v1  

vLLM model test:

curl http://localhost:8000/v1/models

vLLM chat test:

curl http://localhost:8000/v1/chat/completions -H "Content-Type: application/json" -d "{\"model\":\"fitos-gemma\",\"messages\":[{\"role\":\"user\",\"content\":\"Reply with exactly: FitOS AMD vLLM Gemma works.\"}],\"temperature\":0,\"max_tokens\":30}"

Expected response:

FitOS AMD vLLM Gemma works.

## 6. Important Environment Variables

Never commit .env.

Use .env.example as the safe template.

Important variables:

FIREWORKS_API_KEY=  
FIREWORKS_BASE_URL=https://api.fireworks.ai/inference/v1  
FIREWORKS_MODEL=  

AMD_LLM_URL=http://localhost:8000/v1  
AMD_LLM_MODEL=fitos-gemma  
AMD_LLM_API_KEY=not-needed  

USE_CACHE=true  
CACHE_DIR=data/cache  
LLM_TIMEOUT_SECONDS=20  
LLM_TEMPERATURE=0.2  
LLM_HELLO_MESSAGE=FitOS LLM connection works.  
LLM_PROMPT_VERSION=v1  

REVIEW_INPUT_PATH=data/sample/reviews.sample.json  
REVIEW_ANALYSIS_OUTPUT_PATH=data/processed/review_analysis.example.json  
REVIEW_ANALYSIS_MODE=local  

SIZE_CHART_INPUT_PATH=data/sample/raw_size_charts.sample.json  
SIZE_CHART_OUTPUT_PATH=data/processed/parsed_size_charts.example.json  
SIZE_CHART_PARSE_MODE=local  

## 7. AMD Proof Files

Proof files are stored in:

docs/amd_proof/

Important files:

amd_llm_hello.txt  
amd_llm_explain_test.txt  
amd_system.txt  
rocm_smi.txt  
vllm_models.json  
vllm_gemma_test.json  
vllm_server_log_tail.txt  
rocm_smi_vllm.txt  
review_analysis_amd_7.json  
review_analysis_amd_240.json  
amd_review_mining_benchmark.txt  
rocm_smi_review_mining.txt  
vllm_models_after_review_mining.json  
parsed_size_charts_amd.json  
rocm_smi_chart_parser.txt  
vllm_models_chart_parser.json  

These prove:

- AMD Cloud SSH worked
- ROCm detected AMD GPU
- vLLM served Gemma
- Gemma answered through OpenAI-compatible endpoint
- Review mining ran on AMD-hosted Gemma
- Size chart parsing ran on AMD-hosted Gemma
- Throughput benchmark was captured

## 8. Current Limitations

- Full-stack deployment on AMD is still a final demo/deployment task.
- Backend /api/explain integration depends on P4 backend readiness.
- Final seller dashboard display depends on P3 frontend wiring.
- Final schema may need adjustment after main branch/data docs are merged.
- AMD droplet does not need to stay running after proof is captured.

## 9. Teammate Notes

P4 backend can use:

from backend.ai.llm_client import explain_recommendation

P3 seller dashboard can use:

data/processed/review_analysis.amd.240.json  
data/processed/parsed_size_charts.amd.json  
data/processed/fitos_ai_demo.sqlite  

P1 / pitch can use this benchmark line:

Review analysis: 240 reviews / 39.97s on AMD MI300X (vLLM + ROCm)

P6 should only recreate AMD droplet for:

- final deploy
- final rehearsal
- screenshot/video capture
- last-minute proof regeneration

Otherwise, destroy it to save credits.