# 05_LOGGING_SPEC (v1.1.4x)

**Sink:** `logs/ui_debug.log`

## Format
`YYYY-MM-DDTHH:MM:SSZ TAG Message`

## Required tags
- SMARTENTRY BOOT | IMPORT <mod> | EXPORTS [..]
- TRY_ENTRY <name> | TRY_ENTRY_OK <name> | TRY_ENTRY_ERR <name> <trace>
- FIRSTPAINT OK | BADGE OK/ERR
- HANDLER_OK <panel> <action> | HANDLER_ERR <panel> <action> <exc>
