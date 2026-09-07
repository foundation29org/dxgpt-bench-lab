"""
Script para re-evaluar los casos que fallaron por error 503 de la API de Gemini.
Extrae los casos específicos del labeler JSON existente y crea mini-datasets
para re-ejecutar solo la fase de evaluación (SHOULD_EMULATE=false, SHOULD_LABEL=false).

Todos los runs usan JUDGE_MODEL: gemini-2.5-pro.
"""

import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
OUTPUT_BASE = os.path.join(BASE, "output")
DATASETS_BASE = os.path.join(BASE, "..", "..", "..", "datasets")

FAILED = {
    "ddd_hpo": {
        "cases_1indexed": [1180, 1181, 1385, 1393, 1399, 1407, 1723],
        "labeler_src": os.path.join(OUTPUT_BASE, "ddd_hpo", "juanjo_classic_v2", "gemini_3_pro_preview",
            "juanjo_classic_v2___gemini_3_pro_preview___ddxs_from_labeler.json"),
        "dataset_src": os.path.join(DATASETS_BASE, "ddd_hpo.json"),
        "reeval_name": "ddd_hpo_reeval503",
        "model_name": "gemini_3_pro_preview",
        "emulator_model": "gemini-3-pro-preview",
        "prompt_name": "juanjo_classic_v2",
    },
    "mme_hpo": {
        "cases_1indexed": [8, 39],
        "labeler_src": os.path.join(OUTPUT_BASE, "mme_hpo", "juanjo_classic_v2", "gemini_3_pro_preview",
            "juanjo_classic_v2___gemini_3_pro_preview___ddxs_from_labeler.json"),
        "dataset_src": os.path.join(DATASETS_BASE, "mme_hpo.json"),
        "reeval_name": "mme_hpo_reeval503",
        "model_name": "gemini_3_pro_preview",
        "emulator_model": "gemini-3-pro-preview",
        "prompt_name": "juanjo_classic_v2",
    },
    "all_256_clean_gpt4o": {
        "cases_1indexed": [42, 49, 50, 123, 139, 154, 167],
        "labeler_src": os.path.join(OUTPUT_BASE, "all_256_clean", "juanjo_classic_v2", "gpt_4o_low_translated_en",
            "juanjo_classic_v2___gpt_4o_low_translated_en___ddxs_from_labeler.json"),
        "dataset_src": os.path.join(DATASETS_BASE, "all_256_clean.json"),
        "reeval_name": "all_256_clean_reeval503_gpt4o",
        "model_name": "gpt_4o_low_translated_en",
        "emulator_model": "gpt-4o",
        "prompt_name": "juanjo_classic_v2",
    },
    "all_275_gpt4o": {
        "cases_1indexed": [12, 16, 66, 85, 92, 119, 126, 230, 256, 258],
        "labeler_src": os.path.join(OUTPUT_BASE, "all_275", "juanjo_classic_v2", "gpt_4o_low_translated_en",
            "juanjo_classic_v2___gpt_4o_low_translated_en___ddxs_from_labeler.json"),
        "dataset_src": os.path.join(DATASETS_BASE, "all_275.json"),
        "reeval_name": "all_275_reeval503_gpt4o",
        "model_name": "gpt_4o_low_translated_en",
        "emulator_model": "gpt-4o",
        "prompt_name": "juanjo_classic_v2",
    },
    "all_256_clean_gpt5mini": {
        "cases_1indexed": [14],
        "labeler_src": os.path.join(OUTPUT_BASE, "all_256_clean", "juanjo_classic_v2", "gpt_5_mini_low_translated_en",
            "juanjo_classic_v2___gpt_5_mini_low_translated_en___ddxs_from_labeler.json"),
        "dataset_src": os.path.join(DATASETS_BASE, "all_256_clean.json"),
        "reeval_name": "all_256_clean_reeval503_gpt5mini",
        "model_name": "gpt_5_mini_low_translated_en",
        "emulator_model": "gpt-5-mini",
        "prompt_name": "juanjo_classic_v2",
    },
    "all_275_gpt5mini": {
        "cases_1indexed": [12, 229],
        "labeler_src": os.path.join(OUTPUT_BASE, "all_275", "juanjo_classic_v2", "gpt_5_mini_low_translated_en",
            "juanjo_classic_v2___gpt_5_mini_low_translated_en___ddxs_from_labeler.json"),
        "dataset_src": os.path.join(DATASETS_BASE, "all_275.json"),
        "reeval_name": "all_275_reeval503_gpt5mini",
        "model_name": "gpt_5_mini_low_translated_en",
        "emulator_model": "gpt-5-mini",
        "prompt_name": "juanjo_classic_v2",
    },
    "lirical_hpo_gpt4o": {
        "cases_1indexed": [299],
        "labeler_src": os.path.join(OUTPUT_BASE, "lirical_hpo", "juanjo_classic_v2", "gpt_4o_low",
            "juanjo_classic_v2___gpt_4o_low___ddxs_from_labeler.json"),
        "dataset_src": os.path.join(DATASETS_BASE, "lirical_hpo.json"),
        "reeval_name": "lirical_hpo_reeval503_gpt4o",
        "model_name": "gpt_4o_low",
        "emulator_model": "gpt-4o",
        "prompt_name": "juanjo_classic_v2",
    },
}


