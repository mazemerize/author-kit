#!/usr/bin/env pwsh
# Common PowerShell functions for Author Kit

# Canonical book directory names (lowercase).
$AUTHORKIT_BOOK_DIR = 'book'
$AUTHORKIT_WORLD_DIR = 'world'
$AUTHORKIT_CHAPTERS_DIR = 'chapters'
$AUTHORKIT_DIST_DIR = 'dist'

function Get-RepoRoot {
    try {
        $result = git rev-parse --show-toplevel 2>$null
        if ($LASTEXITCODE -eq 0) {
            return $result
        }
    } catch {
        # Git command failed
    }

    # Fall back to script location for non-git repos
    return (Resolve-Path (Join-Path $PSScriptRoot "../../..")).Path
}

function Get-CurrentBranch {
    try {
        $result = git rev-parse --abbrev-ref HEAD 2>$null
        if ($LASTEXITCODE -eq 0) {
            $name = $result.Trim()
            if ($name) {
                return $name
            }
        }
    } catch {
        # Git command failed
    }
    return "main"
}

function Test-HasGit {
    try {
        git rev-parse --show-toplevel 2>$null | Out-Null
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    }
}

function Get-BookDir {
    param([string]$RepoRoot)
    Join-Path $RepoRoot $AUTHORKIT_BOOK_DIR
}

function Get-BookPaths {
    $repoRoot = Get-RepoRoot
    $currentBranch = Get-CurrentBranch
    $hasGit = Test-HasGit
    $bookDir = Get-BookDir -RepoRoot $repoRoot

    [PSCustomObject]@{
        REPO_ROOT      = $repoRoot
        CURRENT_BRANCH = $currentBranch
        HAS_GIT        = $hasGit
        BOOK_DIR       = $bookDir
        BOOK_CONCEPT   = Join-Path $bookDir 'concept.md'
        STYLE_ANCHOR   = Join-Path $bookDir 'style-anchor.md'
        OUTLINE        = Join-Path $bookDir 'outline.md'
        CHAPTERS       = Join-Path $bookDir 'chapters.md'
        RESEARCH       = Join-Path $bookDir 'research.md'
        CHARACTERS     = Join-Path $bookDir 'characters.md'
        WORLD_DIR      = Join-Path $bookDir $AUTHORKIT_WORLD_DIR
        CHAPTERS_DIR   = Join-Path $bookDir $AUTHORKIT_CHAPTERS_DIR
        DIST_DIR       = Join-Path $bookDir $AUTHORKIT_DIST_DIR
    }
}

function Get-BookPathsJson {
    $paths = Get-BookPaths
    [PSCustomObject]@{
        REPO_ROOT    = $paths.REPO_ROOT
        BOOK_DIR     = $paths.BOOK_DIR
        BOOK_CONCEPT = $paths.BOOK_CONCEPT
        STYLE_ANCHOR = $paths.STYLE_ANCHOR
        OUTLINE      = $paths.OUTLINE
        CHAPTERS     = $paths.CHAPTERS
        HAS_GIT      = $paths.HAS_GIT
    } | ConvertTo-Json -Compress
}

function Test-FileExists {
    param([string]$Path, [string]$Description)
    if (Test-Path -Path $Path -PathType Leaf) {
        Write-Output "  + $Description"
        return $true
    } else {
        Write-Output "  - $Description"
        return $false
    }
}

function Test-DirHasFiles {
    param([string]$Path, [string]$Description)
    if ((Test-Path -Path $Path -PathType Container) -and (Get-ChildItem -Path $Path -ErrorAction SilentlyContinue | Where-Object { -not $_.PSIsContainer } | Select-Object -First 1)) {
        Write-Output "  + $Description"
        return $true
    } else {
        Write-Output "  - $Description"
        return $false
    }
}
