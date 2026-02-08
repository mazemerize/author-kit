#!/usr/bin/env pwsh
# Common PowerShell functions for Author Kit

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
    # First check if AUTHORKIT_BOOK environment variable is set
    if ($env:AUTHORKIT_BOOK) {
        return $env:AUTHORKIT_BOOK
    }

    # Then check git if available
    try {
        $result = git rev-parse --abbrev-ref HEAD 2>$null
        if ($LASTEXITCODE -eq 0) {
            return $result
        }
    } catch {
        # Git command failed
    }

    # For non-git repos, try to find the latest book directory
    $repoRoot = Get-RepoRoot
    $booksDir = Join-Path $repoRoot "books"

    if (Test-Path $booksDir) {
        $latestBook = ""
        $highest = 0

        Get-ChildItem -Path $booksDir -Directory | ForEach-Object {
            if ($_.Name -match '^(\d{3})-') {
                $num = [int]$matches[1]
                if ($num -gt $highest) {
                    $highest = $num
                    $latestBook = $_.Name
                }
            }
        }

        if ($latestBook) {
            return $latestBook
        }
    }

    # Final fallback
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

function Test-BookBranch {
    param(
        [string]$Branch,
        [bool]$HasGit = $true
    )

    # For non-git repos, we can't enforce branch naming but still provide output
    if (-not $HasGit) {
        Write-Warning "[authorkit] Warning: Git repository not detected; skipped branch validation"
        return $true
    }

    if ($Branch -notmatch '^[0-9]{3}-') {
        Write-Output "ERROR: Not on a book branch. Current branch: $Branch"
        Write-Output "Book branches should be named like: 001-book-name"
        return $false
    }
    return $true
}

function Get-BookDir {
    param([string]$RepoRoot, [string]$Branch)
    Join-Path $RepoRoot "books/$Branch"
}

# Find book directory by numeric prefix instead of exact branch match
function Find-BookDirByPrefix {
    param(
        [string]$RepoRoot,
        [string]$BranchName
    )

    $booksDir = Join-Path $RepoRoot "books"

    # Extract numeric prefix from branch (e.g., "004" from "004-whatever")
    if ($BranchName -notmatch '^(\d{3})-') {
        # If branch doesn't have numeric prefix, fall back to exact match
        return (Join-Path $booksDir $BranchName)
    }

    $prefix = $matches[1]

    # Search for directories in books/ that start with this prefix
    $matchDirs = @()
    if (Test-Path $booksDir) {
        Get-ChildItem -Path $booksDir -Directory | Where-Object {
            $_.Name -match "^$prefix-"
        } | ForEach-Object {
            $matchDirs += $_.Name
        }
    }

    # Handle results
    if ($matchDirs.Count -eq 0) {
        # No match found - return the branch name path (will fail later with clear error)
        return (Join-Path $booksDir $BranchName)
    } elseif ($matchDirs.Count -eq 1) {
        # Exactly one match
        return (Join-Path $booksDir $matchDirs[0])
    } else {
        # Multiple matches
        Write-Warning "ERROR: Multiple book directories found with prefix '$prefix': $($matchDirs -join ', ')"
        Write-Warning "Please ensure only one book directory exists per numeric prefix."
        return (Join-Path $booksDir $BranchName)
    }
}

function Get-BookPaths {
    $repoRoot = Get-RepoRoot
    $currentBranch = Get-CurrentBranch
    $hasGit = Test-HasGit

    # Use prefix-based lookup to support multiple branches per book
    $bookDir = Find-BookDirByPrefix -RepoRoot $repoRoot -BranchName $currentBranch

    [PSCustomObject]@{
        REPO_ROOT      = $repoRoot
        CURRENT_BRANCH = $currentBranch
        HAS_GIT        = $hasGit
        BOOK_DIR       = $bookDir
        BOOK_CONCEPT   = Join-Path $bookDir 'concept.md'
        OUTLINE        = Join-Path $bookDir 'outline.md'
        CHAPTERS       = Join-Path $bookDir 'chapters.md'
        RESEARCH       = Join-Path $bookDir 'research.md'
        CHARACTERS     = Join-Path $bookDir 'characters.md'
        CHAPTERS_DIR   = Join-Path $bookDir 'chapters'
    }
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
