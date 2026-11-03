# Research tools: sources and scope

## USDA texture

- USDA NRCS Soil Texture Calculator: https://www.nrcs.usda.gov/resources/education-and-teaching-materials/soil-texture-calculator
- USDA NRCS National Agronomy Manual, Part 508, Soil texture: https://www.nrcs.usda.gov/sites/default/files/2022-10/National-Agronomy-Manual.pdf
- Reference implementation for comparison: NCSS AQP `ssc_to_texcl`, https://ncss-tech.github.io/aqp/reference/texture.html

Uses the 12 basic USDA fine-earth classes, excluding sand-size subclasses and coarse-fragment modifiers. Particle limits: 0.05–2 mm sand, 0.002–0.05 mm silt, <0.002 mm clay. Chinese names are presentation aids; English class names identify the system. Classification does not constitute health or suitability assessment. Original values remain in result exports; normalization requires explicit consent in the form. Polygon vertices are drawn from the numerical class boundaries. Boundary inclusivity is specified in texture.js and displayed in the UI.

## Data audit

- NIST box plot fences: https://www.itl.nist.gov/div898/handbook/eda/section3/boxplot.htm
- CSV quoting: RFC 4180, https://www.rfc-editor.org/rfc/rfc4180
- Excel parser: read-excel-file 9.3.14, MIT, https://www.npmjs.com/package/read-excel-file/v/9.3.14

Missing markers, duplicate detection and manual bounds are project quality-control conventions, not scientific or regulatory thresholds. IQR uses linear interpolation at (n−1)p and 1.5×IQR fences, skips mixed-unit columns, n<4 and IQR=0. It never removes, imputes or normalizes source cells. Excel cached values are read without recalculating formulas. Problem CSV exports neutralize spreadsheet formula prefixes with an apostrophe. No file or data request is sent to the backend.

The Windows-only knowledge-vault paths in AGENTS.md were unavailable on this Mac. No project experimental conclusions were inferred from them. Formal use still requires confirmation of the source sample's particle-size system, preparation and measurement method.
