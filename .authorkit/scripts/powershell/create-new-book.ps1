#!/usr/bin/env pwsh
# Deprecated compatibility shim. Use setup-book.ps1 instead.
[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Arguments
)
$ErrorActionPreference = 'Stop'

$target = Join-Path $PSScriptRoot 'setup-book.ps1'
if (-not (Test-Path $target -PathType Leaf)) {
    Write-Error "Missing setup script: $target"
    exit 1
}

Write-Warning "[authorkit] create-new-book.ps1 is deprecated. Use setup-book.ps1."

$forward = @()
$expectsValue = $false
foreach ($arg in $Arguments) {
    if ($expectsValue) {
        $forward += $arg
        $expectsValue = $false
        continue
    }

    switch -Regex ($arg) {
        '^-Json$|^--json$|^-Help$|^--help$' {
            $forward += $arg
            continue
        }
        '^-Title$|^--title$|^-Author$|^--author$|^-Language$|^--language$' {
            $forward += $arg
            $expectsValue = $true
            continue
        }
        default {
            # Ignore legacy positional description and removed options.
            continue
        }
    }
}

& $target @forward
exit $LASTEXITCODE
