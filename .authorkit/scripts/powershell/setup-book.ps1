#!/usr/bin/env pwsh
# Setup or refresh the canonical single-book workspace.
[CmdletBinding()]
param(
    [switch]$Json,
    [string]$Title,
    [string]$Author,
    [string]$Language,
    [switch]$Help
)
$ErrorActionPreference = 'Stop'

if ($Help) {
    Write-Host "Usage: ./setup-book.ps1 [-Json] [-Title <title>] [-Author <author>] [-Language <language>]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Json             Output in JSON format"
    Write-Host "  -Title <title>    Set or override title in book.toml"
    Write-Host "  -Author <author>  Set or override author in book.toml"
    Write-Host "  -Language <lang>  Set or override language (default: en-US)"
    Write-Host "  -Help             Show this help message"
    exit 0
}

. "$PSScriptRoot/common.ps1"

function Read-ExistingTomlValue {
    param(
        [string]$Path,
        [string]$Key
    )
    if (-not (Test-Path $Path -PathType Leaf)) {
        return $null
    }
    $content = Get-Content -Path $Path -Raw -Encoding UTF8
    if ($content -match "(?m)^$Key\s*=\s*""([^""]*)""\s*$") {
        return $matches[1]
    }
    return $null
}

function Read-MetadataValue {
    param(
        [string]$Label,
        [string]$DefaultValue
    )
    $inputValue = Read-Host "$Label [$DefaultValue]"
    if ([string]::IsNullOrWhiteSpace($inputValue)) {
        return $DefaultValue
    }
    return $inputValue.Trim()
}

$paths = Get-BookPaths
Set-Location $paths.REPO_ROOT

$bookDir = $paths.BOOK_DIR
$chaptersDir = $paths.CHAPTERS_DIR
$conceptFile = $paths.BOOK_CONCEPT
$bookTomlPath = Join-Path $bookDir 'book.toml'

New-Item -ItemType Directory -Path $bookDir -Force | Out-Null
New-Item -ItemType Directory -Path $chaptersDir -Force | Out-Null

$template = Join-Path $paths.REPO_ROOT '.authorkit/templates/concept-template.md'
if ((Test-Path $template) -and (-not (Test-Path $conceptFile -PathType Leaf))) {
    Copy-Item $template $conceptFile -Force
} elseif (-not (Test-Path $conceptFile -PathType Leaf)) {
    New-Item -ItemType File -Path $conceptFile -Force | Out-Null
}

$existingTitle = Read-ExistingTomlValue -Path $bookTomlPath -Key 'title'
$existingAuthor = Read-ExistingTomlValue -Path $bookTomlPath -Key 'author'
$existingLanguage = Read-ExistingTomlValue -Path $bookTomlPath -Key 'language'

$defaultTitle = if ($existingTitle) { $existingTitle } else { 'Untitled Book' }
$defaultAuthor = if ($existingAuthor) { $existingAuthor } else { 'Unknown Author' }
$defaultLanguage = if ($existingLanguage) { $existingLanguage } else { 'en-US' }

if ($Json) {
    $bookTitle = if ([string]::IsNullOrWhiteSpace($Title)) { $defaultTitle } else { $Title.Trim() }
    $bookAuthor = if ([string]::IsNullOrWhiteSpace($Author)) { $defaultAuthor } else { $Author.Trim() }
    $bookLanguage = if ([string]::IsNullOrWhiteSpace($Language)) { $defaultLanguage } else { $Language.Trim() }
} else {
    Write-Output "Initialize book metadata (book.toml):"
    $bookTitle = if ([string]::IsNullOrWhiteSpace($Title)) { Read-MetadataValue -Label 'Title' -DefaultValue $defaultTitle } else { $Title.Trim() }
    $bookAuthor = if ([string]::IsNullOrWhiteSpace($Author)) { Read-MetadataValue -Label 'Author' -DefaultValue $defaultAuthor } else { $Author.Trim() }
    $bookLanguage = if ([string]::IsNullOrWhiteSpace($Language)) { Read-MetadataValue -Label 'Language' -DefaultValue $defaultLanguage } else { $Language.Trim() }
}

$bookToml = @"
[book]
title = "$bookTitle"
author = "$bookAuthor"
language = "$bookLanguage"
subtitle = ""

[build]
default_formats = ["docx"]
reference_docx = ".authorkit/templates/publishing/reference.docx"
epub_css = ".authorkit/templates/publishing/epub.css"

[audio]
provider = "openai"
model = "gpt-4o-mini-tts"
voice = "onyx"
speaking_rate_wpm = 170

[stats]
reading_wpm = 200
tts_cost_per_1m_chars = 0.0
"@

Set-Content -Path $bookTomlPath -Value $bookToml -Encoding UTF8 -NoNewline

if ($Json) {
    $obj = [PSCustomObject]@{
        BOOK_DIR     = $bookDir
        CONCEPT_FILE = $conceptFile
        BOOK_TOML    = $bookTomlPath
        HAS_GIT      = $paths.HAS_GIT
    }
    $obj | ConvertTo-Json -Compress
} else {
    Write-Output "BOOK_DIR: $bookDir"
    Write-Output "CONCEPT_FILE: $conceptFile"
    Write-Output "BOOK_TOML: $bookTomlPath"
    Write-Output "HAS_GIT: $($paths.HAS_GIT)"
}
