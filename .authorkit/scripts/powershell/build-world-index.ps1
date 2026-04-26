#!/usr/bin/env pwsh

# Build or rebuild the world/ entity index for fast lookups and consistency checking.
#
# Usage: ./build-world-index.ps1 [OPTIONS]
#
# OPTIONS:
#   -Json               Output stats in JSON format
#   -AddFrontmatter     Batch-add YAML frontmatter to files that lack it
#   -Help               Show help message
#
# This script generates world/_index.md with three sections:
#   1. Entity Registry — one row per entity with ID, name, aliases, file, chapters
#   2. Alias Lookup — flat alias-to-entity mapping for name resolution
#   3. Chapter Manifest — inverted index from chapters to entity lists

[CmdletBinding()]
param(
    [switch]$Json,
    [switch]$AddFrontmatter,
    [switch]$Help
)

$ErrorActionPreference = 'Stop'

if ($Help) {
    Write-Output @"
Usage: build-world-index.ps1 [OPTIONS]

Build or rebuild the world/ entity index for fast lookups.

OPTIONS:
  -Json               Output stats in JSON format
  -AddFrontmatter     Batch-add YAML frontmatter to files that lack it
  -Help               Show this help message

EXAMPLES:
  # Full rebuild of world/_index.md
  .\build-world-index.ps1 -Json

  # Add frontmatter to legacy files, then rebuild
  .\build-world-index.ps1 -AddFrontmatter -Json

OUTPUT (JSON):
  BOOK_DIR, INDEX_FILE, ENTITY_COUNT, ALIAS_COUNT, CHAPTER_COUNT,
  FILES_WITHOUT_FRONTMATTER, ENTITIES

"@
    exit 0
}

# Source common functions
. "$PSScriptRoot/common.ps1"

# --- Helper Functions ---

# Map world/ subdirectory name to type prefix and type value
function Get-TypeInfo {
    param([string]$SubDir)
    switch ($SubDir) {
        'characters'    { return @{ Prefix = 'char-';  Type = 'character' } }
        'places'        { return @{ Prefix = 'place-'; Type = 'place' } }
        'organizations' { return @{ Prefix = 'org-';   Type = 'organization' } }
        'history'       { return @{ Prefix = 'event-'; Type = 'event' } }
        'systems'       { return @{ Prefix = 'sys-';   Type = 'system' } }
        'notes'         { return @{ Prefix = 'note-';  Type = 'note' } }
        default         { return @{ Prefix = 'misc-';  Type = 'misc' } }
    }
}

# Convert a name to kebab-case for ID generation
function ConvertTo-KebabCase {
    param([string]$Name)
    $result = $Name.ToLower()
    # Remove leading articles
    $result = $result -replace '^(the|a|an)\s+', ''
    # Replace non-alphanumeric with hyphens
    $result = $result -replace '[^a-z0-9]+', '-'
    # Collapse multiple hyphens and trim
    $result = $result -replace '-+', '-'
    $result = $result.Trim('-')
    return $result
}

