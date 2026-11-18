# Command Courier sign-in shortcut. Current user only, no service or elevation.
# The shortcut always points to the same modular launcher and reads runtime
# selection at launch. Only this exact owned shortcut may be removed/replaced.
[CmdletBinding()]
param(
    [ValidateSet('install','remove','status')][string]$Action='status',
    [Parameter(Mandatory=$true)][string]$LauncherPath
)
$ErrorActionPreference='Stop'
$launcher=[IO.Path]::GetFullPath($LauncherPath)
if(-not(Test-Path -LiteralPath $launcher -PathType Leaf)){
    throw 'COURIER_LAUNCHER_NOT_FOUND'
}
$folder=[Environment]::GetFolderPath([Environment+SpecialFolder]::Startup)
if([string]::IsNullOrWhiteSpace($folder)){throw 'COURIER_USER_STARTUP_FOLDER_UNAVAILABLE'}
$link=Join-Path $folder 'Command Courier.lnk'
$shell=New-Object -ComObject WScript.Shell
if(Test-Path -LiteralPath $link){
    $existing=$shell.CreateShortcut($link)
    $target=[string]$existing.TargetPath
    if([string]::IsNullOrWhiteSpace($target) -or
       [IO.Path]::GetFullPath($target) -ine $launcher){
        throw 'COURIER_STARTUP_FOREIGN_SHORTCUT_REFUSE'
    }
    if($Action -eq 'status'){
        Write-Output 'COURIER_USER_STARTUP=INSTALLED_OWNED'
        exit 0
    }
    if($Action -eq 'remove'){
        Remove-Item -LiteralPath $link -Force -ErrorAction Stop
        Write-Output 'COURIER_USER_STARTUP=REMOVED'
        exit 0
    }
    Write-Output 'COURIER_USER_STARTUP=ALREADY_INSTALLED'
    exit 0
}
if($Action -eq 'status'){
    Write-Output 'COURIER_USER_STARTUP=NOT_INSTALLED'
    exit 0
}
if($Action -eq 'remove'){
    Write-Output 'COURIER_USER_STARTUP=ALREADY_REMOVED'
    exit 0
}
# Startup registration is explicitly opt-in. It does not launch now.
$shortcut=$shell.CreateShortcut($link)
$shortcut.TargetPath=$launcher
$shortcut.Arguments='start'
$shortcut.WorkingDirectory=[IO.Path]::GetDirectoryName($launcher)
$shortcut.Description='Command Courier - linked relay and HUD (current user, runtime selected at sign-in)'
$shortcut.WindowStyle=7
$shortcut.Save()
$verify=$shell.CreateShortcut($link)
if([IO.Path]::GetFullPath([string]$verify.TargetPath) -ine $launcher){
    throw 'COURIER_STARTUP_LINK_VERIFICATION_FAILED'
}
Write-Output 'COURIER_USER_STARTUP=INSTALLED_OWNED'
Write-Output 'COURIER_STARTUP_EVENT=WINDOWS_INTERACTIVE_USER_SIGN_IN'
