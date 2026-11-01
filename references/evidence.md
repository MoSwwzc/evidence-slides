# Source and evidence handling

## Source roles
Classify each user file as content evidence, narrative/style inspiration, visual template, or user project data. Do not treat a writing style guide as a factual source for the new paper. If roles conflict, record the conflict or ask only when absolutely necessary.

## Source reading
Read abstract, introduction, model/problem statement, datasets, main results, limitations, figure legends, appendices, and supplementary material. Use exact figure/table identifiers. Check negative results and ablations instead of only the abstract. For PPTX, inspect speaker notes and embedded media; old slide content may be outdated.

## Figure candidates
Image extraction is only a first pass. PDF figures may be vector objects, composites of raster figures and labels, or span several regions. Render a page and crop the complete scientific figure at sufficiently high quality when extraction is incomplete. Do not use a clipped chart with missing axes or legends. Do not overwrite figure labels or scientific colors for aesthetic consistency. Keep both the original media and cropped display asset and label each accordingly.

## Tables and re-plots
Recover exact table headers, units, metric directions, error ranges, sample sizes, and row/column groupings. Re-layout tables as editable PPT tables only after checking every visible numeric entry. Data plots may be recreated only from verified exact tabular values; identify the plot as derived and retain source. Do not digitize noisy screenshots and pretend the approximation is exact.

## Claim ledger
For every substantive claim record: claim id, wording, fact/hypothesis/interpretation/teaching-example status, source ids, locator (page, figure, table, equation), relevant data conditions, and caveats. Treat wording such as statistically significant, causation, clinically valid, all datasets, fully automated, or state-of-the-art as high scrutiny. Do not attach a source id that does not support the claim.

## Rights
The user may have a right to use a figure in their private academic presentation while not having a right to redistribute it in an open GitHub repository. Public skill distribution should contain only original synthetic/test assets and code. PPT figures provided for generation remain outputs of an individual job and should credit sources in notes.
