# Recycle Bin Randomizer

Static web UI for [KVN AUST’s *YouTube’s Recycle Bin*](https://docs.google.com/document/d/1mV5PhumaIJ8mtH8XmohqXkk5fjK_HlqcineMccPQm5A) maps (Update 5.0): full lead listing + random search-string generator.

**Not affiliated with YouTube, Google, or KVN AUST.** Keyphrases and research credit belong to the original document and its contributors. This repo is an independent helper UI.

## Try it

Open `index.html` in a browser, or:

```bash
python3 -m http.server 8777 --bind 127.0.0.1
# http://127.0.0.1:8777/
```

## Links (original project)

- [Non-biased Video Searcher](https://kvnaust.github.io/YouTube-NonBiasedVideoSearcher/)
- [KVN AUST on YouTube](https://youtube.com/@kvnaust)
- [KVN AUST on X](https://x.com/mingkastermk)
- [Source Google Doc (maps)](https://docs.google.com/document/d/1mV5PhumaIJ8mtH8XmohqXkk5fjK_HlqcineMccPQm5A)

## Features

- Full listing: map, keyphrase/title, number range or date form, source, credit, example
- **Generate random search**: pick a lead, fill ranges / dates
- Zero-pad numeric fields to `X` width (`XXXX` → `0057`)
- Date templates: `YYYYMMDD`, `YYYY MM DD`, `YYYY-MM-DD`, `DDMMYYYY`, `DDMMYY` (e.g. `VDDMMYY`), `MM DD YYYY`, `YYYY MM`, `Month DD, YYYY`, bare `YYYY`, KO/JA forms
- Map filter + text filter; optional **NSFW-tagged** leads (off by default for random + table)
- Copy + open YouTube search

## Content notice

Obscure / zero-view uploads can include anything (private moments, junk, or NSFW). The source maps mark a handful of leads as NSFW (bitrate/playlist keywords, etc.). Those are excluded unless you opt in. Use at your own risk.

## Rebuild from the Google Doc

```bash
curl -sSL "https://docs.google.com/document/d/1mV5PhumaIJ8mtH8XmohqXkk5fjK_HlqcineMccPQm5A/export?format=txt" \
  -o /tmp/yt-recycle-doc.txt
python3 build_data.py      # → data.json, data.min.json
python3 build_index.py     # → index.html (embeds data)
python3 test_generation.py # rubric tests
```

Section line offsets in `build_data.py` may need updating if the doc structure changes drastically.

## Generator rules (summary)

| Pattern | Behavior |
|--------|----------|
| `XXXX` + range | Random int in range, **clamped** to field width, zero-padded to len(X) |
| `YYYYMMDD` etc. | Real calendar date (valid day-of-month) |
| Fixed string | Emitted as-is (optional quotes) |
| `(>2013)` notes | Year floor when parsed |

## Files

| File | Role |
|------|------|
| `index.html` | Self-contained UI |
| `data.json` | Parsed leads (readable) |
| `build_data.py` | Doc → JSON |
| `build_index.py` | JSON → HTML |
| `test_generation.py` | Padding/date/rubric tests |

## License

MIT for **this helper’s code and packaging**. The map content is sourced from KVN AUST’s public document—respect that work’s attribution when you republish lists or derivatives.
