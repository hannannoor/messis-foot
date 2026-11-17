param([switch]$VerifyOnly,
      [string]$TargetRunDirectory = 'C:\Users\leonj\Desktop\more than a hack data\run files')
$ErrorActionPreference = 'Stop'
$workspaceRoot = [System.IO.Directory]::GetParent($PSScriptRoot).FullName
$analysisRoot = Join-Path $workspaceRoot 'analysis'
$externalRoot = Join-Path $workspaceRoot 'external-reference'
$targetRun = [System.IO.Path]::GetFullPath($TargetRunDirectory)
$targetOutputs = Join-Path $targetRun 'outputs'
$targetResult = Join-Path $targetOutputs 'tactical-validated'
$targetValidation = Join-Path $targetOutputs 'tactical-validation'
$targetSource = Join-Path $targetRun 'football_pipeline.py'
$newSource = Join-Path $PSScriptRoot 'football_pipeline.py'
$oldSource = Join-Path $PSScriptRoot 'football_pipeline.pre_tactical.py'
$backupSource = Join-Path $targetRun 'football_pipeline.pre_tactical.py'
$manifestPath = Join-Path $targetValidation 'delivery-verification.json'
$modelId = 'be756fce3c52d21fda0b10d8a6026f78f9b7d599298d467d2d6ebc59efe9fd38'
function Hash([string]$path) { (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() }
$sourceHash = Hash $newSource
$oldHash = Hash $oldSource
$currentHash = Hash $targetSource
if ($currentHash -ne $oldHash -and $currentHash -ne $sourceHash) {
    throw 'Desktop source has changed since the pre-tactical snapshot; preserving that edit.'
}
$resultRoot = Join-Path $analysisRoot 'tactical-validated'
$proof = Get-Content -LiteralPath (Join-Path $analysisRoot 'four-goal-coverage-verification.json') -Raw | ConvertFrom-Json
$localReport = Get-Content -LiteralPath (Join-Path $resultRoot 'tactical_report.json') -Raw | ConvertFrom-Json
$heldout = Get-Content -LiteralPath (Join-Path $externalRoot 'reports\final-heldout.json') -Raw | ConvertFrom-Json
if (-not $proof.format_valid -or $proof.original_rows -ne 199319 -or $proof.model_id -ne $modelId -or
    $localReport.model_id -ne $modelId -or $localReport.after.labels.X -ne 89200 -or
    $localReport.accuracy_measured -or $localReport.published_dead_interval_applied -or
    -not $heldout.complete -or $heldout.artifact_sha256 -ne $modelId) {
    throw 'Completed results did not pass installation preflight.'
}
if ((Hash (Join-Path $resultRoot 'submission.csv')) -ne $proof.submission_sha256) {
    throw 'Submission differs from the verified result.'
}
$copies = @()
foreach ($name in @('submission.csv','diagnostics.csv','report.json','tactical_report.json','unresolved_intervals.json')) {
    $copies += @{ Source=(Join-Path $resultRoot $name); Target=(Join-Path $targetResult $name) }
}
foreach ($name in @('provenance.json','figshare-manifest.json')) {
    $copies += @{ Source=(Join-Path $externalRoot $name); Target=(Join-Path $targetValidation $name) }
}
foreach ($name in @('baseline-development-validation.json','validation-selection.json','final-heldout.json',
                    'boundary-and-observation-diagnostics.json','team-occlusion-stress.json','provider-coordinate-audit.json')) {
    $copies += @{ Source=(Join-Path $externalRoot ('reports\'+$name)); Target=(Join-Path $targetValidation $name) }
}
foreach ($name in @('freeze-manifest.json','tactical-selected.json')) {
    $copies += @{ Source=(Join-Path $externalRoot ('frozen\'+$name)); Target=(Join-Path $targetValidation $name) }
}
foreach ($name in @('four-goal-coverage-verification.json','tactical-validation-overview.png','four-goal-completion-audit.json')) {
    $copies += @{ Source=(Join-Path $analysisRoot $name); Target=(Join-Path $targetValidation $name) }
}
foreach ($name in @('FOUR_GOALS.md','OFFICIAL_METRIC_LICENSE.txt')) {
    $copies += @{ Source=(Join-Path $PSScriptRoot $name); Target=(Join-Path $targetRun $name) }
}
foreach ($name in @('external-reference-audit.md','metric-reference-audit.md','four-goal-final-review.md')) {
    $copies += @{ Source=(Join-Path $PSScriptRoot ('docs\'+$name)); Target=(Join-Path $targetValidation $name) }
}
foreach ($name in @('four-goal-test-evidence.log','review-cli-red.log','review-cli-green.log','install-recovery-red.log','install-recovery-green.log')) {
    $copies += @{ Source=(Join-Path $PSScriptRoot $name); Target=(Join-Path $targetValidation $name) }
}
$copies += @{ Source=$newSource; Target=$targetSource }
$copies += @{ Source=$oldSource; Target=$backupSource }
foreach ($entry in $copies) {
    if (-not (Test-Path -LiteralPath $entry.Source -PathType Leaf)) { throw "Missing completed source: $($entry.Source)" }
}
$expectedTargets = @{}
foreach ($entry in $copies) { $expectedTargets[$entry.Target] = Hash $entry.Source }
# An interrupted first publication may lack its final manifest. Resume only exact
# expected files; never adopt unrelated names, links, subdirectories or edited bytes.
foreach ($destination in @($targetResult,$targetValidation)) {
    if (Test-Path -LiteralPath $destination) {
        $item = Get-Item -LiteralPath $destination
        if (-not $item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            throw "Delivery destination must be a real directory: $destination"
        }
        foreach ($child in Get-ChildItem -LiteralPath $destination -Force) {
            if ($child.FullName -eq $manifestPath) { continue }
            if ($child.PSIsContainer -or ($child.Attributes -band [IO.FileAttributes]::ReparsePoint) -or
                -not $expectedTargets.ContainsKey($child.FullName)) {
                throw "Unrelated delivery content is preserved: $($child.FullName)"
            }
            if (-not (Test-Path -LiteralPath $manifestPath) -and (Hash $child.FullName) -ne $expectedTargets[$child.FullName]) {
                throw "Partial delivery differs; preserving it: $($child.FullName)"
            }
        }
    }
}
if ($VerifyOnly -and -not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
    throw 'Verification requires the completed delivery manifest.'
}
if (Test-Path -LiteralPath $manifestPath) {
    $prior = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
    if ($prior.delivery -ne 'four-tactical-goals-v1' -or $prior.model_id -ne $modelId) {
        throw 'Existing delivery manifest has a different owner/model.'
    }
    foreach ($entry in $prior.files) {
        if (-not (Test-Path -LiteralPath $entry.target -PathType Leaf) -or (Hash $entry.target) -ne $entry.sha256) {
            throw "Installed delivery changed; preserving it: $($entry.target)"
        }
    }
}
foreach ($entry in $copies) {
    if ((Test-Path -LiteralPath $entry.Target) -and $entry.Target -ne $targetSource -and
        -not (Test-Path -LiteralPath $manifestPath) -and (Hash $entry.Target) -ne (Hash $entry.Source)) {
        throw "Existing target differs; preserving it: $($entry.Target)"
    }
}
if (-not $VerifyOnly) {
    # Stage on the destination volume and verify every byte before publishing.
    $stageDirectory = Join-Path $targetRun ('.tactical-delivery-'+[Guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $stageDirectory | Out-Null
    $index = 0
    foreach ($entry in $copies) {
        $entry.Stage = Join-Path $stageDirectory ([string]$index)
        Copy-Item -LiteralPath $entry.Source -Destination $entry.Stage
        if ((Hash $entry.Stage) -ne $expectedTargets[$entry.Target]) { throw 'Staged copy verification failed.' }
        $index++
    }
    New-Item -ItemType Directory -Path $targetResult,$targetValidation -Force | Out-Null
    # Backup first; executable last. Same-volume moves/replaces are atomic per file.
    $ordered = @($copies | Where-Object { $_.Target -eq $backupSource }) +
               @($copies | Where-Object { $_.Target -ne $backupSource -and $_.Target -ne $targetSource }) +
               @($copies | Where-Object { $_.Target -eq $targetSource })
    foreach ($entry in $ordered) {
        if (Test-Path -LiteralPath $entry.Target) {
            [IO.File]::Replace($entry.Stage,$entry.Target,[System.Management.Automation.Language.NullString]::Value)
        } else {
            [IO.File]::Move($entry.Stage,$entry.Target)
        }
    }
    # Only remove this now-empty staging directory; no recursive cleanup/rollback.
    Remove-Item -LiteralPath $stageDirectory
}
$records = foreach ($entry in $copies) {
    $expected = Hash $entry.Source
    if ((Hash $entry.Target) -ne $expected) { throw "Copy verification failed: $($entry.Target)" }
    @{ source=$entry.Source; target=$entry.Target; sha256=$expected }
}
$version = & 'C:\Python314\python.exe' $targetSource --version
if ($LASTEXITCODE -ne 0 -or ($version -join '') -notmatch '2026.11.05-tactical-validated') {
    throw 'Installed entry point version check failed.'
}
if (-not $VerifyOnly) {
    $manifest = @{ delivery='four-tactical-goals-v1'; model_id=$modelId; verified_at_utc=[DateTime]::UtcNow.ToString('o');
       source_sha256=$sourceHash; original_rows=199319; challenge_accuracy_measured=$false;
       scientific_status='Experimental provider-reference validation; coordinate-freezing artifact limits transfer';
       files=@($records) }
    $stagedManifest = Join-Path $targetRun ('.tactical-manifest-'+[Guid]::NewGuid().ToString('N')+'.tmp')
    $manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $stagedManifest -Encoding UTF8
    if (Test-Path -LiteralPath $manifestPath) { [IO.File]::Replace($stagedManifest,$manifestPath,[System.Management.Automation.Language.NullString]::Value) }
    else { [IO.File]::Move($stagedManifest,$manifestPath) }
}
Write-Output "Verified $(@($records).Count) delivered files, preserved the pre-tactical source and checked the installed version."
Write-Output "Delivery manifest: $manifestPath"
