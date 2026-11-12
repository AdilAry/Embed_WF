# Data rules: [project name]
Read before changing code that loads, joins or computes data. Every rule here must hold in the code and be covered by a test.

## Sources
| Source | Where | Licence and attribution | Notes |
|---|---|---|---|
| [name] | [path or URL] | [licence, attribution text] | [version, size] |

## Units and formats
- [e.g. money in cents, local dates in Europe/Helsinki, timestamps in UTC].

## Keys and joins
- [e.g. table A → table B by column X; ambiguous joins are flagged, never forced].

## Timing
- [e.g. a historical decision uses only what was published before its decision time].

## Thresholds
- [name]: [value], from [source]. Named constants live in [file].
