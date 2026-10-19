Pieces, in file order

1. [··Big picture](#overview)
2. [0Top comment](#piece-0)
3. [1Tuning knobs](#piece-1)
4. [2Similarity](#piece-2)
5. [3Read](#piece-3)
6. [4Stitch](#piece-4)
7. [5The engine](#piece-5)
8. [6Pair tables](#piece-6)
9. [7Pair columns](#piece-7)
10. [8Pair rows](#piece-8)
11. [9Embeddings](#piece-9)
12. [10Pair cells](#piece-10)
13. [11Rescue](#piece-11)
14. [12One table pair](#piece-12)
15. [13Output files](#piece-13)
16. [14Previews](#piece-14)
17. [15Main + CLI](#piece-15)
18. [→One cell's journey](#journey)

# table-segment.py, piece by piece

The 15,000-foot view of the file with a diagram for every piece. "English" means the original document and "Spanish" the translation. The code works for any language pair.

English (original) Spanish (translation) Table outline / key step

**You stopped at Piece 5.** [Continue from the engine](#piece-5)

Whole file · 2,249 lines

## The big picture: how the data changes shape

Two Azure DI JSON files go in. A list of "this English cell = that Spanish cell" pairs comes out, plus a list of cells that found no partner. Each stage hands a smaller, more precise problem to the next.

```mermaid
flowchart TD
  J1["English Azure DI JSON"] --> S1
  J2["Spanish Azure DI JSON"] --> S1
  S1["Stage 1 · READ <br/>JSON to tables to cells"] --> P["Physical tables <br/>exactly as Azure DI saw them"]
  P --> S2["Stage 2 · STITCH <br/>glue tables cut by page breaks"]
  S2 --> L["Logical tables <br/>one real table each"]
  L --> S3["Stage 3 · PAIR TABLES"]
  S3 -->|"no partner"| U["Unmatched cells"]
  S3 -->|"table pairs"| S4["Stage 4 · PAIR COLUMNS"]
  S4 -->|"column map"| S5["Stage 5 · PAIR ROWS"]
  S5 -->|"row blocks"| S6["Stage 6 · PAIR CELLS"]
  S6 -->|"matched"| R["Cell records"]
  S6 -->|"leftovers"| S7["Stage 7 · RESCUE"]
  S7 -->|"rescued"| R
  S7 -->|"still alone"| U
  R --> S8["Stage 8 · JSON and CSV files"]
  U --> S8
  S8 --> S9["Stage 9 · Preview images and PDF"]
  PDF["The two PDFs"] -.->|"only needed for previews"| S9
```

Stages 3 to 7 zoom in step by step: tables, then columns, then rows, then cells, then a second chance for leftovers.

Piece 0 · lines 1–160

## The long comment at the top

The file explains itself here: the problem, the nine stages, the cell tags, the output files and the commands. The diagram shows where this script sits next to the existing pipeline.

```mermaid
flowchart LR
  subgraph PIPE["pipeline.py (already existed)"]
    RP["run_pipeline()"]
    INJ["inject_table_regions_into_page_outputs()"]
    GE["get_embeddings()"]
  end
  RP -->|"writes"| DI["two *_azure_di.json files"]
  RP -->|"writes"| SS["shared_state.json <br/>holds the PDF paths"]
  DI -->|"read by"| TS["table-segment.py <br/>separate script"]
  SS -->|"PDF paths for previews"| TS
  TS -->|"writes"| OUT["table_cell_alignments.json <br/>CSVs and previews"]
  OUT -.->|"same shape, could feed it <br/>not connected today"| INJ
  TS -.->|"only with the embeddings option"| GE
```

The dotted line to the pipeline is the important one: the output is shaped to fit, but nothing connects the two yet.

### Three things to know for your KT

- **It is a separate script.** It does not change `pipeline.py`. Someone still has to connect its output to the pipeline.
- **It cannot be imported normally.** Python cannot `import` a name with a hyphen. Lines 151–159 show how to load it by file path.
- **Its claimed results are unchecked.** The comment says 96% of English cells and 90% of Spanish cells get matched. That is what Copilot reported on your sample. Re-run it before you quote it.

Piece 1 · lines 184–247

## The tuning knobs

Every number that changes a matching decision sits in this one block, so nobody has to hunt through the code.

```mermaid
flowchart LR
  K["Tuning knobs"] --> W["Weights <br/>how much a clue counts <br/>e.g. numbers = 38%"]
  K --> M["Minimum scores <br/>accept a match only above this <br/>e.g. table pair at least 0.30"]
  K --> G["Gap costs <br/>price of leaving an item alone <br/>e.g. row gap = 0.34"]
```

Three kinds of knob. Gap costs stop the code from forcing bad matches, and also from giving up too easily.

| Group | Key knobs |
| --- | --- |
| Similarity | numbers 0.38 · shared words 0.22 · letter chunks 0.28 · length 0.12 |
| Stage 2 stitch | header at least 80% similar · column drift at most 6% · at most 2 pages later |
| Stage 3 tables | gap 0.30 · minimum pair 0.30 · 2:1 merge only if each part is at least 0.45 |
| Stage 4 columns | gap 0.35 · header 50% / body 30% / position 20% |
| Stage 5 rows | gap 0.34 · minimum 0.10 · up to 3 rows merge · content 82% / position 18% |
| Stages 6 and 7 | flag below 0.35 · rescue needs 0.30 and at most 28% of table height apart |

These values were tuned on one English/Spanish sample. Another document type or language pair may need different values.

Piece 2 · lines 251–391

## The similarity toolkit

One question: **how alike are these two texts, when they are in different languages?** The answer is a score from 0 to 1. No translation and no internet are used.

```mermaid
flowchart LR
  A["Text A <br/>'$25 copay/visit'"] --> C["Clean up <br/>remove accents, lowercase, <br/>extra spaces, :selected:"]
  B["Text B <br/>'Copago de $25/visita'"] --> C
  C --> N["Numbers · 38%"]
  C --> T["Shared words · 22%"]
  C --> G["3-letter chunks · 28%"]
  C --> L["Length · 12%"]
  N --> D{"Do numbers or words <br/>appear on either side?"}
  T --> D
  D -->|"yes: keep the clue"| BL["Weighted blend"]
  D -->|"no: drop it, share its weight"| BL
  G --> BL
  L --> BL
  BL --> S["Score from 0 to 1"]
```

Chunks and length always count. Numbers and words count only when at least one side has them, so a cell with no digits is not punished.

### How the letter chunks catch similar words

"specialist"

spepececiciaialalilisist

"especialista"

espspepececiciaialalilisiststa

8 of the chunks are shared (in blue), so the two words score high even though they are in different languages.

### How numbers are compared

| English | Spanish | Read as | Match? |
| --- | --- | --- | --- |
| `$87.50` | `$87,50` | 87.5 and 87.5 | yes |
| `20%` | `$20` | percent 20 and plain 20 | no |

The limit: this works because English and Spanish share an alphabet. For Korean or Hindi, words and chunks share nothing, so only numbers and position are left. That is why the optional embeddings exist ([Piece 9](#piece-9)).

Piece 3 · Stage 1 · lines 395–639

## Read: JSON into tables and cells

```mermaid
flowchart TD
  J["Azure DI JSON"] --> T["For each table <br/>name it t1, t2, t3 in document order"]
  T --> PG["Find its page <br/>which page its text falls on, <br/>else use its position box"]
  PG --> C["For each cell"]
  C --> E{"Has real text?"}
  E -->|"no: empty or only :selected:"| SK["Skip it"]
  E -->|"yes"| BX["Position box <br/>inches times 72 = PDF points"]
  BX --> TG["Give it a tag <br/>p2t3c17 = page 2, table 3, cell 17"]
  TG --> CL["Cell object <br/>text clues worked out once"]
  CL --> PT["Added to its PhysicalTable"]
```

Key names are read in both spellings (row_index and rowIndex), because different Azure SDK versions write them differently.

### The three containers

```mermaid
flowchart LR
  subgraph LT["LogicalTable olt1: one real table"]
    direction LR
    subgraph P1["PhysicalTable t2 · page 2"]
      direction TB
      c1["Cell p2t2c1"]
      c2["Cell p2t2c2"]
      c3["more cells"]
    end
    subgraph P2["PhysicalTable t3 · page 3"]
      direction TB
      c4["Cell p3t3c1"]
      c5["more cells"]
    end
  end
```

A Cell is one box. A PhysicalTable is a table exactly as Azure DI returned it. A LogicalTable is one or more physical tables glued together, and Stage 2 fills it.

The cell number in a tag is Azure's own order. Skipped empty cells leave gaps (c4, c6 with no c5). That is normal, not a bug.

Piece 4 · Stage 2 · lines 643–709

## Stitch: repair tables cut by page breaks

The script walks through the tables in reading order. For each one it asks: is this the rest of the previous table?

```mermaid
flowchart TD
  N["Next table in reading order"] --> Q1{"Same number of columns <br/>as the previous table?"}
  Q1 -->|"no"| NEW["Start a new logical table"]
  Q1 -->|"yes"| Q2{"On a later page, <br/>at most 2 pages later?"}
  Q2 -->|"no"| NEW
  Q2 -->|"yes"| Q3{"Header repeated? <br/>header text at least 80% similar"}
  Q3 -->|"yes"| GLUE["Glue it onto the previous table"]
  Q3 -->|"no"| Q4{"Columns at the same x positions? <br/>drift at most 6% of table width"}
  Q4 -->|"yes"| GLUE
  Q4 -->|"no"| NEW
  GLUE --> LOG["Decision and reason saved in the report"]
  NEW --> LOG
```

It only compares with the table just before. Every decision and its reason goes into the report, so a wrong glue is easy to trace.

### After gluing, rows are renumbered end to end

```mermaid
flowchart LR
  subgraph A["t2 · page 2"]
    direction TB
    a0["row 0 · header"]
    a1["rows 1 to 6"]
  end
  subgraph L["olt1 · logical rows"]
    direction TB
    l0["0 · header"]
    l1["1 to 6"]
    l7["7 · repeated header, set aside"]
    l8["8 to 16"]
  end
  subgraph B["t3 · page 3"]
    direction TB
    b0["row 0 · header printed again"]
    b1["rows 1 to 9"]
  end
  a0 --> l0
  a1 --> l1
  b0 -->|"marked repeated"| l7
  b1 -->|"plus 7"| l8
```

The second part's rows continue after the first part's. The header printed again on page 3 is page decoration, so it is kept out of row matching and paired separately later ([Piece 10](#piece-10)).

Logical tables get names like `olt1` (original logical table 1) and `tlt1` (translated logical table 1).

Piece 5 · lines 713–836 You stopped here

## The engine: pair two ordered lists without crossing

This is the most important piece. Stages 3, 4 and 5 all use it: for tables, for columns and for rows.

Picture two queues of people, one English and one Spanish, standing in the same order. You walk down both queues. At every step you pick one move, and you never pair someone near the front of one queue with someone near the back of the other.

```mermaid
flowchart TD
  P["Next English item and next Spanish item"] --> C1["Pair them <br/>gain: their score"]
  P --> C2["Skip the English item <br/>lose: gap cost"]
  P --> C3["Skip the Spanish item <br/>lose: gap cost"]
  P --> C4["Group 2 or 3 on one side with 1 on the other <br/>gain: score times size, minus a small merge penalty"]
  C1 --> B["Try every path efficiently, <br/>keep the one with the best total"]
  C2 --> B
  C3 --> B
  C4 --> B
  B --> O["Blocks: ONE_TO_ONE · ONE_TO_MANY · MANY_TO_ONE <br/>ORIGINAL_ONLY · TRANSLATED_ONLY"]
```

The four moves. A pair scoring below the stage's minimum is never allowed. This method is called dynamic programming; Git's diff and DNA alignment use the same idea.

### What a finished alignment looks like

OCR split one English row into two, so they merge onto one Spanish row (blue). One Spanish row has no English partner, so it is skipped and the gap cost is paid. No line ever crosses another. The row texts are an illustration, not real output.

### Helper 1: the position prior

Two items at the same relative spot get 1.0, for example both 30% of the way down their lists. The value drops as they drift apart. This lets rows with no shared words still land in the right place, held between the rows around them that do match.

### Helper 2: mutual-best sharpening (the "ratio test")

Cross-language scores bunch together, mostly between 0.3 and 0.6, so a clear winner and a runner-up look alike. Each score is multiplied by (its score ÷ the best competing score in its row or column). The winner keeps its score and runners-up shrink.

| Pair | Before | Best competitor | After | Against the 0.30 cut-off |
| --- | --- | --- | --- | --- |
| English A ↔ Spanish X | 0.60 | 0.60 | 0.60 | can pair |
| English A ↔ Spanish Y | 0.40 | 0.60 | 0.27 | blocked |
| English B ↔ Spanish X | 0.35 | 0.60 | 0.20 | blocked |
| English B ↔ Spanish Y | 0.55 | 0.55 | 0.55 | can pair |

Example numbers worked through the real formula. Before sharpening, all four pairs were above 0.30. After it, only the two clear winners are.

Piece 6 · Stage 3 · lines 838–927

## Pair tables

```mermaid
flowchart LR
  E["Every English table"] --> SC["Score every pair"]
  S["Every Spanish table"] --> SC
  SC --> M["Score matrix"]
  M --> SH["Sharpen <br/>mutual-best"]
  SH --> EN["Engine <br/>gap 0.30 · minimum 0.30 <br/>2:1 only if each part at least 0.45"]
  EN -->|"paired"| TP["Table pairs <br/>go on to Stages 4 to 7"]
  EN -->|"left alone"| UN["All its cells unmatched <br/>e.g. Spanish-only tables"]
  M -.->|"saved"| REP["Report: table_score_matrix"]
```

When two tables were paired wrongly, open the saved score matrix: it shows what the runner-up scored.

```mermaid
pie showData title What a table-pair score is made of
  "Header text" : 45
  "All the table's text" : 30
  "Shape: columns and cell count" : 15
  "Position in the document" : 10
```

A table with no partner is not an error. The Spanish sample has tables that the English version writes as normal paragraphs, and the pipeline's paragraph matching handles that text. A 2:1 pairing is allowed for the case where Stage 2 missed a continuation.

Piece 7 · Stage 4 · lines 929–977

## Pair columns

This runs inside one table pair. Each column is described by its header text and its body text. Score = 50% header + 30% body + 20% position. Columns pair 1:1 only and never merge.

```mermaid
flowchart LR
  subgraph EN["English columns"]
    direction TB
    e0["0 · Common Medical Event"]
    e1["1 · Services You May Need"]
    e2["2 · What You Will Pay"]
  end
  subgraph ES["Spanish columns"]
    direction TB
    s0["0 · Evento médico común"]
    s1["1 · Servicios que podría necesitar"]
    s2["2 · Lo que usted pagará"]
    s3["3 · Información importante"]
  end
  e0 -->|"0 to 0"| s0
  e1 -->|"1 to 1"| s1
  e2 -->|"2 to 2"| s2
```

The result is a column map, here {0→0, 1→1, 2→2}. The extra Spanish column 3 has no partner and is left alone. The column names are an illustration.

Piece 8 · Stage 5 · lines 979–1150

## Pair rows: the heart of the file

This is the part your old paragraph logic struggled with. `RowView` arranges a table as rows, then columns, then cells, leaving out repeated headers. Then every candidate row pairing gets a score.

### How two rows are scored

```mermaid
flowchart TD
  R["English row block and Spanish row block"] --> CM["Walk the columns <br/>using the Stage 4 column map"]
  CM --> CS["Compare the text in each column pair <br/>similarity toolkit"]
  CS --> WT["Weight by text length <br/>long description columns count more"]
  WT --> COV["Coverage check <br/>rows filling different numbers of columns lose a little"]
  COV --> MIX["82% content + 18% position"]
  MIX --> HD{"Header rows?"}
  HD -->|"both are headers"| PLUS["add 0.10"]
  HD -->|"one header, one not"| MINUS["subtract 0.12"]
  HD -->|"neither"| KEEP["no change"]
  PLUS --> SC["Row score, kept between 0 and 1"]
  MINUS --> SC
  KEEP --> SC
```

### The merge guard

The engine may merge up to 3 rows with 1, for rows that OCR split apart. But joining rows makes a score look better on its own, because more text means more chances to match a number. Without a guard the engine would merge everything, so every merge must pass this check:

```mermaid
flowchart TD
  M["Engine wants to merge rows <br/>e.g. 2 English rows with 1 Spanish row"] --> S1["Score the merged block"]
  S1 --> S2["Find the best plain 1:1 score <br/>among those same rows"]
  S2 --> F{"Is one of the rows a fragment? <br/>at most 60 characters, <br/>in at most half the usual columns"}
  F -->|"yes"| T1["Allow 0.02 slack"]
  F -->|"no"| T0["No slack"]
  T1 --> Q{"Merged score at least <br/>best 1:1 score minus slack?"}
  T0 --> Q
  Q -->|"yes"| OK["Merge offered to the engine"]
  Q -->|"no"| NO["Merge blocked"]
```

The real case it was built for: OCR split "Tier 2 – Your" and "Midrange-Cost Option" into two English rows, while the Spanish has one. A fragment is a tiny leftover row such as "especializada" alone on a line.

Piece 9 · lines 1152–1207

## Optional embeddings

```mermaid
flowchart TD
  F{"Started with --embeddings?"} -->|"no, the default"| LEX["Letter clues only <br/>runs offline, no credentials"]
  F -->|"yes"| LD["Load pipeline.py by its file path"]
  LD --> GE["Get Gemini embeddings <br/>for every cell's text"]
  GE --> OK{"Did it work?"}
  OK -->|"yes"| BL["Score = 55% meaning + 45% letter clues"]
  OK -->|"no"| MSG["Print 'embeddings unavailable'"]
  MSG --> LEX
```

Off by default, because the script then runs with no internet or credentials, and for Spanish the letter clues are enough. Useful for languages with a different alphabet.

Piece 10 · Stage 6 · lines 1209–1360

## Pair cells

```mermaid
flowchart TD
  RB["One matched row block"] --> COL["For each English column"]
  COL --> MAP{"Does it have a partner <br/>in the column map?"}
  MAP -->|"no"| SKIP["Skip it, rescue may try later"]
  MAP -->|"yes"| CNT{"How many cells on each side?"}
  CNT -->|"1 and 1"| O1["ONE_TO_ONE"]
  CNT -->|"1 and several"| O2["ONE_TO_MANY <br/>texts joined, scored together"]
  CNT -->|"several and 1"| O3["MANY_TO_ONE <br/>texts joined, scored together"]
  CNT -->|"several and several"| O4["Run the engine on the cells"]
  O1 --> REC["Records: at least one per English cell"]
  O2 --> REC
  O3 --> REC
  O4 --> REC
  REC --> FL{"Score below 0.35?"}
  FL -->|"yes"| LC["Flag LOW_CONFIDENCE <br/>means check it, not wrong"]
  FL -->|"no"| DONE["No flag"]
```

One record per cell, so no cell disappears silently. If 3 English cells match 1 Spanish cell, you get 3 records pointing at the same Spanish cell.

### What one record holds

#### Fields the pipeline already understands

- `original_cell_id`, `translated_cell_id`
- both texts, offsets and position boxes
- `mapping_source = "structural_table_segment"`
- `span_level_mapping`

#### Extra fields for checking

- `score`, `match_type`, `stage`
- `flags`, e.g. LOW_CONFIDENCE
- pages, table tags, row and column on both sides
- full id lists for merged groups

### Repeated headers are paired separately

```mermaid
flowchart LR
  subgraph EN["English"]
    eh["Header row <br/>printed once"]
  end
  subgraph ES["Spanish"]
    direction TB
    sh1["Header row · page 1"]
    sh2["Header printed again · page 2"]
  end
  eh -->|"row matching, Stage 5"| sh1
  eh -->|"repeated-header pairing <br/>English never repeats, so its first header stands in"| sh2
```

This is why the English header appeared twice in the test run. The 1st repeat pairs with the 1st repeat and the 2nd with the 2nd. If the counts differ they are spread evenly, and a side that never repeats lends its first header.

Piece 11 · Stage 7 · around lines 1360–1400

## Rescue: a second chance for leftovers

```mermaid
flowchart TD
  L["Each leftover English cell"] --> P["Compare with each leftover Spanish cell"]
  P --> F1{"Same column <br/>according to the column map?"}
  F1 -->|"no"| X["Not a candidate"]
  F1 -->|"yes"| F2{"At most 28% of the table's <br/>height apart?"}
  F2 -->|"no"| X
  F2 -->|"yes"| F3{"Score at least 0.30?"}
  F3 -->|"no"| X
  F3 -->|"yes"| C["Candidate pair"]
  C --> G["Sort all candidates, best first <br/>each cell can be used once"]
  G --> R["Rescued pairs, stage = rescue"]
  G --> U["Cells still alone go to the unmatched list"]
```

Piece 12 · lines 1465–1531

## One table pair, start to finish

`map_table_pair()` runs Stages 4 to 7 for one table pair. The order of calls:

```mermaid
sequenceDiagram
  participant Run as run_table_segmentation
  participant Pair as map_table_pair
  participant Col as align_columns
  participant Row as align_rows
  participant Hdr as map_repeated_headers
  participant Cel as _pair_cell_lists
  participant Res as rescue_unmatched_cells
  Run->>Pair: one English and one Spanish logical table
  Pair->>Col: Stage 4
  Col-->>Pair: column map
  Pair->>Row: Stage 5, using the column map
  Row-->>Pair: row blocks
  Pair->>Hdr: repeated headers
  Hdr-->>Pair: header records
  loop each row block and each column
    Pair->>Cel: Stage 6
    Cel-->>Pair: cell groups become records
  end
  Pair->>Res: Stage 7, the leftovers
  Res-->>Pair: rescued records and still-unmatched cells
  Pair-->>Run: records, column map, row log, unmatched cells
```

Piece 13 · Stage 8 · lines 1533–1691

## The output files

```mermaid
flowchart LR
  R["All cell records"] --> G["Group by English page and table <br/>same shape as pipeline.align_tables()"]
  G --> J1["table_cell_alignments.json <br/>the main result"]
  G --> C1["table_mappings.csv <br/>one row per pair"]
  R --> J2["table_segment_report.json <br/>the why"]
  U["Unmatched and low-confidence cells"] --> C2["table_anomalies.csv <br/>reviewer to-do list"]
  U --> J2
```

| File | What is in it | Open it when |
| --- | --- | --- |
| `table_cell_alignments.json` | All matched pairs plus summary numbers | You want the result, or other code needs it |
| `table_segment_report.json` | Stitching decisions, score matrix, row blocks, column maps, unmatched cells | You need to know why something matched or did not |
| `table_mappings.csv` | One row per pair. First columns match `reports/mappings.csv`. `numeric_agreement`: 1 = numbers agree, 0 = they do not | Reviewing in Excel |
| `table_anomalies.csv` | Unmatched cells on both sides, and low-confidence pairs | Giving reviewers a list to check |

The summary numbers include coverage (% of cells matched), average score, the low-confidence count and the unmatched counts.

Piece 14 · Stage 9 · lines 1694–1963

## Preview images

```mermaid
flowchart TD
  M["Cell records"] --> PP["Group into page pairs <br/>English page next to Spanish page"]
  PP --> RD["Turn both pages into images <br/>PyMuPDF at 200 dpi"]
  RD --> DR["Draw boxes <br/>red: English cell · green: Spanish cell <br/>blue: table outline · grey: unmatched"]
  DR --> LB["Tag label inside each box's top-left corner <br/>a Spanish cell shows its English partner's tag"]
  LB --> CB["Paste the two pages side by side"]
  CB --> JPG["One JPEG per page pair <br/>table_preview_opage_X_tpage_Y.jpg"]
  JPG --> PDF["All pages in one PDF <br/>table_alignment_output_previews.pdf"]
```

Page pairs come from the matches, not "page N next to page N", because the Spanish document is longer. If drawing fails, the rest of the run still succeeds.

The same tag on a red box and a green box means "these two cells are matched". A grey dashed box is a cell with no partner. This is a sketch, not a real preview.

Piece 15 · lines 1967–2248

## The main function and the command line

```mermaid
flowchart TD
  CMD["python table-segment.py with options"] --> A{"--original and --translated given?"}
  A -->|"yes"| USE["Use those two JSON files"]
  A -->|"no"| B{"--artifacts-dir given?"}
  B -->|"no"| ERR["Stop with an error"]
  B -->|"yes"| DISC["Find the two *_azure_di.json files <br/>the one named after the folder is English"]
  USE --> PQ{"PDF paths given?"}
  DISC --> PQ
  PQ -->|"no"| SS["Read PDF paths from shared_state.json"]
  PQ -->|"yes"| RUN["run_table_segmentation()"]
  SS --> RUN
  RUN --> ST["Stages printed as 1/9 to 9/9, <br/>then the files are written"]
```

When you are lost in the file, start at `run_table_segmentation()`: it calls every stage in order.

```
python table-segment.py --artifacts-dir <folder>
python table-segment.py --original A_azure_di.json --translated B_azure_di.json --out <folder>
```

Useful options: `--no-previews`, `--preview 20` (print 20 sample pairs), `--embeddings`, `--quiet`, `--render-dpi`.

Putting it together · from the test run

## One cell's journey

```mermaid
flowchart TD
  A["1 · Read <br/>'$25 copay/visit' gets the tag p1t1c6"] --> B["2 · Stitch <br/>the Spanish table split over 2 pages is glued into one"]
  B --> C["3 · Pair tables <br/>English table with the glued Spanish table"]
  C --> D["4 · Pair columns <br/>'What You Will Pay' with 'Lo que usted pagara'"]
  D --> E["5 · Pair rows <br/>row 1 with row 1: both have $25 and visit or visita"]
  E --> F["6 · Pair cells <br/>with 'Copago de $25/visita', score 0.66"]
  F --> G["8 · Output <br/>written to JSON and CSV, numeric_agreement = 1"]
  G --> H["9 · Preview <br/>red box and green box, both labelled p1t1c6"]
```

Stage 7 is not needed here: the cell was matched in Stage 6. The score of 0.66 comes from the number 25 agreeing and the chunks "cop" and "opa" matching.