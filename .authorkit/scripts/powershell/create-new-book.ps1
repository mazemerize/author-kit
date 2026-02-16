#!/usr/bin/env pwsh
# Create a new book project
[CmdletBinding()]
param(
    [switch]$Json,
    [string]$ShortName,
    [int]$Number = 0,
    [string]$Title,
    [string]$Author,
    [string]$Language,
    [switch]$Help,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$BookDescription
)
$ErrorActionPreference = 'Stop'

# Show help if requested
if ($Help) {
    Write-Host "Usage: ./create-new-book.ps1 [-Json] [-ShortName <name>] [-Number N] [-Title <title>] [-Author <author>] [-Language <language>] <book description>"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Json               Output in JSON format"
    Write-Host "  -ShortName <name>   Provide a custom short name (2-4 words) for the branch"
    Write-Host "  -Number N           Specify branch number manually (overrides auto-detection)"
    Write-Host "  -Title <title>      Set initial book title for book.toml"
    Write-Host "  -Author <author>    Set initial author for book.toml"
    Write-Host "  -Language <lang>    Set language (default: en-US)"
    Write-Host "  -Help               Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  ./create-new-book.ps1 'A mystery novel set in Victorian London' -ShortName 'victorian-mystery'"
    Write-Host "  ./create-new-book.ps1 'Technical guide to distributed systems'"
    exit 0
}

# Check if book description provided
if (-not $BookDescription -or $BookDescription.Count -eq 0) {
    Write-Error "Usage: ./create-new-book.ps1 [-Json] [-ShortName <name>] [-Title <title>] [-Author <author>] [-Language <language>] <book description>"
    exit 1
}

$bookDesc = ($BookDescription -join ' ').Trim()

# Resolve repository root
function Find-RepositoryRoot {
    param(
        [string]$StartDir,
        [string[]]$Markers = @('.git', '.authorkit')
    )
    $current = Resolve-Path $StartDir
    while ($true) {
        foreach ($marker in $Markers) {
            if (Test-Path (Join-Path $current $marker)) {
                return $current
            }
        }
        $parent = Split-Path $current -Parent
        if ($parent -eq $current) {
            return $null
        }
        $current = $parent
    }
}

function Get-HighestNumberFromBooks {
    param([string]$BooksDir)

    $highest = 0
    if (Test-Path $BooksDir) {
        Get-ChildItem -Path $BooksDir -Directory | ForEach-Object {
            if ($_.Name -match '^(\d+)') {
                $num = [int]$matches[1]
                if ($num -gt $highest) { $highest = $num }
            }
        }
    }
    return $highest
}

function Get-HighestNumberFromBranches {
    param()

    $highest = 0
    try {
        $branches = git branch -a 2>$null
        if ($LASTEXITCODE -eq 0) {
            foreach ($branch in $branches) {
                $cleanBranch = $branch.Trim() -replace '^\*?\s+', '' -replace '^remotes/[^/]+/', ''
                if ($cleanBranch -match '^(\d+)-') {
                    $num = [int]$matches[1]
                    if ($num -gt $highest) { $highest = $num }
                }
            }
        }
    } catch {
        Write-Verbose "Could not check Git branches: $_"
    }
    return $highest
}

function Get-NextBranchNumber {
    param([string]$BooksDir)

    try {
        git fetch --all --prune 2>$null | Out-Null
    } catch {
        # Ignore fetch errors
    }

    $highestBranch = Get-HighestNumberFromBranches
    $highestBook = Get-HighestNumberFromBooks -BooksDir $BooksDir
    $maxNum = [Math]::Max($highestBranch, $highestBook)
    return $maxNum + 1
}

function ConvertTo-CleanBranchName {
    param([string]$Name)
    return $Name.ToLower() -replace '[^a-z0-9]', '-' -replace '-{2,}', '-' -replace '^-', '' -replace '-$', ''
}

function Get-BranchName {
    param([string]$Description)

    $stopWords = @(
        'i', 'a', 'an', 'the', 'to', 'for', 'of', 'in', 'on', 'at', 'by', 'with', 'from',
        'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
        'do', 'does', 'did', 'will', 'would', 'should', 'could', 'can', 'may', 'might', 'must', 'shall',
        'this', 'that', 'these', 'those', 'my', 'your', 'our', 'their',
        'want', 'need', 'add', 'get', 'set', 'book', 'about', 'write', 'writing'
    )

    $cleanName = $Description.ToLower() -replace '[^a-z0-9\s]', ' '
    $words = $cleanName -split '\s+' | Where-Object { $_ }

    $meaningfulWords = @()
    foreach ($word in $words) {
        if ($stopWords -contains $word) { continue }
        if ($word.Length -ge 3) {
            $meaningfulWords += $word
        } elseif ($Description -match "\b$($word.ToUpper())\b") {
            $meaningfulWords += $word
        }
    }

    if ($meaningfulWords.Count -gt 0) {
        $maxWords = if ($meaningfulWords.Count -eq 4) { 4 } else { 3 }
        $result = ($meaningfulWords | Select-Object -First $maxWords) -join '-'
        return $result
    } else {
        $result = ConvertTo-CleanBranchName -Name $Description
        $fallbackWords = ($result -split '-') | Where-Object { $_ } | Select-Object -First 3
        return [string]::Join('-', $fallbackWords)
    }
}

