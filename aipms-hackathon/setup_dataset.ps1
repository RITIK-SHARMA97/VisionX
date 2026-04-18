# PowerShell Helper: Prepare C-MAPSS Dataset Download

param(
    [string]$ZipPath = "",
    [string]$SourceFolder = "",
    [switch]$Help
)

if ($Help) {
    Write-Host @"
C-MAPSS Dataset Download Helper

USAGE:
  .\setup_dataset.ps1 -ZipPath "C:\path\to\nasa-cmaps.zip"
  .\setup_dataset.ps1 -SourceFolder "C:\path\to\extracted\folder"
  .\setup_dataset.ps1 -Help

OPTIONS:
  -ZipPath         Path to downloaded nasa-cmaps.zip file
  -SourceFolder    Path to folder containing extracted files
  -Help            Show this help message

EXAMPLES:
  # If you have the ZIP file:
  .\setup_dataset.ps1 -ZipPath "C:\Users\sharm\Downloads\nasa-cmaps.zip"

  # If already extracted:
  .\setup_dataset.ps1 -SourceFolder "C:\Users\sharm\Downloads\nasa-cmaps"

STEPS:
  1. Download from: https://www.kaggle.com/datasets/behrad3d/nasa-cmaps
  2. Save to your Downloads folder
  3. Run: .\setup_dataset.ps1 -ZipPath "path\to\nasa-cmaps.zip"
  4. Or extract first, then run: .\setup_dataset.ps1 -SourceFolder "path\to\folder"
"@
    exit
}

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommandPath
$TargetDir = Join-Path $ProjectRoot "data" "raw"

# Ensure target directory exists
if (!(Test-Path $TargetDir)) {
    New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
    Write-Host "✓ Created directory: $TargetDir" -ForegroundColor Green
}

$RequiredFiles = @(
    'train_FD001.txt',
    'test_FD001.txt',
    'RUL_FD001.txt',
    'train_FD003.txt',
    'test_FD003.txt',
    'RUL_FD003.txt'
)

# Handle ZIP file
if ($ZipPath -and (Test-Path $ZipPath)) {
    Write-Host "`n" 
    Write-Host "=" * 80
    Write-Host "EXTRACTING ZIP FILE" -ForegroundColor Cyan
    Write-Host "=" * 80
    Write-Host "`nZIP File: $ZipPath" -ForegroundColor Yellow
    
    $ExtractPath = Join-Path $ProjectRoot "data" "_temp_extract"
    
    try {
        Write-Host "Extracting..."
        Expand-Archive -Path $ZipPath -DestinationPath $ExtractPath -Force
        Write-Host "✓ Extracted successfully" -ForegroundColor Green
        
        # Find the data files in extracted folder
        Write-Host "`nSearching for required files..."
        $SourceFolder = $ExtractPath
    }
    catch {
        Write-Host "✗ Error extracting ZIP: $_" -ForegroundColor Red
        exit 1
    }
}

# Copy files from source folder
if ($SourceFolder -and (Test-Path $SourceFolder)) {
    Write-Host "`n"
    Write-Host "=" * 80
    Write-Host "COPYING FILES" -ForegroundColor Cyan
    Write-Host "=" * 80
    Write-Host "`nSource: $SourceFolder" -ForegroundColor Yellow
    Write-Host "Target: $TargetDir" -ForegroundColor Yellow
    Write-Host ""
    
    $FilesFound = 0
    $FilesCopied = 0
    
    foreach ($file in $RequiredFiles) {
        $SourceFile = Get-ChildItem -Path $SourceFolder -Filter $file -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
        
        if ($SourceFile) {
            $FilesFound++
            $TargetFile = Join-Path $TargetDir $file
            
            try {
                Copy-Item -Path $SourceFile.FullName -Destination $TargetFile -Force
                $SizeMB = [math]::Round($SourceFile.Length / 1MB, 2)
                Write-Host "  ✓ $file ($SizeMB MB)" -ForegroundColor Green
                $FilesCopied++
            }
            catch {
                Write-Host "  ✗ $file - Error: $_" -ForegroundColor Red
            }
        }
        else {
            Write-Host "  ? $file - Not found" -ForegroundColor Yellow
        }
    }
    
    Write-Host ""
    Write-Host "=" * 80
    Write-Host "RESULTS" -ForegroundColor Cyan
    Write-Host "=" * 80
    Write-Host "Files found:  $FilesFound / 6"
    Write-Host "Files copied: $FilesCopied / 6"
    Write-Host ""
    
    if ($FilesCopied -eq 6) {
        Write-Host "✅ SUCCESS! All files copied" -ForegroundColor Green
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor Green
        Write-Host "  1. python check_dataset.py  (verify installation)"
        Write-Host "  2. python models/train/run_phase_2b.py  (start pipeline)"
    }
    else {
        Write-Host "⚠ Some files missing - check extracted folder" -ForegroundColor Yellow
    }
    
    # Cleanup temp folder
    if ((Test-Path $ExtractPath) -and ($SourceFolder -eq $ExtractPath)) {
        Remove-Item -Path $ExtractPath -Recurse -Force -ErrorAction SilentlyContinue
    }
}
else {
    if (!$ZipPath -and !$SourceFolder) {
        Write-Host "`n"
        Write-Host "=" * 80
        Write-Host "C-MAPSS Dataset Setup Helper" -ForegroundColor Cyan
        Write-Host "=" * 80
        Write-Host ""
        Write-Host "Usage:" -ForegroundColor Yellow
        Write-Host "  .\setup_dataset.ps1 -ZipPath ""C:\path\to\nasa-cmaps.zip"""
        Write-Host "  .\setup_dataset.ps1 -SourceFolder ""C:\path\to\extracted\folder"""
        Write-Host "  .\setup_dataset.ps1 -Help"
        Write-Host ""
        Write-Host "Download the dataset from:" -ForegroundColor Green
        Write-Host "  https://www.kaggle.com/datasets/behrad3d/nasa-cmaps"
        Write-Host ""
    }
    else {
        Write-Host "✗ Invalid path: $($ZipPath ?? $SourceFolder)" -ForegroundColor Red
    }
}

Write-Host ""
