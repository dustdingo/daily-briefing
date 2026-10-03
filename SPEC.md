# Daily briefing: handoff spec

This kit replaces the hand-built briefing page with a fixed design plus one data file.
The daily task (on the Mac Mini) only writes `briefing-data.json`. It never edits the design.

## Files

| File | Who touches it | What it is |
|---|---|---|
| `template.html` | nobody (design) | The page: layout, colors, tabs, rendering code. Has two placeholders, `__TITLE__` and `__BRIEFING_DATA__`. |
| `build.py` | nobody | Validates the data, injects it into the template, writes `index.html`, optionally commits and pushes. Python 3 standard library only. |
| `briefing-data.json` | **the daily task** | All of today's content. Replaced in full each morning. |
| `index.html` | generated | The published page. Never edit by hand. |

Put all four in the root of the GitHub Pages repo (`dustdingo/daily-briefing`) next to the existing `index.html`. The first run overwrites the old page.

## Daily run (what the scheduled task does)

1. Gather the day's content as it does today (calendar, Things tasks, Toggl, MyFitnessPal, weather, devotional, and so on).
2. Write a complete `briefing-data.json` in the schema below. Replace the whole file; do not patch it.
3. From the repo folder run:
   ```
   python3 build.py --push
   ```
   - Exit code 0: built and pushed (or nothing changed).
   - Exit code 2: the data failed validation. The problems are printed one per line. Fix the JSON and re-run. Nothing is written or pushed when validation fails.
4. GitHub Pages republishes within a minute or two.

`python3 build.py --check` validates only. `python3 build.py` builds without pushing.

### Mac Mini notes
- The task runs on the Mac Mini, so the repo clone, `git` credentials and `python3` must live there. Use the same clone and credentials the current task already pushes with.
- `build.py` runs `git add`, `git commit` and `git push` in the folder that holds `index.html`. If the existing task pushes a different way (a script, `gh`, a different branch), keep that mechanism: run `python3 build.py` (no `--push`) and then your existing push step.
- No packages to install. If `python3` is not found, install Apple's command line tools (`xcode-select --install`).
- Fonts load from Google Fonts at view time. The page needs internet on the iPad or desktop to get them; it falls back to system fonts offline.

## Rules for the data

- **Write real data only.** Missing facts are omitted or set to an empty list, not invented.
- **Plain text only.** No HTML or markdown. The page escapes everything.
- **Roles.** Wherever a field is called `role`, use exactly one of: `Speaking`, `SPS`, `Teaching`, `Seacoast`, `Freelance`, `Personal`. Each has a fixed color and icon in the design. Fields marked "optional role" may be `null`.
- **Numbers are numbers** (`20.0`, not `"20.0h"`) wherever the schema says number.
- **Lists can be any length**, except where a minimum is noted. The layout reflows.
- **Keep copy short.** Cards are sized for one to three sentences.
- **Devotional full text** (see `reading.devotional.fullText`) is optional. See "Devotional text" below.

## Schema (`schemaVersion: 1`)

```
{
  "schemaVersion": 1,
  "title": "Briefing 10-03",              // browser tab title
  "date": "2026-10-03",                    // ISO date, used for the commit message
  "dateLabel": "Saturday, October 3",      // heading on Today
  "generatedAt": "Saturday, October 3, 2026 at 4:22 AM ET",
  "today": { ... }, "brief": { ... }, "reading": { ... },
  "fitness": { ... }, "time": { ... }, "week": { ... }
}
```

### today  (tab: Today)
```
"weather": { "hi": 82, "lo": 72, "feelsLike": "~87°", "humidity": "94%", "summary": "one or two sentences" }
"gamePlan": [ { "label": "Protect", "tone": "ok|warn|neutral", "text": "" } ]        // usually 4: Protect, Pressure, Tonight, Watch out
"priorities": [ { "title": "", "role": "Role", "due": "Overdue (Oct 2)", "overdue": true, "next": "next action" } ]   // usually 3
"sequenceNote": "Optional work block 7–11 AM, then family.",                          // optional
"sequence": [ { "time": "7:00–9:00 AM", "what": "" } ]
"headsUp": [ { "kind": "Overdue|Calendar|Nutrition|...", "role": "Role or null", "text": "" } ]
```

### brief  (tab: Brief)
```
"morningRead": [ "paragraph", "paragraph" ]
"watchOut": "short phrase, shown as 'Watch out for: …'"                  // optional
"forgetting": [ { "role": "Role or null", "title": "", "text": "" } ]
"whatsNext": [ { "title": "", "text": "" } ]                              // numbered automatically
"opportunities": [ { "role": "Role", "title": "", "text": "" } ]         // role picks the icon and color
"projectCards": [ { "role": "Role", "level": "Critical|High|Medium|Low", "why": "", "best": "", "watch": "" } ]
```

