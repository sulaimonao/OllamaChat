import argparse
import os
import json
import sys

# Add the backend directory to the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.search_engine import SearchEngine

def main():
    parser = argparse.ArgumentParser(description="CLI for the local search engine.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- Index command ---
    index_parser = subparsers.add_parser("index", help="Index a directory of documents.")
    index_parser.add_argument("path", type=str, help="The path to the directory to index.")

    # --- Search command ---
    search_parser = subparsers.add_parser("search", help="Search the index.")
    search_parser.add_argument("query", type=str, help="The search query.")
    search_parser.add_argument("--top-k", type=int, default=8, help="The number of results to return.")

    args = parser.parse_args()

    # Initialize the search engine
    search_engine = SearchEngine()

    if args.command == "index":
        if not os.path.isdir(args.path):
            print(f"Error: Path '{args.path}' is not a valid directory.")
            return

        # Get all file paths in the directory
        file_paths = []
        for root, _, files in os.walk(args.path):
            for file in files:
                file_paths.append(os.path.join(root, file))

        search_engine.index(file_paths)
        print(f"Successfully indexed {len(file_paths)} files from '{args.path}'.")

    elif args.command == "search":
        results = search_engine.search(args.query, top_k=args.top_k)
        print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
