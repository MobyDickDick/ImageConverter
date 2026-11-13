# Only the server supplies the picker kind and remembered directory.
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
Add-Type -AssemblyName System.Windows.Forms
$dialog = New-Object System.Windows.Forms.OpenFileDialog
$owner = New-Object System.Windows.Forms.Form
try {
    if ($env:ICC_GUI_PICKER_KIND -eq 'image') {
        $dialog.Title = 'Rasterbild auswählen'
        $dialog.Filter = 'Rasterbilder (*.png;*.jpg;*.jpeg;*.bmp;*.webp;*.tif;*.tiff)|*.png;*.jpg;*.jpeg;*.bmp;*.webp;*.tif;*.tiff'
    } else {
        $dialog.Title = if ($env:ICC_GUI_PICKER_KIND -eq 'sample') { 'Sample-SVG auswählen' } else { 'Plan-B-Referenz auswählen' }
        $dialog.Filter = 'SVG-Vektorgrafik (*.svg)|*.svg'
    }
    $dialog.CheckFileExists = $true
    $dialog.Multiselect = $false
    $dialog.RestoreDirectory = $true
    if ($env:ICC_GUI_INITIAL_DIRECTORY -and (Test-Path -LiteralPath $env:ICC_GUI_INITIAL_DIRECTORY -PathType Container)) {
        $dialog.InitialDirectory = $env:ICC_GUI_INITIAL_DIRECTORY
    }
    $owner.ShowInTaskbar = $false
    $owner.TopMost = $true
    $owner.Opacity = 0
    $owner.Show()
    $owner.Activate()
    if ($dialog.ShowDialog($owner) -eq [System.Windows.Forms.DialogResult]::OK) {
        @{ selected = $true; path = $dialog.FileName } | ConvertTo-Json -Compress
    } else {
        @{ selected = $false } | ConvertTo-Json -Compress
    }
} catch {
    @{ error = $_.Exception.Message } | ConvertTo-Json -Compress
    exit 1
} finally {
    $dialog.Dispose()
    $owner.Dispose()
}
