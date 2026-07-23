# Developer Platform 1.0 – Integrationspaket

1. ZIP im Repository-Root entpacken.
2. `.gitignore.additions` in die vorhandene `.gitignore` übernehmen.
3. `powerplatform/scripts/DeveloperPlatform.psd1` prüfen.
4. `pwsh ./powerplatform/scripts/Validate.ps1` ausführen.
5. `pwsh ./powerplatform/scripts/Build.ps1` ausführen.

Das Paket enthält produktive Skripte und ersetzt die bisherigen drei Build-/Pack-Skripte durch kompatible, erweiterte Versionen.
