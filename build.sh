#!/bin/zsh
# Build the CV PDFs locally:  ./build.sh            (all)
#                             ./build.sh CV_condensed.tex
# 1. regenerates publications_list.tex from publications.bib (if present)
# 2. compiles with LuaLaTeX into build/, copies PDFs to pdf/ and the Applications folder
cd "${0:A:h}"
OUT=/Users/marrewijk/Documents/Aplications/CV
mkdir -p pdf build "$OUT"
[[ -f publications.bib ]] && python3 scripts/make_publications.py
targets=("$@"); (( ${#targets} )) || targets=(CV_condensed.tex Publications.tex)
for f in $targets; do
  [[ $f == Publications.tex && ! -f publications_list.tex ]] && { echo "skip $f (no publications.bib yet)"; continue; }
  lualatex -interaction=nonstopmode -halt-on-error -output-directory=build "$f" >/dev/null 2>&1 \
    && lualatex -interaction=nonstopmode -output-directory=build "$f" >/dev/null 2>&1 \
    && cp "build/${f:r}.pdf" pdf/ && cp "build/${f:r}.pdf" "$OUT/" \
    && echo "ok   $f ($(pdfinfo build/${f:r}.pdf | awk '/Pages/{print $2}') p)" \
    || { echo "FAIL $f"; grep -A3 '^!' "build/${f:r}.log" | head -8; }
done
