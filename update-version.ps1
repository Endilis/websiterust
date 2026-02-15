# Auto-update CSS version based on file hash
# Usage: .\update-version.ps1

$cssFile = "style.css"
$htmlFile = "index.html"

# Calculate MD5 hash of CSS file
$cssHash = Get-FileHash $cssFile -Algorithm MD5
$shortHash = $cssHash.Hash.Substring(0, 8).ToLower()

# Read HTML content
$htmlContent = Get-Content $htmlFile -Raw

# Find current version and replace with hash
$pattern = '(href="style\.css\?v=)[^"]+(")'
$replacement = "`${1}$shortHash`$2"
$newContent = $htmlContent -replace $pattern, $replacement

# Save updated HTML
$newContent | Set-Content $htmlFile -NoNewline

Write-Host "✅ CSS version updated to: v=$shortHash" -ForegroundColor Green

# Show what changed
$currentVersion = if ($htmlContent -match 'href="style\.css\?v=([^"]+)"') { $matches[1] } else { "unknown" }
Write-Host "   Old version: v=$currentVersion" -ForegroundColor Yellow
Write-Host "   New version: v=$shortHash" -ForegroundColor Cyan
Write-Host ""
Write-Host "💡 Now run: git add . && git commit -m 'Update CSS version' && git push" -ForegroundColor Blue
