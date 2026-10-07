<#
refresh_toc.ps1 - fill in a .docx table of contents and its page numbers.

md2docx.py only writes a TOC field. Word is what computes the entries and the page
numbers, so without this step the reader opens the file to an empty contents page and
has to press F9. Run it once before handing the document over.

    powershell -ExecutionPolicy Bypass -File refresh_toc.ps1

With no argument it refreshes the file named below, next to this script. Pass -File
to point it somewhere else. Word is started hidden and closed again. Close the file
first if it is open in Word or WPS, otherwise saving fails on a lock.

This is a document build tool, not part of the data pipeline. It needs no pywin32.
#>
param([string[]]$File)

# Locate the document by an ASCII pattern so the script itself stays pure ASCII:
# PowerShell 5.1 reads a BOM-less UTF-8 script as ANSI, which would mangle any
# non-ASCII path written here.
if (-not $File -or $File.Count -eq 0) {
    $found = Get-ChildItem -Path $PSScriptRoot -Recurse -Filter '*Research_Plan_EN.docx' `
        -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($found) { $File = @($found.FullName) }
    else { Write-Output 'no docx found next to this script'; exit 0 }
}

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$ok = $true
foreach ($path in $File) {
    if (-not (Test-Path $path)) { Write-Output ('missing: ' + $path); $ok = $false; continue }
    $doc = $null
    try {
        $doc = $word.Documents.Open($path)
        $doc.Fields.Update() | Out-Null
        $n = $doc.TablesOfContents.Count
        for ($i = 1; $i -le $n; $i++) { $doc.TablesOfContents($i).Update() }
        $doc.Save()
        Write-Output ('refreshed TOC x' + $n + ' in ' + (Split-Path $path -Leaf))
    } catch {
        Write-Output ('failed: ' + (Split-Path $path -Leaf) + ' :: ' + $_.Exception.Message)
        $ok = $false
    } finally {
        if ($doc) { $doc.Close(0) }
    }
}
$word.Quit()
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
if ($ok) { Write-Output 'done' } else { Write-Output 'some files failed' }