# Parse YAML frontmatter from file content lines
# Returns a hashtable of parsed fields, or $null if no frontmatter found
function Parse-Frontmatter {
    param([string[]]$Lines)

    if ($Lines.Count -lt 3 -or $Lines[0].Trim() -ne '---') {
        return $null
    }

    # Find closing ---
    $endIdx = -1
    for ($i = 1; $i -lt $Lines.Count; $i++) {
        if ($Lines[$i].Trim() -eq '---') {
            $endIdx = $i
            break
        }
    }
    if ($endIdx -lt 0) { return $null }

    $fm = @{
        Id             = ''
        Type           = ''
        Name           = ''
        Aliases        = @()
        Chapters       = @()
        FirstAppearance = ''
        Relationships  = @()
        Tags           = @()
        LastUpdated    = ''
        EndLine        = $endIdx
    }

    $inRelationship = $false
    $currentRel = $null

    for ($i = 1; $i -lt $endIdx; $i++) {
        $line = $Lines[$i]

        # Relationship items (nested under relationships:)
        if ($inRelationship) {
            if ($line -match '^\s+-\s+target:\s*(.+)$') {
                # New relationship item
                if ($currentRel -and $currentRel.Target) {
                    $fm.Relationships += $currentRel
                }
                $currentRel = @{ Target = $matches[1].Trim(); Type = ''; Since = '' }
                continue
            }
            if ($line -match '^\s+type:\s*(.+)$' -and $currentRel) {
                $currentRel.Type = $matches[1].Trim()
                continue
            }
            if ($line -match '^\s+since:\s*(.+)$' -and $currentRel) {
                $currentRel.Since = $matches[1].Trim()
                continue
            }
            # If we hit a non-indented line, end relationships block
            if ($line -match '^[a-z]') {
                if ($currentRel -and $currentRel.Target) {
                    $fm.Relationships += $currentRel
                }
                $currentRel = $null
                $inRelationship = $false
                # Fall through to parse this line as a regular field
            } else {
                continue
            }
        }

        # Simple fields
        if ($line -match '^id:\s*(.+)$') {
            $fm.Id = $matches[1].Trim()
        }
        elseif ($line -match '^type:\s*(.+)$') {
            $fm.Type = $matches[1].Trim()
        }
        elseif ($line -match '^name:\s*(.+)$') {
            $fm.Name = $matches[1].Trim()
        }
        elseif ($line -match '^first_appearance:\s*(.+)$') {
            $fm.FirstAppearance = $matches[1].Trim()
        }
        elseif ($line -match '^last_updated:\s*(.+)$') {
            $fm.LastUpdated = $matches[1].Trim()
        }
        # Inline array fields: [a, b, c]
        elseif ($line -match '^aliases:\s*\[([^\]]*)\]$') {
            $raw = $matches[1].Trim()
            if ($raw) {
                $fm.Aliases = $raw -split ',\s*' | ForEach-Object { $_.Trim() }
            }
        }
        elseif ($line -match '^chapters:\s*\[([^\]]*)\]$') {
            $raw = $matches[1].Trim()
            if ($raw) {
                $fm.Chapters = $raw -split ',\s*' | ForEach-Object { $_.Trim() }
            }
        }
        elseif ($line -match '^tags:\s*\[([^\]]*)\]$') {
            $raw = $matches[1].Trim()
            if ($raw) {
                $fm.Tags = $raw -split ',\s*' | ForEach-Object { $_.Trim() }
            }
        }
        # Relationships block start
        elseif ($line -match '^relationships:') {
            $inRelationship = $true
            $currentRel = $null
        }
    }

    # Flush last relationship
    if ($currentRel -and $currentRel.Target) {
        $fm.Relationships += $currentRel
    }

    return $fm
}

# Extract metadata heuristically from a file without frontmatter
function Extract-HeuristicMetadata {
    param(
        [string]$FilePath,
        [string]$SubDir,
        [string[]]$Lines,
        [string]$RelativePath
    )

    $typeInfo = Get-TypeInfo -SubDir $SubDir

    # Extract name from first H1
    $name = ''
    foreach ($line in $Lines) {
        if ($line -match '^#\s+(.+)$') {
            $name = $matches[1].Trim()
            break
        }
    }
    if (-not $name) {
        $name = [System.IO.Path]::GetFileNameWithoutExtension($FilePath) -replace '-', ' '
        $name = (Get-Culture).TextInfo.ToTitleCase($name)
    }

    $kebab = ConvertTo-KebabCase -Name $name
    $id = "$($typeInfo.Prefix)$kebab"

    # Extract chapter tags from body via regex
    $bodyText = $Lines -join "`n"
    $chapterTags = @()
    $tagMatches = [regex]::Matches($bodyText, '\((CONCEPT|CH\d{2}|CH\d{2}-rev|AMEND-\d{4}-\d{2}-\d{2}|RETCON-\d{4}-\d{2}-\d{2}|PIVOT-\d{4}-\d{2}-\d{2})\)')
    foreach ($m in $tagMatches) {
        $tag = $m.Groups[1].Value
        if ($chapterTags -notcontains $tag) {
            $chapterTags += $tag
        }
    }

    # Determine first appearance (lowest CHxx, excluding CONCEPT)
    $firstAppearance = 'CONCEPT'
    $chNums = $chapterTags | Where-Object { $_ -match '^CH\d{2}$' } | Sort-Object
    if ($chNums.Count -gt 0) {
        $firstAppearance = $chNums[0]
    }

    return @{
        Id              = $id
        Type            = $typeInfo.Type
        Name            = $name
        Aliases         = @()
        Chapters        = $chapterTags
        FirstAppearance = $firstAppearance
        Relationships   = @()
        Tags            = @()
        LastUpdated     = (Get-Item $FilePath).LastWriteTime.ToString('yyyy-MM-dd')
        HasFrontmatter  = $false
    }
}