### reading  (tab: Reading)
```
"devotional": {
  "series": "My Utmost for His Highest", "date": "Oct 3", "title": "", "reference": "Mark 9:29",
  "summary": [ "short paragraph", ... ],        // shown when fullText is empty
  "fullText": [ "paragraph", ... ],             // optional; when non-empty it replaces the summary
  "url": "https://…"                            // optional; adds a "Read the full entry" button when fullText is empty
}
"prayer": [ "name", ... ]
"creative": { "date": "Oct 3", "title": "", "summary": "", "paragraphs": [ ... ], "question": "" }   // use summary OR paragraphs; question optional
```

### fitness  (tab: Fitness, three views: Overview / Workout / Meals)
```
"eyebrow": "Saturday · Rest day"
"stats": [ { "value": "228.6", "label": "lb weekly avg" } ]               // 3 or 4 tiles
"progress": [ { "label": "Weight", "text": "" } ]                        // Progress check rows
"closing": "one-line takeaway"                                            // optional
"goals": [ { "name": "Strength sessions", "done": 2, "total": 3 } ]
"goalsNote": ""                                                           // optional
"workout": { "label": "Today's workout · Saturday", "title": "Rest day", "lines": [ "", "" ] }
"split": [ { "day": "Mon", "what": "Chest & Biceps" } ]
"splitNote": ""                                                           // optional
"strengthNotes": [ "" ]
"macroTargets": { "cal": 2308, "protein": 200, "carbs": 215, "fat": 72 }
"macroNote": "Rest day: no workout window needed."                       // optional
"meals": [ { "slot": "Breakfast", "what": "", "cal": 210, "protein": 28, "carbs": 2, "fat": 10 } ]   // totals are calculated by the page
"pack": { "count": "1 meal away from home", "items": [ { "slot": "Snack 2", "when": "Linkin Park, 2:00 PM", "text": "" } ] }   // optional
"dinnerCall": { "title": "Dinner call: chicken", "text": "" }            // optional
"alert": { "title": "Nutrition", "text": "" }                            // optional; shown as a warning card. Use null when there is none.
```

### time  (tab: Time)
```
"guidingOrder": ""                                                        // optional
"periods": [                                                              // first period is shown by default; any number allowed
  { "id": "week", "label": "This week", "total": "32.7", "caption": "Oct 3 week · logged so far",
    "note": "the takeaway paragraph",
    "rows": [ { "name": "ACEP", "hours": 20.0, "role": "Freelance" } ],   // role picks the bar color; null = neutral gray (e.g. Music)
    "days": [ { "day": "Mon", "hours": 7.3 } ]                            // optional bar chart; null to omit
  }
]
```
Color mapping used so far: ACEP → Freelance, Seacoast Church → Seacoast, Moody and CSU → Teaching, Speaking → Speaking, Smartphone Storytellers → SPS, Music → null.

### week  (tab: Overview, two views: Focus & projects / Calendar)
```
"rangeLabel": "Week of Sep 28 – Oct 4"
"focus": [ { "role": "Role", "title": "", "text": "", "when": "Oct 9", "overdue": false } ]
"overdue": [ { "title": "", "role": "Role", "due": "Oct 2" } ]
"projects": [ {
    "role": "Role", "area": "Display name",
    "roleEvaluation": "the role evaluation sentence",
    "blocks": [ { "label": "Active projects|This week|This month|Open (no deadline)|Suggestions", "lines": [ "", "" ] } ]
} ]
"calendar": [ { "kicker": "This week|Next 30 days", "title": "Week of Oct 5",
    "rows": [ { "day": "Mon 10/5", "time": "9:00 AM", "title": "", "fyi": false } ] } ]   // leave "day" empty for a second event on the same day
"calendarNote": ""                                                        // optional
```

## Devotional text

The `fullText` field exists so your task can fill it with the day's entry if you want it shown in full on the Reading tab. The kit does not include any devotional text. Two things to know:
- GitHub Pages is public. Anyone with the link can read what the page contains, including a full copyrighted entry. Your current page already works this way, so this is the same exposure, not a new one.
- If you would rather not publish it, leave `fullText` as `[]` and the page shows the short summary and a link instead.

## Dark mode and layout

- The page follows the device's light or dark setting automatically.
- Phone and iPad portrait: bottom tab bar. iPad landscape, iPad Pro and desktop: left sidebar, with cards flowing into two or three columns.
- Open a tab directly with a link ending in `#brief`, `#reading`, `#fitness`, `#time`, `#week` or `#today` (handy as an iPad home-screen bookmark).

## Changing the design later

Design changes happen in `template.html` (ask Claude to change it, then replace the file). The daily task never needs to know. If a change adds or renames data fields, `schemaVersion` and this spec change with it.
