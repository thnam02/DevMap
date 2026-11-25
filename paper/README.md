# Paper (ISSTA 2027 submission)

- `main.tex`: the paper, `\documentclass[acmsmall,screen,review,anonymous]{acmart}` as the ISSTA 2027 CFP requires
  (single column; 18 pages strict excluding references and Data Availability).
- `references.bib`: 24 entries. Entries marked `TODO` must be checked against the publisher or arXiv record before
  submission.
- `figures/overview.png`: Figure 1. Replace with a vector PDF before submission.
- Red `\ph{...}` marks are placeholders, filled after the 13 Dec run freeze.
- Regenerate from the Paper Draft doc (the doc is the source while the text is still moving):
  `python doc2tex.py paper.xml main.tex && python restyle.py main.tex`. `doc2tex.py` converts the doc's XML;
  `restyle.py` applies the emphasis conventions of recent ISSTA/ICSE RTS papers (`\tool` in small caps, run-in
  `\para` headings, RQ list, "Answer to RQn" boxes). Both assert on the text they change, so a reworded passage
  stops them instead of being skipped silently.

Build: `latexmk -pdf main.tex` (TeX Live with acmart and libertine, or upload the folder to Overleaf).