# Generate YAML frontmatter string for a given entity metadata
function Format-Frontmatter {
    param([hashtable]$Entity)

    $aliasStr = if ($Entity.Aliases.Count -gt 0) {
        "[$(($Entity.Aliases | ForEach-Object { $_ }) -join ', ')]"
    } else { '[]' }

    $chapStr = if ($Entity.Chapters.Count -gt 0) {
        "[$(($Entity.Chapters | ForEach-Object { $_ }) -join ', ')]"
    } else { '[]' }

    $tagsStr = if ($Entity.Tags.Count -gt 0) {
        "[$(($Entity.Tags | ForEach-Object { $_ }) -join ', ')]"
    } else { '[]' }

    $relLines = ''
    if ($Entity.Relationships.Count -gt 0) {
        $relLines = "`nrelationships:"
        foreach ($rel in $Entity.Relationships) {
            $relLines += "`n  - target: $($rel.Target)`n    type: $($rel.Type)`n    since: $($rel.Since)"
        }
    } else {
        $relLines = "`nrelationships: []"
    }

    return @"
---
id: $($Entity.Id)
type: $($Entity.Type)
name: $($Entity.Name)
aliases: $aliasStr
chapters: $chapStr
first_appearance: $($Entity.FirstAppearance)$relLines
tags: $tagsStr
last_updated: $($Entity.LastUpdated)
---
"@
}

# Sort chapter tags: CONCEPT first, then CHxx numerically, then CHxx-rev, then AMEND/PIVOT/RETCON by date
function Sort-ChapterTags {
    param([string[]]$Tags)

    $concept = $Tags | Where-Object { $_ -eq 'CONCEPT' }
    $chTags = $Tags | Where-Object { $_ -match '^CH\d{2}$' } | Sort-Object
    $chRevTags = $Tags | Where-Object { $_ -match '^CH\d{2}-rev$' } | Sort-Object
    $otherTags = $Tags | Where-Object { $_ -match '^(AMEND|PIVOT|RETCON)-' } | Sort-Object

    $result = @()
    if ($concept) { $result += $concept }
    $result += $chTags
    $result += $chRevTags
    $result += $otherTags
    return $result
}

# Escape pipe characters for markdown table cells
function Escape-TableCell {
    param([string]$Text)
    return $Text -replace '\|', '\|'
}

# --- Main Script ---

$paths = Get-BookPaths
$bookDir = $paths.BOOK_DIR
$worldDir = Join-Path $bookDir 'world'
$legacyWorldDir = Join-Path $bookDir 'World'

if (-not (Test-Path $worldDir -PathType Container)) {
    if (Test-Path $legacyWorldDir -PathType Container) {
        Write-Output "ERROR: Legacy world directory casing detected at $legacyWorldDir"
        Write-Output "Rename it to lowercase 'world/' before running world commands."
        exit 1
    }
    Write-Output "ERROR: world/ directory not found at $worldDir"
    Write-Output "Run /authorkit.world.build first to create the world."
    exit 1
}

# Collect all entity files
$entityFiles = @()
$subDirs = @('characters', 'places', 'organizations', 'history', 'systems', 'notes')

