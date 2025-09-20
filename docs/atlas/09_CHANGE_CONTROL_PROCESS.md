# 09_CHANGE_CONTROL_PROCESS (v1.1.4x)

1) Write the intent in patch notes first.
2) Back up files as `*.bak.v1.1.4x`.
3) Make the smallest change that satisfies the contract.
4) Purge `__pycache__`.
5) Run acceptance steps and paste log snippets into patch notes.
6) If failure: revert fast, document the reason, try again.
