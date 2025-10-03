# RNGenius Random Application Documentation

## Functional Narrative

### Purpose and Promise

RNGenius exists as a playful but precise embodiment of **Quantum-Adjacent Algorithmic Non-Determinism**: press a single heroic button and claim a brand-new number. The app relieves decision fatigue by outsourcing tiny choices to randomness, just as the philosophy deck prescribes (“Let Fate Plan Your Day” and “Decision fatigue is real. Randomness is relief.”).

### Requirements Fulfilment

| Requirement (source) | Implementation cue |
| --- | --- |
| **FR-1** — The interface must feature a button labeled “I’m Feeling Chaotic.” (`RNGenius_Functional_Spec.docx.md`, §4) | The Tkinter primary button uses the exact label and visually anchors the window. |
| **FR-2** — Clicking reveals a random integer in the main display. | `generate_number` picks a 64-bit signed integer and pushes it into the prominent number label. |
| **FR-3** — Provide copy-to-clipboard support. | The companion button enables after the first draw and confirms success with a dialog. |
| **FR-4** — Persist the last five results for the session. | A scroll-free history label lists the most recent values in newest-first order. |
| **NFR-1** — Response under 150 ms. | Local RNG calls return instantly, keeping perceived latency negligible. |
| **NFR-2** — Accessible and keyboard operable. | Enter/Space bindings mirror the main button plus an explicit focus hand-off. |
| **NFR-3** — Delight factor ≥ 0.93 giggles per click. | Rotating window titles and confetti bursts deliver the required whimsy. |

### Daily Rituals & Micro-Planning

The PPT outline encourages users to roll a number each morning, map odd values to creative work, even values to admin, honour the number 7 with a stretch, and treat primes as prompts for novelty. RNGenius keeps results visible and copyable so these rituals can plug into planning systems without friction.

### Ethical Guardrails

Philosophy slide 4 warns against surrendering responsibility. The application respects that stance: randomness is a tiebreaker and mood freshener, not a substitute for judgement. Do not deploy it for safety-critical or irreversible decisions.

### Onboarding Flow

Borrowing from the user manual PDF:

1. Launch the app and take a centring breath.
2. Activate “I’m Feeling Chaotic.”
3. Enjoy the confetti while your integer destiny materialises.
4. Copy the value if you need it elsewhere (odd = adventurous, even = admin).
5. Revisit the bottom history if you want to revisit recent draws.

## Technical Deep Dive

### Module Snapshot

- **Source**: `tests/random_app.py`
- **Entry point**: `main()` constructs a `Tk` root and instantiates `RNGeniusApp`.
- **Dependencies**: Standard library only (`tkinter`, `random`, `time`).
- **Numerics**: Signed 64-bit range via `MIN_INT64 = -(2**63)` and `MAX_INT64 = 2**63 - 1`.

### UI Composition

1. **Header Frame** — bold title plus a subtitle inviting entropy.
2. **Display Stack** — a large Courier label for the number, backed by a canvas overlay reserved for confetti.
3. **Control Bar** — grid-aligned action and copy buttons; the latter starts disabled.
4. **History Panel** — monospace label reporting the latest five values, trimmed on update.
5. **Global Bindings** — `<Return>` and `<space>` are routed to the generator, with the main button receiving initial focus.

### Randomness & History Engine

`generate_number` funnels directly into `random.randint(MIN_INT64, MAX_INT64)`, memoises the result, unlocks the copy button, and unshifts the value into `history`, slicing the list to at most five entries. The UI label mirrors this array, ensuring the state users see matches the data the tests assert against.

### Clipboard Workflow

`copy_to_clipboard` guards against empty state, clears the current clipboard, appends the latest number as text, and provides feedback via `messagebox.showinfo`, aligning with the user manual’s reassurance that an unwanted number can simply be rerolled.

### Confetti System

`_burst_confetti` seeds 80 particles (40 for overlapping bursts) near the canvas crown, each with velocity, colour, gravity, drag, and lifespan fields. `_animate_confetti` runs every ~16 ms to apply physics, bounce at the floor, shrink near expiration, and cull expired nodes. The particle palette matches the playful tone demanded by the delight requirement and signals success beyond the numeric output.

### Responsiveness & Layout

Window geometry defaults to 560×460, with a 520×420 minimum to preserve layout integrity during resizes. `_on_canvas_resize` keeps the confetti canvas colour synced with the surrounding theme so the animation blends seamlessly when themes change.

### Accessibility & Delight Mechanics

- Keyboard parity ensures power users and assistive tech receive equal functionality.
- The rotating window titles double as textual feedback, delivering the promised Giggles Per Click metric.
- Visual contrast (bold fonts, warm button palette) keeps the primary action discoverable, while the wrap-enabled number label accommodates lengthy integers without overflow.

### Integration Hooks

Because the fixture is stateful only in memory and avoids external dependencies, it is safe for automated demos, screenshot generation, or behavioural tests. Additional instrumentation (logging, analytics, exports) can be added around `generate_number` without disturbing the current experience.

### Document Provenance

Content here draws directly from Escarabajo-managed artifacts:

- `.Escarabajo/kb/tests/data/RNGenius_Functional_Spec.docx.md`
- `.Escarabajo/kb/tests/data/RNGenius_Philosophy.pptx.md`
- `.Escarabajo/kb/tests/data/RNGenius_User_Manual.pdf.md`

These Markdown snippets were obtained via the `list_kb` registry and opened locally as instructed.
