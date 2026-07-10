---

## AMD / Gemma Usage

FitOS uses AMD Developer Cloud, ROCm, vLLM, Fireworks, and Gemma for the AI parts of the system.

The recommendation engine itself is deterministic. Gemma is used only for language-heavy tasks:

1. Parsing messy seller size charts into normalized JSON.
2. Mining fit signals from product reviews.
3. Generating shopper-facing explanations from structured recommendation JSON.

This prevents the LLM from inventing sizes while still using Gemma where it is strongest.

### AMD Developer Cloud + ROCm + vLLM

For batch AI workloads, FitOS ran Gemma on AMD Developer Cloud using ROCm and vLLM.

```txt
AMD Developer Cloud GPU instance
→ ROCm
→ vLLM
→ google/gemma-2-2b-it
→ served as fitos-gemma
→ OpenAI-compatible endpoint