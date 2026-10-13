param(
  [string]$RelayRoot = ''
)
$ErrorActionPreference='Stop'
# Windows Relay browser repair entrypoint retired 2026-10-12.
# No local backups; no secondary Client tree or consumer extension mutations.
# Only the operator-selected canonical extension-persistent manifest is supported.
throw 'RETIRED_NO_LOCAL_BACKUPS: install-browser-fix.ps1 is obsolete. Use the canonical extension-persistent in Main-Build; do not create local backups.'
