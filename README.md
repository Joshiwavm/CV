# CV — Joshiwa van Marrewijk

Live: **https://joshiwavm.github.io/CV/** (condensed CV) ·
[publication list](https://joshiwavm.github.io/CV/vanMarrewijk_publications.pdf)

Every push to `main` (also from Overleaf's GitHub sync) rebuilds both PDFs via
`.github/workflows/publish-cv.yml`. Compile with **LuaLaTeX**.

| File | What |
|---|---|
| `CV_condensed.tex` | condensed CV (main document) — text lives in `content_condensed.tex` |
| `Publications.tex` | publication list — entries in `publications_list.tex` (generated) |
| `publications.bib` | SciX/ADS BibTeX export; paste a fresh export over it to update |
| `scripts/make_publications.py` | builds `publications_list.tex` from the bib (groups by author position, filters proceedings/datasets/software/errata) |
| `styles/` | layout (`B2_airy.tex`), shared settings, journal macros |
| `Marrewijk_CV.tex`, `Resume Sections/`, `fed-res.cls` | the old (original Overleaf) CV |
| `build.sh` | local build: regenerates the list, compiles, copies PDFs to `pdf/` |

Note: Overleaf cannot run Python. After editing `publications.bib` in Overleaf,
the live PDF is still correct (CI regenerates the list); the Overleaf preview
updates after you pull the regenerated `publications_list.tex` or run `./build.sh` locally.
