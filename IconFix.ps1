#Requires -Version 5.1
[CmdletBinding()]
param(
    [string]$Path = [Environment]::GetFolderPath("DesktopDirectory"),

    [switch]$All,
    [switch]$NoElevate,
    [switch]$NoPause,
    [switch]$Version,
    [switch]$Elevated
)

$ErrorActionPreference = "Stop"

$Script:AppName = "IconFix"
$Script:AppVersion = "2.1.0"
$Script:SelfUrl = "https://raw.githubusercontent.com/Einck0/IconFix/main/IconFix.ps1"
$Script:PublicDesktopPath = Join-Path $env:PUBLIC "Desktop"
$Script:Headers = @{
    "User-Agent" = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
}

function Write-IconFixLog {
    param(
        [ValidateSet("INFO", "WARN", "ERROR")]
        [string]$Level,
        [string]$Message
    )

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "$timestamp | $Level | $Message"
}

function Test-IsAdministrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function ConvertTo-CommandLineArgument {
    param([string]$Value)

    if ($null -eq $Value) {
        return '""'
    }

    return '"' + ($Value -replace '"', '\"') + '"'
}

function Get-CurrentScriptPath {
    if ($PSCommandPath) {
        return $PSCommandPath
    }

    if ($MyInvocation.MyCommand.Path) {
        return $MyInvocation.MyCommand.Path
    }

    return $null
}

function Save-SelfToTempFile {
    $targetPath = Join-Path $env:TEMP "IconFix.ps1"
    Write-IconFixLog -Level "INFO" -Message "Downloading runnable script to $targetPath"
    Invoke-WebRequest -UseBasicParsing -Uri $Script:SelfUrl -OutFile $targetPath -Headers $Script:Headers
    return $targetPath
}

function Resolve-ScanPath {
    param([string]$InputPath)

    $expandedPath = [Environment]::ExpandEnvironmentVariables($InputPath)
    if (-not [IO.Path]::IsPathRooted($expandedPath)) {
        $expandedPath = Join-Path (Get-Location).Path $expandedPath
    }

    if (-not (Test-Path -LiteralPath $expandedPath -PathType Container)) {
        throw "Scan path does not exist: $expandedPath"
    }

    return (Resolve-Path -LiteralPath $expandedPath).ProviderPath
}

function Start-ElevatedProcess {
    param([string]$TargetPath)

    $scriptPath = Get-CurrentScriptPath
    if (-not $scriptPath) {
        $scriptPath = Save-SelfToTempFile
    }

    $arguments = @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", (ConvertTo-CommandLineArgument $scriptPath),
        "-Path", (ConvertTo-CommandLineArgument $TargetPath),
        "-Elevated"
    )

    if ($All) {
        $arguments += "-All"
    }
    if ($NoElevate) {
        $arguments += "-NoElevate"
    }
    if ($NoPause) {
        $arguments += "-NoPause"
    }

    Start-Process -FilePath "powershell.exe" -Verb RunAs -ArgumentList ($arguments -join " ")
}

function Ensure-Administrator {
    param([string]$TargetPath)

    if (Test-IsAdministrator) {
        return $false
    }

    if ($Elevated) {
        throw "Administrator elevation was requested, but the new process is still not elevated."
    }

    if ($NoElevate) {
        Write-IconFixLog -Level "WARN" -Message "Running without administrator rights. Some icon files may fail to write."
        return $false
    }

    Write-IconFixLog -Level "INFO" -Message "Requesting administrator permission..."
    Start-ElevatedProcess -TargetPath $TargetPath
    return $true
}

function Get-UrlShortcutFiles {
    param([string]$DirectoryPath)

    if (-not (Test-Path -LiteralPath $DirectoryPath -PathType Container)) {
        return @()
    }

    return @(
        Get-ChildItem -LiteralPath $DirectoryPath -Recurse -Filter "*.url" -ErrorAction SilentlyContinue |
            Where-Object { -not $_.PSIsContainer } |
            Sort-Object FullName
    )
}