# Resolve repo root
$fallbackRoot = (Find-RepositoryRoot -StartDir $PSScriptRoot)
if (-not $fallbackRoot) {
    Write-Error "Error: Could not determine repository root. Please run this script from within the repository."
    exit 1
}

try {
    $repoRoot = git rev-parse --show-toplevel 2>$null
    if ($LASTEXITCODE -eq 0) {
        $hasGit = $true
    } else {
        throw "Git not available"
    }
} catch {
    $repoRoot = $fallbackRoot
    $hasGit = $false
}

Set-Location $repoRoot

$booksDir = Join-Path $repoRoot 'books'
New-Item -ItemType Directory -Path $booksDir -Force | Out-Null

# Generate branch name
if ($ShortName) {
    $branchSuffix = ConvertTo-CleanBranchName -Name $ShortName
} else {
    $branchSuffix = Get-BranchName -Description $bookDesc
}

# Determine branch number
if ($Number -eq 0) {
    if ($hasGit) {
        $Number = Get-NextBranchNumber -BooksDir $booksDir
    } else {
        $Number = (Get-HighestNumberFromBooks -BooksDir $booksDir) + 1
    }
}

$bookNum = ('{0:000}' -f $Number)
$branchName = "$bookNum-$branchSuffix"

# GitHub enforces a 244-byte limit on branch names
$maxBranchLength = 244
if ($branchName.Length -gt $maxBranchLength) {
    $maxSuffixLength = $maxBranchLength - 4
    $truncatedSuffix = $branchSuffix.Substring(0, [Math]::Min($branchSuffix.Length, $maxSuffixLength))
    $truncatedSuffix = $truncatedSuffix -replace '-$', ''

    $originalBranchName = $branchName
    $branchName = "$bookNum-$truncatedSuffix"

    Write-Warning "[authorkit] Branch name exceeded GitHub's 244-byte limit"
    Write-Warning "[authorkit] Original: $originalBranchName ($($originalBranchName.Length) bytes)"
    Write-Warning "[authorkit] Truncated to: $branchName ($($branchName.Length) bytes)"
}

if ($hasGit) {
    try {
        git checkout -b $branchName | Out-Null
    } catch {
        Write-Warning "Failed to create git branch: $branchName"
    }
} else {
    Write-Warning "[authorkit] Warning: Git repository not detected; skipped branch creation for $branchName"
}

$bookDir = Join-Path $booksDir $branchName
New-Item -ItemType Directory -Path $bookDir -Force | Out-Null

# Copy concept template if it exists
$template = Join-Path $repoRoot '.authorkit/templates/concept-template.md'
$conceptFile = Join-Path $bookDir 'concept.md'
if (Test-Path $template) {
    Copy-Item $template $conceptFile -Force
} else {
    New-Item -ItemType File -Path $conceptFile -Force | Out-Null
}

# Create chapters subdirectory
$chaptersDir = Join-Path $bookDir 'chapters'
New-Item -ItemType Directory -Path $chaptersDir -Force | Out-Null

# Set the AUTHORKIT_BOOK environment variable for the current session
$env:AUTHORKIT_BOOK = $branchName

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

# Initialize canonical publish metadata file.
$bookTomlPath = Join-Path $bookDir 'book.toml'
$defaultTitle = (($branchSuffix -split '-') | ForEach-Object { (Get-Culture).TextInfo.ToTitleCase($_) }) -join ' '
$defaultAuthor = 'Unknown Author'
$defaultLanguage = 'en-US'

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
        BRANCH_NAME  = $branchName
        CONCEPT_FILE = $conceptFile
        BOOK_NUM     = $bookNum
        BOOK_DIR     = $bookDir
        BOOK_TOML    = $bookTomlPath
        HAS_GIT      = $hasGit
    }
    $obj | ConvertTo-Json -Compress
} else {
    Write-Output "BRANCH_NAME: $branchName"
    Write-Output "CONCEPT_FILE: $conceptFile"
    Write-Output "BOOK_NUM: $bookNum"
    Write-Output "BOOK_DIR: $bookDir"
    Write-Output "BOOK_TOML: $bookTomlPath"
    Write-Output "HAS_GIT: $hasGit"
    Write-Output "AUTHORKIT_BOOK environment variable set to: $branchName"
}
