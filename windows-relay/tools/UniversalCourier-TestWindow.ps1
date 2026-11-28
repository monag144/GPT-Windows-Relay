# Visible isolated Windows Forms fixture for real generic-UIA courier validation.
# Never opens, reads, or modifies the user's messaging apps or documents.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$Title,
    [Parameter(Mandatory=$true)][string]$OutputDir,
    [string]$Initial='',
    [switch]$WithSend
)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[System.Windows.Forms.Application]::EnableVisualStyles()
$dir=[IO.Path]::GetFullPath($OutputDir)
[IO.Directory]::CreateDirectory($dir) | Out-Null
$sentPath=Join-Path $dir 'sent.txt'
$editorPath=Join-Path $dir 'final-editor.txt'
$readyPath=Join-Path $dir 'ready.txt'
$clickPath=Join-Path $dir 'clicks.txt'
$form=New-Object System.Windows.Forms.Form
$form.Text=$Title
$form.StartPosition='CenterScreen'
$form.Width=770
$form.Height=200
$form.TopMost=$true
$form.MaximizeBox=$false
$form.MinimizeBox=$false
$entry=New-Object System.Windows.Forms.TextBox
$entry.SetBounds(16,16,690,28)
$entry.AccessibleName='Courier qualification input'
$entry.Text=$Initial
$form.Controls.Add($entry)
$posted=New-Object System.Windows.Forms.Label
$posted.SetBounds(16,96,690,28)
$posted.Text=''
$form.Controls.Add($posted)
$script:clicks=0
if($WithSend){
    $button=New-Object System.Windows.Forms.Button
    $button.SetBounds(16,54,120,32)
    $button.Text='Send'
    $button.AccessibleName='Send'
    $button.Add_Click({
        $script:clicks++
        $value=[string]$entry.Text
        if($value.Length -gt 0){
            [IO.File]::AppendAllText($sentPath,($value+[char]10),
                (New-Object System.Text.UTF8Encoding($false)))
            $posted.Text=$value
            $entry.Clear()
        }
    })
    $form.Controls.Add($button)
}
$form.Add_Shown({
    $form.Activate()
    $form.BringToFront()
    [void]$entry.Focus()
    [IO.File]::WriteAllText($readyPath,'READY')
})
$form.Add_FormClosed({
    [IO.File]::WriteAllText($editorPath,[string]$entry.Text,
        (New-Object System.Text.UTF8Encoding($false)))
    [IO.File]::WriteAllText($clickPath,[string]$script:clicks)
})
[System.Windows.Forms.Application]::Run($form)
