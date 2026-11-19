#!/bin/zsh
# Build all draft CVs and copy PDFs to drafts/pdf and the Applications folder.
cd "${0:A:h}"
OUT=/Users/marrewijk/Documents/Aplications/CV/drafts
mkdir -p pdf build "$OUT"
for f in ${@:-CV_*.tex}; do
  lualatex -interaction=nonstopmode -halt-on-error -output-directory=build "$f" >/dev/null 2>&1 \
    && lualatex -interaction=nonstopmode -output-directory=build "$f" >/dev/null 2>&1 \
    && cp "build/${f:r}.pdf" pdf/ && cp "build/${f:r}.pdf" "$OUT/" && echo "ok   $f ($(pdfinfo build/${f:r}.pdf | awk '/Pages/{print $2}') p)" \
    || { echo "FAIL $f"; grep -A3 '^!' "build/${f:r}.log" | head -8; }
done