function Get-ShortcutDiscovery {
    param([string]$TargetPath)

    $localShortcuts = @(Get-UrlShortcutFiles -DirectoryPath $TargetPath)
    $publicShortcuts = @(Get-UrlShortcutFiles -DirectoryPath $Script:PublicDesktopPath)
    $seen = @{}
    $shortcuts = New-Object System.Collections.Generic.List[object]

    foreach ($shortcut in @($localShortcuts) + @($publicShortcuts)) {
        if ($null -eq $shortcut) {
            continue
        }

        $key = $shortcut.FullName.ToLowerInvariant()
        if ($seen.ContainsKey($key)) {
            continue
        }

        $seen[$key] = $true
        $shortcuts.Add($shortcut) | Out-Null
    }

    return [pscustomobject]@{
        Shortcuts = @($shortcuts.ToArray())
        LocalCount = $localShortcuts.Count
        PublicCount = $publicShortcuts.Count
    }
}

function ConvertTo-SelectionIndexes {
    param(
        [string]$RawText,
        [int]$MaxIndex
    )

    if ([string]::IsNullOrWhiteSpace($RawText)) {
        return @()
    }

    $tokens = $RawText.Trim() -split "[\s,]+"
    $selected = New-Object System.Collections.Generic.List[int]
    $selectedSet = @{}

    foreach ($token in $tokens) {
        $index = 0
        if (-not [int]::TryParse($token, [ref]$index)) {
            throw "Invalid selection '$token'. Please enter numbers only."
        }
        if ($index -lt 0) {
            throw "Selection cannot be negative."
        }
        if ($index -eq 0) {
            return @(1..$MaxIndex)
        }
        if ($index -gt $MaxIndex) {
            throw "Selection is out of range: $index"
        }
        if (-not $selectedSet.ContainsKey($index)) {
            $selectedSet[$index] = $true
            $selected.Add($index) | Out-Null
        }
    }

    return @($selected.ToArray() | Sort-Object)
}

function Select-Shortcuts {
    param([object[]]$Shortcuts)

    if ($All) {
        return @($Shortcuts)
    }

    Write-Host "0: All files"
    for ($i = 0; $i -lt $Shortcuts.Count; $i++) {
        Write-Host "$($i + 1): $($Shortcuts[$i].FullName)"
    }

    $rawSelection = Read-Host "`nSelect shortcut numbers to fix, separated by spaces or commas"
    $indexes = ConvertTo-SelectionIndexes -RawText $rawSelection -MaxIndex $Shortcuts.Count
    return @($indexes | ForEach-Object { $Shortcuts[$_ - 1] })
}

function Read-ShortcutMetadata {
    param([object]$Shortcut)

    try {
        $content = [IO.File]::ReadAllText($Shortcut.FullName, [Text.Encoding]::Default)
    }
    catch {
        Write-IconFixLog -Level "ERROR" -Message "Failed to read shortcut $($Shortcut.FullName): $($_.Exception.Message)"
        return $null
    }

    $steamMatch = [regex]::Match($content, "(?im)^URL=steam://rungameid/(\d+)\s*$")
    if (-not $steamMatch.Success) {
        Write-IconFixLog -Level "WARN" -Message "Skipping non-Steam shortcut: $($Shortcut.FullName)"
        return $null
    }

    $iconMatch = [regex]::Match($content, "(?im)^IconFile=(.+?\.ico)\s*$")
    if (-not $iconMatch.Success) {
        Write-IconFixLog -Level "WARN" -Message "Skipping shortcut without IconFile: $($Shortcut.FullName)"
        return $null
    }

    $iconPath = $iconMatch.Groups[1].Value.Trim()
    return [pscustomobject]@{
        ShortcutPath = $Shortcut.FullName
        SteamId = $steamMatch.Groups[1].Value
        IconPath = $iconPath
        IconName = [IO.Path]::GetFileName($iconPath)
    }
}

