param(
    [ValidateSet("current", "all", "clean")]
    [string]$Target = "current"
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$CliRoot = Resolve-Path (Join-Path $ScriptDir "..")
$OutputDir = Join-Path $CliRoot "build\output"

function Build-Target {
    param(
        [Parameter(Mandatory = $true)][string]$GoOS,
        [Parameter(Mandatory = $true)][string]$GoArch
    )

    $ext = if ($GoOS -eq "windows") { ".exe" } else { "" }
    $outFile = Join-Path $OutputDir ("neurograph-{0}-{1}{2}" -f $GoOS, $GoArch, $ext)

    Write-Host ("Building {0}/{1} -> {2}" -f $GoOS, $GoArch, $outFile)

    Push-Location $CliRoot
    try {
        $env:GOOS = $GoOS
        $env:GOARCH = $GoArch
        $env:CGO_ENABLED = "0"
        go build -trimpath -ldflags "-s -w" -o $outFile ./cmd/neurograph
    }
    finally {
        Remove-Item Env:GOOS -ErrorAction SilentlyContinue
        Remove-Item Env:GOARCH -ErrorAction SilentlyContinue
        Remove-Item Env:CGO_ENABLED -ErrorAction SilentlyContinue
        Pop-Location
    }
}

if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

switch ($Target) {
    "current" {
        Push-Location $CliRoot
        try {
            $goos = (go env GOOS).Trim()
            $goarch = (go env GOARCH).Trim()
        }
        finally {
            Pop-Location
        }
        Build-Target -GoOS $goos -GoArch $goarch
    }
    "all" {
        Build-Target -GoOS "linux" -GoArch "amd64"
        Build-Target -GoOS "linux" -GoArch "arm64"
        Build-Target -GoOS "darwin" -GoArch "amd64"
        Build-Target -GoOS "darwin" -GoArch "arm64"
        Build-Target -GoOS "windows" -GoArch "amd64"
        Build-Target -GoOS "windows" -GoArch "arm64"
    }
    "clean" {
        if (Test-Path $OutputDir) {
            Remove-Item -Recurse -Force $OutputDir
        }
        New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
        Write-Host ("Cleaned {0}" -f $OutputDir)
    }
}

Write-Host ("Build artifacts are in: {0}" -f $OutputDir)
