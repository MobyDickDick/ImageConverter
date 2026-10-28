# Invoked by the local GUI with paths passed through its child-process environment.
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
Add-Type -AssemblyName System.Windows.Forms
$dialog = New-Object System.Windows.Forms.SaveFileDialog
$owner = New-Object System.Windows.Forms.Form
try {
    $dialog.Title = 'SVG speichern unter'
    $dialog.Filter = 'SVG-Vektorgrafik (*.svg)|*.svg'
    $dialog.DefaultExt = 'svg'
    $dialog.AddExtension = $true
    $dialog.OverwritePrompt = $true
    $dialog.FileName = $env:ICC_GUI_FILENAME
    $dialog.RestoreDirectory = $true
    $owner.ShowInTaskbar = $false
    $owner.TopMost = $true
    $owner.Opacity = 0
    $owner.Show()
    $owner.Activate()
    if ($dialog.ShowDialog($owner) -eq [System.Windows.Forms.DialogResult]::OK) {
        Copy-Item -LiteralPath $env:ICC_GUI_SOURCE -Destination $dialog.FileName -Force
        @{ saved = $true; path = $dialog.FileName } | ConvertTo-Json -Compress
    } else {
        @{ saved = $false } | ConvertTo-Json -Compress
    }
} catch {
    @{ error = $_.Exception.Message } | ConvertTo-Json -Compress
    exit 1
} finally {
    $dialog.Dispose()
    $owner.Dispose()
}
