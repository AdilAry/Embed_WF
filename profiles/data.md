# Profile: data project

Use this when the project loads, joins or computes on data. Paste the blocks below into the project's files, fill the brackets, and delete this heading text. Copy `profiles/data-rules.md` from the kit to `docs/data.md`.

## Into AGENTS.md, as its own section
```
## Data
- **Source:** [files, API or sensor, and where they live].
- **Rules that always hold:** [at most 5 lines; anything longer goes in docs/data.md].
- **Licences:** [each source, its licence and the attribution text].
- **Permission to send data to an external AI:** [none: work from column names and synthetic fixtures | granted by <owner> for <what>].
- `data/raw/` is never committed if it holds personal, company-internal or unlicensed data.
```

## Into AGENTS.md, under "Read only when needed"
```
| `docs/data.md` | before changing code that loads, joins or computes data |
```

## Into docs/plan.md
In the foundation section:
```
- Drop physically implausible values and log how many. Before choosing the unit of analysis, count how many units have enough samples; if most don't, tell me.
```
In the core-feature section:
```
- If it ranks or shortlists: read the top results as the user would. They must make sense for that use, in that order.
- If it exports: open the file where users will, with their locale settings (delimiter, decimal mark, encoding). If that can't be tested, list it as a limit.
```
If the product calls an AI:
```
- **AI in the product:** [provider, key name in .env, notes file in docs/]. Rules and real data decide; AI only explains results the code has verified. It works without keys: cached answers, labelled as cached. Read generated text for meaning as well as numbers: it must not claim more than the data shows.
```
