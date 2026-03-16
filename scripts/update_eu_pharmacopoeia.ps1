param(
    [string]$RawDir = "data/raw/eu_pharmacopoeia"
)

$ErrorActionPreference = "Stop"

New-Item -ItemType Directory -Path $RawDir -Force | Out-Null
python -m pipelines.ingestion.ingest_documents --raw-dir $RawDir
python -m pipelines.indexing.build_vector_index

Write-Output "EU Pharmacopoeia update completed from: $RawDir"
