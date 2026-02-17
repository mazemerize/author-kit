#!/usr/bin/env pwsh
# Setup book outline artifacts

[CmdletBinding()]
param(
    [switch]$Json,
    [switch]$Help
)

$ErrorActionPreference = 'Stop'

# Show help if requested
if ($Help) {
    Write-Output "Usage: ./setup-outline.ps1 [-Json] [-Help]"
    Write-Output "  -Json     Output results in JSON format"
    Write-Output "  -Help     Show this help message"
    exit 0
}

# Load common functions
. "$PSScriptRoot/common.ps1"

# Get all paths and variables from common functions
$paths = Get-BookPaths

# Ensure the book directory exists
New-Item -ItemType Directory -Path $paths.BOOK_DIR -Force | Out-Null

# Copy outline template if it exists
$template = Join-Path $paths.REPO_ROOT '.authorkit/templates/outline-template.md'
if (Test-Path $template) {
    Copy-Item $template $paths.OUTLINE -Force
    Write-Output "Copied outline template to $($paths.OUTLINE)"
} else {
    Write-Warning "Outline template not found at $template"
    New-Item -ItemType File -Path $paths.OUTLINE -Force | Out-Null
}

# Ensure chapters directory exists
New-Item -ItemType Directory -Path $paths.CHAPTERS_DIR -Force | Out-Null

# Output results
if ($Json) {
    $result = [PSCustomObject]@{
        BOOK_CONCEPT = $paths.BOOK_CONCEPT
        OUTLINE      = $paths.OUTLINE
        BOOK_DIR     = $paths.BOOK_DIR
        CHAPTERS_DIR = $paths.CHAPTERS_DIR
        HAS_GIT      = $paths.HAS_GIT
    }
    $result | ConvertTo-Json -Compress
} else {
    Write-Output "BOOK_CONCEPT: $($paths.BOOK_CONCEPT)"
    Write-Output "OUTLINE: $($paths.OUTLINE)"
    Write-Output "BOOK_DIR: $($paths.BOOK_DIR)"
    Write-Output "CHAPTERS_DIR: $($paths.CHAPTERS_DIR)"
    Write-Output "HAS_GIT: $($paths.HAS_GIT)"
}