def extract_and_create(ds_key, info):
    cases_0idx = [c - 1 for c in info["cases_1indexed"]]
    print(f"\n{'='*60}")
    print(f"Run: {ds_key} | Cases (1-indexed): {info['cases_1indexed']}")

    with open(info["labeler_src"], "r", encoding="utf-8") as f:
        full_labeler = json.load(f)
    mini_labeler = [full_labeler[i] for i in cases_0idx]

    with open(info["dataset_src"], "r", encoding="utf-8") as f:
        full_dataset = json.load(f)
    mini_dataset = [full_dataset[i] for i in cases_0idx]

    reeval_name = info["reeval_name"]
    prompt_name = info["prompt_name"]
    model_name = info["model_name"]

    mini_dataset_path = os.path.join(DATASETS_BASE, f"{reeval_name}.json")
    with open(mini_dataset_path, "w", encoding="utf-8") as f:
        json.dump(mini_dataset, f, ensure_ascii=False, indent=2)

    out_dir = os.path.join(OUTPUT_BASE, reeval_name, prompt_name, model_name)
    os.makedirs(out_dir, exist_ok=True)

    prefix = f"{prompt_name}___{model_name}"
    labeler_dest = os.path.join(out_dir, f"{prefix}___ddxs_from_labeler.json")
    with open(labeler_dest, "w", encoding="utf-8") as f:
        json.dump(mini_labeler, f, ensure_ascii=False, indent=2)

    config_content = f"""# Re-evaluación de casos fallados por 503 - {ds_key}
# Casos originales (1-indexed): {info['cases_1indexed']}

EXPERIMENT_NAME: "{reeval_name}-{prompt_name}-low"
EXPERIMENT_DESCRIPTION: "Re-eval {len(cases_0idx)} casos 503 en {ds_key}. Casos: {info['cases_1indexed']}"

DATASET_PATH: "bench/datasets/{reeval_name}.json"

DXGPT_EMULATOR:
  MODEL: "{info['emulator_model']}"
  CANDIDATE_PROMPT_PATH: "bench/candidate-prompts/juanjo_classic_v2.txt"
  PARAMS:
    temperature: 0.1
    max_tokens: 12000
  OUTPUT_SCHEMA: false
  OUTPUT_SCHEMA_PATH: "bench/candidate-prompts/candidate_output_schema.json"
  TRANSLATE_CASE:
    ENABLED: false

EVALUATOR:
  BERT_ACCEPTANCE_THRESHOLD: 0.80
  BERT_AUTOCONFIRM_THRESHOLD: 0.90
  ENABLE_ICD10_PARENT_SEARCH: true
  ENABLE_ICD10_SIBLING_SEARCH: true
  JUDGE_MODEL: "gemini-2.5-pro"
  JUDGE_PARAMS:
    reasoning_effort: "low"
    thinking_level: "low"
    max_tokens: 10000
    temperature: 0.1

MAIN:
  SHOULD_EMULATE: false
  SHOULD_LABEL: false
  SHOULD_EVALUATE: true

TIMESTAMP: null
"""
    config_path = os.path.join(BASE, f"config_{reeval_name}.yaml")
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(config_content)
    print(f"  → {len(mini_dataset)} cases | config: config_{reeval_name}.yaml")
    return config_path


if __name__ == "__main__":
    skip = {"ddd_hpo", "mme_hpo"}  # already re-evaluated
    results = {}
    for ds_key, info in FAILED.items():
        if ds_key in skip:
            print(f"Skipping {ds_key} (already re-evaluated)")
            continue
        config_path = extract_and_create(ds_key, info)
        results[ds_key] = config_path

    print(f"\n{'='*60}")
    print("Commands (run sequentially):")
    for ds_key, config_path in results.items():
        print(f"  python main.py --config {os.path.basename(config_path)}")
