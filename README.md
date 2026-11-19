# CV — Joshiwa van Marrewijk

Live: **https://joshiwavm.github.io/CV/** (condensed CV) ·
[publication list](https://joshiwavm.github.io/CV/vanMarrewijk_publications.pdf)

Every push to `main` (also from Overleaf's GitHub sync) rebuilds both PDFs via
`.github/workflows/publish-cv.yml`. Compile with **LuaLaTeX**.

```
CV_condensed.tex          main document: condensed CV
Publications.tex          main document: publication list
content/
  content_condensed.tex   the CV text (edit this)
  publications.bib        SciX/ADS BibTeX export (paste a fresh export over it)
  publications_list.tex   generated from the .bib, do not edit
styles/                   layout (B2_airy.tex), shared settings, journal macros
scripts/
  make_publications.py    builds content/publications_list.tex (groups by author
                          position; drops proceedings, datasets, software, errata)
old_cv/                   the original Overleaf CV (Marrewijk_CV.tex, pdfLaTeX)
```

Overleaf cannot run Python: after replacing `content/publications.bib` the live PDF
is correct (CI regenerates the list), but the Overleaf preview of the list only updates
once the regenerated `publications_list.tex` is in the project (run the script locally and push).