function Save-SteamIcon {
    param([object]$Metadata)

    $iconUrl = "https://cdn.cloudflare.steamstatic.com/steamcommunity/public/images/apps/$($Metadata.SteamId)/$($Metadata.IconName)"
    $iconDirectory = Split-Path -Parent $Metadata.IconPath
    if ($iconDirectory) {
        New-Item -ItemType Directory -Force -Path $iconDirectory | Out-Null
    }

    $tempFile = [IO.Path]::GetTempFileName()
    try {
        Invoke-WebRequest -UseBasicParsing -Uri $iconUrl -Headers $Script:Headers -TimeoutSec 10 -OutFile $tempFile
        Move-Item -LiteralPath $tempFile -Destination $Metadata.IconPath -Force
    }
    catch {
        if (Test-Path -LiteralPath $tempFile) {
            Remove-Item -LiteralPath $tempFile -Force -ErrorAction SilentlyContinue
        }
        throw
    }
}

function Repair-Icons {
    param([string]$TargetPath)

    Write-IconFixLog -Level "INFO" -Message "Scanning shortcuts in $TargetPath"
    $discovery = Get-ShortcutDiscovery -TargetPath $TargetPath
    if ($discovery.Shortcuts.Count -eq 0) {
        Write-IconFixLog -Level "INFO" -Message "No .url shortcuts found."
        return 0
    }

    Write-IconFixLog -Level "INFO" -Message "Found $($discovery.Shortcuts.Count) shortcuts. Local: $($discovery.LocalCount), Public desktop: $($discovery.PublicCount)."
    $selectedShortcuts = Select-Shortcuts -Shortcuts $discovery.Shortcuts
    if ($selectedShortcuts.Count -eq 0) {
        Write-IconFixLog -Level "INFO" -Message "No shortcuts selected."
        return 0
    }

    $successCount = 0
    $failedCount = 0
    $skippedCount = 0

    foreach ($shortcut in $selectedShortcuts) {
        $metadata = Read-ShortcutMetadata -Shortcut $shortcut
        if ($null -eq $metadata) {
            $skippedCount++
            continue
        }

        try {
            Save-SteamIcon -Metadata $metadata
            $successCount++
            Write-IconFixLog -Level "INFO" -Message "Fixed: $($metadata.ShortcutPath)"
        }
        catch {
            $failedCount++
            Write-IconFixLog -Level "ERROR" -Message "Failed: $($metadata.ShortcutPath) - $($_.Exception.Message)"
        }
    }

    Write-IconFixLog -Level "INFO" -Message "Complete. Success: $successCount, Failed: $failedCount, Skipped: $skippedCount."
    if ($failedCount -gt 0) {
        return 1
    }

    return 0
}

function Wait-IfNeeded {
    param([bool]$ShouldPause)

    if (-not $ShouldPause) {
        return
    }

    if ([Environment]::UserInteractive) {
        Read-Host "`nPress Enter to exit"
    }
}

$shouldPause = -not $NoPause
$exitCode = 0

try {
    if ($Version) {
        Write-Host "$Script:AppName $Script:AppVersion"
        return
    }

    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
    }
    catch {
        Write-IconFixLog -Level "WARN" -Message "Could not force TLS 1.2, continuing with system defaults."
    }

    $targetPath = Resolve-ScanPath -InputPath $Path
    $relaunched = Ensure-Administrator -TargetPath $targetPath
    if ($relaunched) {
        $shouldPause = $false
        return
    }

    Write-IconFixLog -Level "INFO" -Message "$Script:AppName $Script:AppVersion started."
    $exitCode = Repair-Icons -TargetPath $targetPath
}
catch {
    $exitCode = 1
    Write-IconFixLog -Level "ERROR" -Message $_.Exception.Message
}
finally {
    Wait-IfNeeded -ShouldPause $shouldPause
}

exit $exitCode
