import json
import os
import sys
import numpy as np
from tabulate import tabulate

# Add the backend directory to the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from tools.search_engine import SearchEngine

def calculate_recall_at_k(retrieved_ids, relevant_ids, k):
    """Calculates Recall@k."""
    retrieved_at_k = retrieved_ids[:k]
    relevant_retrieved = [doc_id for doc_id in retrieved_at_k if doc_id in relevant_ids]
    return len(relevant_retrieved) / len(relevant_ids) if relevant_ids else 0

def calculate_mrr(retrieved_ids, relevant_ids):
    """Calculates Mean Reciprocal Rank."""
    for i, doc_id in enumerate(retrieved_ids):
        if doc_id in relevant_ids:
            return 1 / (i + 1)
    return 0

def run_evaluation():
    """Runs the retrieval evaluation harness."""
    # 1. Load gold standard data
    gold_file_path = os.path.join(os.path.dirname(__file__), 'gold.jsonl')
    with open(gold_file_path, 'r') as f:
        gold_data = [json.loads(line) for line in f]

    # 2. Initialize SearchEngine
    search_engine = SearchEngine()

    # 3. Index documents
    data_dir = "backend/local_data"
    file_paths = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith(".md")]
    search_engine.index(file_paths)

    # 4. Run evaluation
    k = 5
    lexical_recalls = []
    lexical_mrrs = []
    hybrid_recalls = []
    hybrid_mrrs = []

    for item in gold_data:
        question = item["question"]
        relevant_ids = item["answers"]

        # Lexical search
        lexical_results = search_engine.search_lexical(question, top_k=10)
        lexical_retrieved_ids = list(dict.fromkeys([res["source_id"] for res in lexical_results])) # Deduplicate while preserving order
        lexical_recalls.append(calculate_recall_at_k(lexical_retrieved_ids, relevant_ids, k))
        lexical_mrrs.append(calculate_mrr(lexical_retrieved_ids, relevant_ids))

        # Hybrid search
        hybrid_results = search_engine.search_hybrid(question, top_k=10)
        hybrid_retrieved_ids = list(dict.fromkeys([res["source_id"] for res in hybrid_results])) # Deduplicate while preserving order
        hybrid_recalls.append(calculate_recall_at_k(hybrid_retrieved_ids, relevant_ids, k))
        hybrid_mrrs.append(calculate_mrr(hybrid_retrieved_ids, relevant_ids))

    # 5. Print results
    headers = ["Metric", "Lexical Search", "Hybrid Search"]
    table = [
        [f"Recall@{k}", np.mean(lexical_recalls), np.mean(hybrid_recalls)],
        ["MRR", np.mean(lexical_mrrs), np.mean(hybrid_mrrs)]
    ]
    print("\nRetrieval Evaluation Results:")
    print(tabulate(table, headers=headers, tablefmt="grid"))

if __name__ == "__main__":
    run_evaluation()
