# Search Query Bundles

The search module issues four query variants for every user request to drive the local `termsearch` crawler. Each query stays under 120 characters and escapes apostrophes.

1. **Precision** – `+"<subject>" +key terms --QDF=4`
   - Uses mandatory `+` modifiers for all tokens and boosts freshness with `--QDF=4`.
2. **Recall** – loose keywords.
   - Drops modifiers to broaden the result set.
3. **Exploration** – `synonym1 OR synonym2 ... --QDF=4`
   - Uses `OR` joins to surface alternate phrasings and enforces freshness with `--QDF=4`.
4. **Validation** – `"subject" site:<trusted>`
   - Restricts hits to whitelisted domains from `config/search.yaml` to verify reliability.

Documents are accepted when `relevance ≥ 0.70` and reliability meets the ingest policy threshold. Results are sorted by relevance and reliability before ingesting in a single batch.
