# Handoffs

## Target catalog overlay queue
- **Flow:** Target catalog → Overlay queue → ingestion processor. Selecting "Overlay" on a curated spectrum now enqueues the remote URL with a stable label. The main app loop downloads each entry, routes it through the existing local ingest pipeline, and publishes the overlay with provenance.
- **State:** The queue is processed on every rerun and is cleared after ingestion. Ledger-lock decisions continue to gate duplicate handling; the checkbox mirrors the `duplicate_ledger_lock` model state and no longer mutates widget keys directly.

## Support notes
- **Ingestion failures:** Users see a toast explaining which overlay failed. Inspect Streamlit server logs for stack traces and retry by re-queuing the spectrum. Network outages or malformed payloads will leave the queue empty after processing.

- **Metadata guardrails:** Files with fewer than three samples are rejected as metadata. If a user expects a spectrum but hits this guard, double-check the MAST product (metadata files often end with `_metadata.txt`).

- **Ledger lock:** Confirmation prompts now toggle the model state (`duplicate_ledger_lock`) without writing to `duplicate_ledger_lock_checkbox`. If overlays stop deduping, confirm that ledger lock is enabled and that the ledger backend is reachable.
- **Logs:** Application warnings surface inline; detailed errors stream to the console running `streamlit run app/ui/main.py`. When diagnosing repeated failures, enable debug logging on the fetcher or capture the downloaded payload from `/tmp` for offline inspection.
