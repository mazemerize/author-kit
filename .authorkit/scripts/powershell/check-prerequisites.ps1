#!/usr/bin/env pwsh

# Consolidated prerequisite checking script for Author Kit
#
# Usage: ./check-prerequisites.ps1 [OPTIONS]
#
# OPTIONS:
#   -Json               Output in JSON format
#   -RequireChapters    Require chapters.md to exist (for drafting phase)
#   -IncludeChapters    Include chapters.md in AVAILABLE_DOCS list
#   -PathsOnly          Only output path variables (no validation)
#   -Help               Show help message

[CmdletBinding()]
param(
    [switch]$Json,
    [switch]$RequireChapters,
    [switch]$IncludeChapters,
    [switch]$PathsOnly,
    [switch]$Help
)

$ErrorActionPreference = 'Stop'

# Show help if requested
if ($Help) {
    Write-Output @"
Usage: check-prerequisites.ps1 [OPTIONS]

Consolidated prerequisite checking for Author Kit workflow.

OPTIONS:
  -Json               Output in JSON format
  -RequireChapters    Require chapters.md to exist (for drafting phase)
  -IncludeChapters    Include chapters.md in AVAILABLE_DOCS list
  -PathsOnly          Only output path variables (no prerequisite validation)
  -Help               Show this help message

EXAMPLES:
  # Check outline prerequisites (concept.md required)
  .\check-prerequisites.ps1 -Json

  # Check drafting prerequisites (concept.md + chapters.md required)
  .\check-prerequisites.ps1 -Json -RequireChapters -IncludeChapters

  # Get book paths only (no validation)
  .\check-prerequisites.ps1 -PathsOnly

"@
    exit 0
}

# Source common functions
. "$PSScriptRoot/common.ps1"

# Get canonical book paths
$paths = Get-BookPaths

# If paths-only mode, output paths and exit
if ($PathsOnly) {
    if ($Json) {
        [PSCustomObject]@{
            REPO_ROOT    = $paths.REPO_ROOT
            BOOK_DIR     = $paths.BOOK_DIR
            BOOK_CONCEPT = $paths.BOOK_CONCEPT
            STYLE_ANCHOR = $paths.STYLE_ANCHOR
            OUTLINE      = $paths.OUTLINE
            CHAPTERS     = $paths.CHAPTERS
        } | ConvertTo-Json -Compress
    } else {
        Write-Output "REPO_ROOT: $($paths.REPO_ROOT)"
        Write-Output "BOOK_DIR: $($paths.BOOK_DIR)"
        Write-Output "BOOK_CONCEPT: $($paths.BOOK_CONCEPT)"
        Write-Output "STYLE_ANCHOR: $($paths.STYLE_ANCHOR)"
        Write-Output "OUTLINE: $($paths.OUTLINE)"
        Write-Output "CHAPTERS: $($paths.CHAPTERS)"
    }
    exit 0
}

# Validate required directories and files
if (-not (Test-Path $paths.BOOK_DIR -PathType Container)) {
    Write-Output "ERROR: Book directory not found: $($paths.BOOK_DIR)"
    Write-Output "Run /authorkit.conceive first to create the book structure."
    exit 1
}

if (-not (Test-Path $paths.OUTLINE -PathType Leaf)) {
    Write-Output "ERROR: outline.md not found in $($paths.BOOK_DIR)"
    Write-Output "Run /authorkit.outline first to create the book outline."
    exit 1
}

# Check for chapters.md if required
if ($RequireChapters -and -not (Test-Path $paths.CHAPTERS -PathType Leaf)) {
    Write-Output "ERROR: chapters.md not found in $($paths.BOOK_DIR)"
    Write-Output "Run /authorkit.chapters first to create the chapter breakdown."
    exit 1
}

# Build list of available documents
$docs = @()

# Always check these optional docs
if (Test-Path $paths.RESEARCH) { $docs += 'research.md' }
if (Test-Path $paths.CHARACTERS) { $docs += 'characters.md' }

# Check chapters directory (only if it exists and has subdirectories)
if ((Test-Path $paths.CHAPTERS_DIR) -and (Get-ChildItem -Path $paths.CHAPTERS_DIR -Directory -ErrorAction SilentlyContinue | Select-Object -First 1)) {
    $docs += 'chapters/'
}

# Include chapters.md if requested and it exists
if ($IncludeChapters -and (Test-Path $paths.CHAPTERS)) {
    $docs += 'chapters.md'
}

# Output results
if ($Json) {
    [PSCustomObject]@{
        BOOK_DIR       = $paths.BOOK_DIR
        STYLE_ANCHOR   = $paths.STYLE_ANCHOR
        AVAILABLE_DOCS = $docs
    } | ConvertTo-Json -Compress
} else {
    Write-Output "BOOK_DIR:$($paths.BOOK_DIR)"
    Write-Output "STYLE_ANCHOR:$($paths.STYLE_ANCHOR)"
    Write-Output "AVAILABLE_DOCS:"

    Test-FileExists -Path $paths.RESEARCH -Description 'research.md' | Out-Null
    Test-FileExists -Path $paths.CHARACTERS -Description 'characters.md' | Out-Null
    Test-DirHasFiles -Path $paths.CHAPTERS_DIR -Description 'chapters/' | Out-Null

    if ($IncludeChapters) {
        Test-FileExists -Path $paths.CHAPTERS -Description 'chapters.md' | Out-Null
    }
}
