# Runners & Launchers

Run everything from C:\Code\spectra-app\

- RUN_CMDS\Verify-Project.ps1
  First step. Confirms repo structure, version.json, brains + handoff notes.

- RUN_CMDS\Start-Spectra.ps1
  Boots the app. Accepts -Port to change port.

- RUN_CMDS\start_spectra.cmd
  Same as above, for CMD shell.

- RUN_CMDS\Clean-Install.ps1
  Nukes .venv and reinstalls deps.

- RUN-LOCAL.txt
  Human-readable instructions mirroring the scripts.
