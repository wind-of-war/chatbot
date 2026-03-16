param(
    [string]$Manifest = "data/sources/regulatory_docs_sources.json",
    [string]$RawRoot = "data/raw",
    [bool]$FullRebuild = $true
)

$python = "python"
if (Test-Path ".venv\\Scripts\\python.exe") {
    $python = ".venv\\Scripts\\python.exe"
}

Write-Output "[1/4] Download regulatory sources..."
& $python scripts/download_regulatory_sources.py --manifest $Manifest --raw-root $RawRoot

if ($FullRebuild) {
    Write-Output "[2/4] Full rebuild enabled: clean processed/embeddings..."
    Get-ChildItem data\\processed\\*.txt -ErrorAction SilentlyContinue | Remove-Item -Force
    Get-ChildItem data\\embeddings\\*.vec -ErrorAction SilentlyContinue | Remove-Item -Force
} else {
    Write-Output "[2/4] Full rebuild disabled: keep existing processed/embeddings..."
}

Write-Output "[3/4] Ingest PDF documents..."
& $python -m pipelines.ingestion.ingest_documents --raw-dir $RawRoot

Write-Output "[4/4] Build vector index..."
& $python -m pipelines.indexing.build_vector_index

Write-Output "Regulatory corpus update completed."
