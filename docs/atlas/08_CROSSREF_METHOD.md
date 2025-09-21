# 08_CROSSREF_METHOD (v1.1.4x)

To map references between files:
1. Grep for imports: `Select-String -Path app\**\*.py -Pattern '^from app\.|^import app\.' -AllMatches`
2. Build a table: who imports what, and who calls which public API.
3. For each module, fill a `TEMPLATE_MODULE_CARD.md` and place it under `docs/atlas/module/`.
