#!/usr/bin/env pwsh
# Setup or refresh the canonical single-book workspace.
[CmdletBinding()]
param(
    [switch]$Json,
    [string]$Title,
    [string]$Author,
    [string]$Subtitle,
    [string]$Language,
    [switch]$Help
)
$ErrorActionPreference = 'Stop'

if ($Help) {
    Write-Host "Usage: ./setup-book.ps1 [-Json] [-Title <title>] [-Author <author>] [-Subtitle <subtitle>] [-Language <language>]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Json                 Output in JSON format"
    Write-Host "  -Title <title>        Set or override title in book.toml"
    Write-Host "  -Author <author>      Set or override author in book.toml"
    Write-Host "  -Subtitle <subtitle>  Set or override subtitle in book.toml"
    Write-Host "  -Language <lang>      Set or override language (default: en-US)"
    Write-Host "  -Help                 Show this help message"
    exit 0
}

. "$PSScriptRoot/common.ps1"

# PSBoundParameters is the canonical way in PowerShell to detect "was this
# parameter explicitly passed?" — distinct from "is its value non-empty?".
# A user passing `-Subtitle ""` is a legitimate intent to clear, not a no-op.
$titleSet = $PSBoundParameters.ContainsKey('Title')
$authorSet = $PSBoundParameters.ContainsKey('Author')
$subtitleSet = $PSBoundParameters.ContainsKey('Subtitle')
$languageSet = $PSBoundParameters.ContainsKey('Language')

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

function Write-Utf8NoBom {
    param(
        [string]$Path,
        [string]$Content
    )
    $utf8NoBom = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText($Path, $Content, $utf8NoBom)
}

