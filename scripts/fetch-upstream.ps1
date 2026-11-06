 $ErrorActionPreference = 'Stop'
 $repoRoot = Split-Path -Parent $PSScriptRoot
 $manifest = Get-Content -LiteralPath (Join-Path $repoRoot 'cad/source/manifest.json') -Raw | ConvertFrom-Json
 foreach ($entry in $manifest.files) {
     $target = Join-Path $repoRoot $entry.local_path
     New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target) | Out-Null
     $url = "https://raw.githubusercontent.com/kumamuk-git/roBa/$($manifest.commit)/$($entry.upstream_path)"
     Invoke-WebRequest -Uri $url -OutFile $target
     $actual = git hash-object --no-filters -- $target
     if ($actual -ne $entry.git_blob_sha1) { throw "Hash mismatch: $($entry.local_path)" }
     Write-Output "Verified: $($entry.local_path)"
 }
