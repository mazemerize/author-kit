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

function Get-BookLanguage {
    # The book's prose language, from book/book.toml `[book] language`. Same
    # extraction as setup-book.ps1's Read-ExistingTomlValue (that script owns
    # writing the field; this one only reports it). Missing file or key means
    # en-US, which keeps every project created before the field mattered
    # behaving as before.
    param([string]$BookDir)
    $bookToml = Join-Path $BookDir 'book.toml'
    if (Test-Path -Path $bookToml -PathType Leaf) {
        $content = Get-Content -Path $bookToml -Raw -Encoding UTF8
        if ($content -match '(?m)^language\s*=\s*"([^"]*)"\s*$') {
            $value = $matches[1].Trim()
            if ($value) { return $value }
        }
    }
    return 'en-US'
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
        BOOK_LANGUAGE  = Get-BookLanguage -BookDir $bookDir
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
        REPO_ROOT     = $paths.REPO_ROOT
        BOOK_DIR      = $paths.BOOK_DIR
        BOOK_LANGUAGE = $paths.BOOK_LANGUAGE
        BOOK_CONCEPT  = $paths.BOOK_CONCEPT
        STYLE_ANCHOR  = $paths.STYLE_ANCHOR
        OUTLINE       = $paths.OUTLINE
        CHAPTERS      = $paths.CHAPTERS
        HAS_GIT       = $paths.HAS_GIT
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

function Test-DirHasChapterSubdirs {
    # Only pure-numeric chapter folders (e.g. 01, 02) that contain a draft.md
    # count as drafted chapters, mirroring the CLI's discover_chapter_drafts
    # convention (book/chapters/NN/draft.md) so backups like `01-old/` or an
    # empty `01/` don't make the dir look populated when build/stats/status
    # would find nothing. The ASCII [0-9] class matches the bash flavor (.NET
    # \d would also accept non-ASCII Unicode digits).
    param([string]$Path)
    if (-not (Test-Path -Path $Path -PathType Container)) { return $false }
    return [bool](Get-ChildItem -Path $Path -Directory -ErrorAction SilentlyContinue |
        Where-Object {
            $_.Name -match '^[0-9]+$' -and
            (Test-Path -LiteralPath (Join-Path $_.FullName 'draft.md') -PathType Leaf)
        } | Select-Object -First 1)
}