function Set-BookStringField {
    # Replace `key = "..."` for a top-level [book] string key, in place. Leaves
    # the rest of the file (other sections, comments, custom keys) untouched.
    param(
        [string]$Path,
        [string]$Key,
        [string]$Value
    )
    if (-not (Test-Path $Path -PathType Leaf)) { return }
    $content = Get-Content -Path $Path -Raw -Encoding UTF8
    $pattern = "(?m)^$([regex]::Escape($Key))\s*=\s*""[^""]*""\s*$"
    if ($content -notmatch $pattern) { return }
    $escaped = $Value -replace '\\', '\\' -replace '"', '\"'
    $replacement = "$Key = `"$escaped`""
    $newContent = [regex]::Replace($content, $pattern, $replacement, 1)
    Write-Utf8NoBom -Path $Path -Content $newContent
}

$paths = Get-BookPaths
Set-Location $paths.REPO_ROOT

$bookDir = $paths.BOOK_DIR
$chaptersDir = $paths.CHAPTERS_DIR
$conceptFile = $paths.BOOK_CONCEPT
$styleAnchorFile = $paths.STYLE_ANCHOR
$bookTomlPath = Join-Path $bookDir 'book.toml'

New-Item -ItemType Directory -Path $bookDir -Force | Out-Null
New-Item -ItemType Directory -Path $chaptersDir -Force | Out-Null

$template = Join-Path $paths.REPO_ROOT '.authorkit/templates/concept-template.md'
if ((Test-Path $template) -and (-not (Test-Path $conceptFile -PathType Leaf))) {
    Copy-Item $template $conceptFile -Force
} elseif (-not (Test-Path $conceptFile -PathType Leaf)) {
    New-Item -ItemType File -Path $conceptFile -Force | Out-Null
}

$styleTemplate = Join-Path $paths.REPO_ROOT '.authorkit/templates/style-anchor-template.md'
if ((Test-Path $styleTemplate) -and (-not (Test-Path $styleAnchorFile -PathType Leaf))) {
    Copy-Item $styleTemplate $styleAnchorFile -Force
} elseif (-not (Test-Path $styleAnchorFile -PathType Leaf)) {
    New-Item -ItemType File -Path $styleAnchorFile -Force | Out-Null
}

$existingTitle = Read-ExistingTomlValue -Path $bookTomlPath -Key 'title'
$existingAuthor = Read-ExistingTomlValue -Path $bookTomlPath -Key 'author'
$existingSubtitle = Read-ExistingTomlValue -Path $bookTomlPath -Key 'subtitle'
$existingLanguage = Read-ExistingTomlValue -Path $bookTomlPath -Key 'language'

$defaultTitle = if ($existingTitle) { $existingTitle } else { 'Untitled Book' }
$defaultAuthor = if ($existingAuthor) { $existingAuthor } else { 'Unknown Author' }
$defaultSubtitle = if ($existingSubtitle) { $existingSubtitle } else { '' }
$defaultLanguage = if ($existingLanguage) { $existingLanguage } else { 'en-US' }

if (-not (Test-Path $bookTomlPath -PathType Leaf)) {
    # Fresh install: write the full template. `tts_cost_per_1m_chars` ships
    # commented out so users opt in (see README "Book Export"). All other
    # fields have safe defaults that book_core.parse_book_config tolerates.
    if ($Json) {
        $bookTitle = if ($titleSet) { $Title.Trim() } else { $defaultTitle }
        $bookAuthor = if ($authorSet) { $Author.Trim() } else { $defaultAuthor }
        $bookSubtitle = if ($subtitleSet) { $Subtitle.Trim() } else { $defaultSubtitle }
        $bookLanguage = if ($languageSet) { $Language.Trim() } else { $defaultLanguage }
    } else {
        Write-Output "Initialize book metadata (book.toml):"
        $bookTitle = if ($titleSet) { $Title.Trim() } else { Read-MetadataValue -Label 'Title' -DefaultValue $defaultTitle }
        $bookAuthor = if ($authorSet) { $Author.Trim() } else { Read-MetadataValue -Label 'Author' -DefaultValue $defaultAuthor }
        $bookSubtitle = if ($subtitleSet) { $Subtitle.Trim() } else { Read-MetadataValue -Label 'Subtitle' -DefaultValue $defaultSubtitle }
        $bookLanguage = if ($languageSet) { $Language.Trim() } else { Read-MetadataValue -Label 'Language' -DefaultValue $defaultLanguage }
    }

    $bookToml = @"
[book]
title = "$bookTitle"
author = "$bookAuthor"
language = "$bookLanguage"
subtitle = "$bookSubtitle"

[build]
default_formats = ["docx"]
reference_docx = ".authorkit/templates/publishing/reference.docx"
epub_css = ".authorkit/templates/publishing/epub.css"

[audio]
provider = "openai"
model = "gpt-4o-mini-tts"
voice = "marin"
instructions = ".authorkit/templates/publishing/audio-instructions.txt"
speaking_rate_wpm = 170

[stats]
reading_wpm = 200
# tts_cost_per_1m_chars = 0.000015   # uncomment and set to enable cost estimates in `authorkit book stats`
"@

    Write-Utf8NoBom -Path $bookTomlPath -Content $bookToml
} else {
    # File exists — preserve all user customizations. Only update the four
    # [book] string fields, and only when the corresponding parameter was
    # explicitly bound (JSON mode) or the user typed a new value at the
    # prompt (interactive mode).
    if ($Json) {
        if ($titleSet) { Set-BookStringField -Path $bookTomlPath -Key 'title' -Value $Title.Trim() }
        if ($authorSet) { Set-BookStringField -Path $bookTomlPath -Key 'author' -Value $Author.Trim() }
        if ($subtitleSet) { Set-BookStringField -Path $bookTomlPath -Key 'subtitle' -Value $Subtitle.Trim() }
        if ($languageSet) { Set-BookStringField -Path $bookTomlPath -Key 'language' -Value $Language.Trim() }
    } else {
        Write-Output "Update book metadata (book.toml):"
        if ($titleSet) {
            Set-BookStringField -Path $bookTomlPath -Key 'title' -Value $Title.Trim()
        } else {
            $entered = Read-Host "Title [$defaultTitle]"
            if (-not [string]::IsNullOrWhiteSpace($entered) -and $entered.Trim() -ne $defaultTitle) {
                Set-BookStringField -Path $bookTomlPath -Key 'title' -Value $entered.Trim()
            }
        }
        if ($authorSet) {
            Set-BookStringField -Path $bookTomlPath -Key 'author' -Value $Author.Trim()
        } else {
            $entered = Read-Host "Author [$defaultAuthor]"
            if (-not [string]::IsNullOrWhiteSpace($entered) -and $entered.Trim() -ne $defaultAuthor) {
                Set-BookStringField -Path $bookTomlPath -Key 'author' -Value $entered.Trim()
            }
        }
        if ($subtitleSet) {
            Set-BookStringField -Path $bookTomlPath -Key 'subtitle' -Value $Subtitle.Trim()
        } else {
            $entered = Read-Host "Subtitle [$defaultSubtitle]"
            if (-not [string]::IsNullOrWhiteSpace($entered) -and $entered.Trim() -ne $defaultSubtitle) {
                Set-BookStringField -Path $bookTomlPath -Key 'subtitle' -Value $entered.Trim()
            }
        }
        if ($languageSet) {
            Set-BookStringField -Path $bookTomlPath -Key 'language' -Value $Language.Trim()
        } else {
            $entered = Read-Host "Language [$defaultLanguage]"
            if (-not [string]::IsNullOrWhiteSpace($entered) -and $entered.Trim() -ne $defaultLanguage) {
                Set-BookStringField -Path $bookTomlPath -Key 'language' -Value $entered.Trim()
            }
        }
    }
}

if ($Json) {
    $obj = [PSCustomObject]@{
        BOOK_DIR     = $bookDir
        CONCEPT_FILE = $conceptFile
        STYLE_ANCHOR = $styleAnchorFile
        BOOK_TOML    = $bookTomlPath
        HAS_GIT      = $paths.HAS_GIT
    }
    $obj | ConvertTo-Json -Compress
} else {
    Write-Output "BOOK_DIR: $bookDir"
    Write-Output "CONCEPT_FILE: $conceptFile"
    Write-Output "STYLE_ANCHOR: $styleAnchorFile"
    Write-Output "BOOK_TOML: $bookTomlPath"
    Write-Output "HAS_GIT: $($paths.HAS_GIT)"
}
