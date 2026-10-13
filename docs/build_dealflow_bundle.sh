#!/usr/bin/env bash
# Rebuild all Deal Flow OS Phase 0 PDFs from their Markdown sources and repackage the zip.
# Run this whenever any DEALFLOW_*.md changes:  bash /app/docs/build_dealflow_bundle.sh
set -euo pipefail
cd "$(dirname "$0")"

declare -A DOCS=(
  [DEALFLOW_INTEGRATION_READINESS]="CAUL AI x Deal Flow OS - Integration Readiness (Phase 0)"
  [DEALFLOW_ACCESS_REQUEST]="Deal Flow OS - Access & Approval Request"
  [DEALFLOW_METRICS_API_REQUEST]="Deal Flow OS - Metrics API + Key Build Request"
  [DEALFLOW_CAUL_CONSUMER_SPEC]="CAUL AI - Deal Flow OS Consumer Spec (Phase 1 pre-spec)"
)

for base in "${!DOCS[@]}"; do
  python md_to_pdf.py "${base}.md" "${base}.pdf" "${DOCS[$base]}"
done

rm -f CAUL_DEALFLOW_PHASE0_BUNDLE.zip
zip -j CAUL_DEALFLOW_PHASE0_BUNDLE.zip \
  DEALFLOW_INTEGRATION_READINESS.pdf DEALFLOW_INTEGRATION_READINESS.md \
  DEALFLOW_ACCESS_REQUEST.pdf DEALFLOW_ACCESS_REQUEST.md \
  DEALFLOW_METRICS_API_REQUEST.pdf DEALFLOW_METRICS_API_REQUEST.md \
  DEALFLOW_CAUL_CONSUMER_SPEC.pdf DEALFLOW_CAUL_CONSUMER_SPEC.md
echo "Bundle rebuilt: $(pwd)/CAUL_DEALFLOW_PHASE0_BUNDLE.zip"