foreach ($subDir in $subDirs) {
    $dirPath = Join-Path $worldDir $subDir
    if (Test-Path $dirPath -PathType Container) {
        Get-ChildItem -Path $dirPath -Filter '*.md' -File -Recurse | ForEach-Object {
            $relPath = $_.FullName.Substring($worldDir.Length).TrimStart('\', '/')
            $relPath = $relPath -replace '\\', '/'
            $entityFiles += @{
                FullPath = $_.FullName
                SubDir   = $subDir
                RelPath  = $relPath
            }
        }
    }
}

if ($entityFiles.Count -eq 0) {
    Write-Output "WARNING: No entity files found in $worldDir"
    if ($Json) {
        [PSCustomObject]@{
            BOOK_DIR     = $bookDir
            INDEX_FILE   = Join-Path $worldDir '_index.md'
            ENTITY_COUNT = 0
            ALIAS_COUNT  = 0
            CHAPTER_COUNT = 0
            FILES_WITHOUT_FRONTMATTER = 0
        } | ConvertTo-Json -Compress
    }
    exit 0
}

# Parse all entities
$entities = @()
$filesWithoutFrontmatter = @()

foreach ($ef in $entityFiles) {
    $lines = Get-Content -Path $ef.FullPath -Encoding UTF8

    $fm = Parse-Frontmatter -Lines $lines

    if ($fm) {
        $entity = @{
            Id              = $fm.Id
            Type            = $fm.Type
            Name            = $fm.Name
            Aliases         = $fm.Aliases
            Chapters        = $fm.Chapters
            FirstAppearance = $fm.FirstAppearance
            Relationships   = $fm.Relationships
            Tags            = $fm.Tags
            LastUpdated     = $fm.LastUpdated
            RelPath         = $ef.RelPath
            FullPath        = $ef.FullPath
            HasFrontmatter  = $true
        }
        $entities += $entity
    } else {
        $entity = Extract-HeuristicMetadata -FilePath $ef.FullPath -SubDir $ef.SubDir -Lines $lines -RelativePath $ef.RelPath
        $entity.RelPath = $ef.RelPath
        $entity.FullPath = $ef.FullPath
        $entity.HasFrontmatter = $false
        $entities += $entity
        $filesWithoutFrontmatter += $ef
    }
}

# --- AddFrontmatter Mode ---

if ($AddFrontmatter -and $filesWithoutFrontmatter.Count -gt 0) {
    foreach ($ef in $filesWithoutFrontmatter) {
        $entity = $entities | Where-Object { $_.FullPath -eq $ef.FullPath }
        if (-not $entity) { continue }

        $fmBlock = Format-Frontmatter -Entity $entity
        $existingContent = Get-Content -Path $ef.FullPath -Raw -Encoding UTF8

        $newContent = "$fmBlock`n$existingContent"
        Set-Content -Path $ef.FullPath -Value $newContent -Encoding UTF8 -NoNewline

        $entity.HasFrontmatter = $true
    }

    Write-Warning "[authorkit] Added frontmatter to $($filesWithoutFrontmatter.Count) file(s)"

    # Re-count after adding
    $filesWithoutFrontmatter = @()
}

# --- Build Index Sections ---

# Sort entities: by type alphabetically, then by name within type
$sortedEntities = $entities | Sort-Object @{Expression={$_.Type}}, @{Expression={$_.Name}}

# 1. Entity Registry
$registryLines = @()
$registryLines += '| ID | Type | Name | Aliases | File | Chapters | First Appearance | Flags |'
$registryLines += '|----|------|------|---------|------|----------|-----------------|-------|'

foreach ($e in $sortedEntities) {
    $aliasStr = ($e.Aliases | ForEach-Object { Escape-TableCell $_ }) -join '; '
    $sortedChapters = Sort-ChapterTags -Tags $e.Chapters
    $chapStr = $sortedChapters -join ', '
    $flags = if (-not $e.HasFrontmatter) { '[NO FRONTMATTER]' } else { '' }

    $registryLines += "| $(Escape-TableCell $e.Id) | $($e.Type) | $(Escape-TableCell $e.Name) | $aliasStr | $($e.RelPath) | $chapStr | $($e.FirstAppearance) | $flags |"
}

# 2. Alias Lookup
$aliasMap = @{}

foreach ($e in $sortedEntities) {
    # Name is implicitly an alias
    $allNames = @($e.Name) + $e.Aliases

    foreach ($alias in $allNames) {
        $aliasLower = $alias.ToLower()
        if (-not $aliasMap.ContainsKey($aliasLower)) {
            $aliasMap[$aliasLower] = @{
                Display  = $alias
                Entities = @()
            }
        }
        $aliasMap[$aliasLower].Entities += @{ Id = $e.Id; Type = $e.Type }
    }
}

$aliasLines = @()
$aliasLines += '| Alias | Entity ID | Type | Ambiguous |'
$aliasLines += '|-------|-----------|------|-----------|'

$sortedAliases = $aliasMap.GetEnumerator() | Sort-Object { $_.Value.Display.ToLower() }
$totalAliasRows = 0

foreach ($entry in $sortedAliases) {
    $display = $entry.Value.Display
    $entitiesForAlias = $entry.Value.Entities
    $ambiguous = if ($entitiesForAlias.Count -gt 1) { 'YES' } else { '' }

    foreach ($ent in $entitiesForAlias) {
        $aliasLines += "| $(Escape-TableCell $display) | $($ent.Id) | $($ent.Type) | $ambiguous |"
        $totalAliasRows++
    }
}

# 3. Chapter Manifest
$chapterMap = @{}

foreach ($e in $sortedEntities) {
    foreach ($ch in $e.Chapters) {
        # For CHxx-rev, also add to base CHxx
        $keys = @($ch)
        if ($ch -match '^(CH\d{2})-rev$') {
            $baseChapter = $matches[1]
            if ($keys -notcontains $baseChapter) {
                $keys += $baseChapter
            }
        }

        foreach ($key in $keys) {
            # Only include CONCEPT and CHxx/CHxx-rev in manifest (not AMEND/PIVOT/RETCON date tags)
            if ($key -match '^(CONCEPT|CH\d{2}|CH\d{2}-rev)$') {
                if (-not $chapterMap.ContainsKey($key)) {
                    $chapterMap[$key] = @()
                }
                if ($chapterMap[$key] -notcontains $e.Id) {
                    $chapterMap[$key] += $e.Id
                }
            }
        }
    }
}

# Sort chapter keys: CONCEPT first, then CHxx numerically
$sortedChapterKeys = @()
if ($chapterMap.ContainsKey('CONCEPT')) {
    $sortedChapterKeys += 'CONCEPT'
}
$chKeys = $chapterMap.Keys | Where-Object { $_ -match '^CH\d{2}$' } | Sort-Object
$sortedChapterKeys += $chKeys
$chRevKeys = $chapterMap.Keys | Where-Object { $_ -match '^CH\d{2}-rev$' } | Sort-Object
$sortedChapterKeys += $chRevKeys

$manifestLines = @()
foreach ($key in $sortedChapterKeys) {
    $entityIds = $chapterMap[$key] | Sort-Object
    $manifestLines += "### $key"
    $manifestLines += ($entityIds -join ', ')
    $manifestLines += ''
}

# --- Assemble Index File ---

$timestamp = (Get-Date).ToString('yyyy-MM-ddTHH:mm:ss')
$noFmCount = ($entities | Where-Object { -not $_.HasFrontmatter }).Count

$indexContent = @"
---
generated: $timestamp
entity_count: $($entities.Count)
schema_version: 1
---

# World Index

## Entity Registry

$($registryLines -join "`n")

## Alias Lookup

$($aliasLines -join "`n")

## Chapter Manifest

$($manifestLines -join "`n")

## Statistics

- **Total entities**: $($entities.Count)
- **Characters**: $(($entities | Where-Object { $_.Type -eq 'character' }).Count)
- **Places**: $(($entities | Where-Object { $_.Type -eq 'place' }).Count)
- **Organizations**: $(($entities | Where-Object { $_.Type -eq 'organization' }).Count)
- **Events**: $(($entities | Where-Object { $_.Type -eq 'event' }).Count)
- **Systems**: $(($entities | Where-Object { $_.Type -eq 'system' }).Count)
- **Notes**: $(($entities | Where-Object { $_.Type -eq 'note' }).Count)
- **Total aliases**: $totalAliasRows
- **Chapters tracked**: $($sortedChapterKeys.Count)
- **Files with frontmatter**: $(($entities | Where-Object { $_.HasFrontmatter }).Count)/$($entities.Count)
"@

$indexFile = Join-Path $worldDir '_index.md'
Set-Content -Path $indexFile -Value $indexContent -Encoding UTF8 -NoNewline

# --- Output ---

if ($Json) {
    [PSCustomObject]@{
        BOOK_DIR                   = $bookDir
        INDEX_FILE                 = $indexFile
        ENTITY_COUNT               = $entities.Count
        ALIAS_COUNT                = $totalAliasRows
        CHAPTER_COUNT              = $sortedChapterKeys.Count
        FILES_WITHOUT_FRONTMATTER  = $noFmCount
    } | ConvertTo-Json -Compress
} else {
    Write-Output "INDEX_FILE: $indexFile"
    Write-Output "ENTITY_COUNT: $($entities.Count)"
    Write-Output "ALIAS_COUNT: $totalAliasRows"
    Write-Output "CHAPTER_COUNT: $($sortedChapterKeys.Count)"
    Write-Output "FILES_WITHOUT_FRONTMATTER: $noFmCount"
}
