.PHONY: index test-search

index:
	python -m backend.tools.search_cli index backend/local_data

test-search:
	python -m backend.tools.search_cli search "what is ollamachat?"
