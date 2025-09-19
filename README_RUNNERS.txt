# Runners & Launchers

Use these from C:\Code\spectra-app\

- RUN_CMDS\Start-Spectra.ps1
  Boots the app consistently. Accepts -Port if you need a different port.

- RUN_CMDS\start_spectra.cmd
  Same as above, for plain CMD shells.

- RUN_CMDS\Clean-Install.ps1
  Nukes the venv and reinstalls dependencies (use if your env gets weird).

- RUN_CMDS\Verify-Project.ps1
  Checks critical files exist, confirms version info can be read, and prints the first lines of the longform patch notes if found.

- RUN-LOCAL.txt
  Human-readable instructions mirroring the scripts.
