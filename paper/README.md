# Paper (ISSTA 2027 submission)

- `main.tex`: the paper, `\documentclass[acmsmall,screen,review,anonymous]{acmart}` as the ISSTA 2027 CFP requires
  (single column; 18 pages strict excluding references and Data Availability).
- `references.bib`: 24 entries. Entries marked `TODO` must be checked against the publisher or arXiv record before
  submission.
- `figures/overview.png`: Figure 1. Replace with a vector PDF before submission.
- Red `\ph{...}` marks are placeholders, filled after the 13 Dec run freeze.
- `doc2tex.py`: converts the Paper Draft doc's XML into `main.tex` (`python doc2tex.py paper.xml main.tex`). From now
  on, edit `main.tex` directly; the converter is kept only to show how it was produced.

Build: `latexmk -pdf main.tex` (TeX Live with acmart and libertine, or upload the folder to Overleaf).
