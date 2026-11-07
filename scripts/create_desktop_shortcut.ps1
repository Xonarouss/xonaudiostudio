# Create Windows Desktop Shortcut for XonAudio Studio
$scriptRoot = Split-Path -Parent $PSScriptRoot
if (-not $scriptRoot) { $scriptRoot = "D:\TTS + Effects" }

$TargetBat = Join-Path $scriptRoot "Start_AudioStudio.bat"
$IconPath = Join-Path $scriptRoot "assets\icon.ico"

try {
    $desktopPath = [Environment]::GetFolderPath("Desktop")
    $shortcutPath = Join-Path $desktopPath "XonAudio Studio.lnk"

    $wshShell = New-Object -ComObject WScript.Shell
    $shortcut = $wshShell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = $TargetBat
    $shortcut.WorkingDirectory = $scriptRoot
    $shortcut.IconLocation = "$IconPath,0"
    $shortcut.Description = "XonAudio Studio - AI Voice Cloning & Sound Effects by Xonarous Inc"
    $shortcut.WindowStyle = 1
    $shortcut.Save()

    Write-Host ""
    Write-Host "=====================================================================" -ForegroundColor Green
    Write-Host "[+] Bureaubladsnelkoppeling succesvol aangemaakt met het XonAudio logo!" -ForegroundColor Green
    Write-Host "    Locatie: $shortcutPath" -ForegroundColor Cyan
    Write-Host "=====================================================================" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host ""
    Write-Host "[!] Kon snelkoppeling op Desktop niet direct opslaan: $_" -ForegroundColor Yellow
    Write-Host "    Tip: Je kunt altijd rechtsklikken op Start_AudioStudio.bat -> Kopiëren naar -> Bureaublad (snelkoppeling maken)" -ForegroundColor Gray
}
