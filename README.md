
# PairGo Fruit Personality Algorithm: Terminal Demo

A standalone, dependency-free preview of the scoring logic behind the [PairGo](https://www.pairgoapp.com) personality quiz. This repo exists to show the logic, not the product; for the live quiz, see [pairgoapp.com](https://www.pairgoapp.com).

## What it does

Takes 22 quiz answers and returns one of **12 fruit personality types**, refined down to one of **96 subtypes**, using a two-part scoring model:

1. **Dimensional scoring.** Each answer nudges 8 abstract personality dimensions (all starting at a neutral baseline of 50, clamped to 0-100). By the end of the quiz, the user has an 8-number profile.
2. **Spine scoring.** In parallel, each answer choice also casts a "vote" for one of the 12 fruit types. Votes are tallied and normalized, with a coverage-compensation weight applied so fruits that appear less often as an answer option aren't structurally disadvantaged.
3. **Subtype matching.** Each of the 96 subtypes has a fixed 8-dimensional "fingerprint." The user's dimensional profile is compared against every fingerprint (Euclidean distance, converted to a similarity score).
4. **Final blend.** Each subtype's final score is **45% spine score + 55% dimensional similarity**. Highest score wins; its parent fruit is the user's fruit type, and the subtype is the finer-grained result.

## Why it's built this way

The blended model was a deliberate choice over a pure vote-count or pure-clustering approach. Spine scoring alone over-rewards whichever fruit had the most answer options available (hence the coverage-compensation weights), while dimensional-only scoring can miss the more intuitive, plain-language "which fruit do your answers actually sound like" signal. Blending both, weighted toward the dimensional score, was the balance that held up best against real quiz-taker feedback during testing.

## Run it

No installation, no dependencies. Pure Python 3 standard library (`math`, `typing`).

```bash
python3 Pairgo_personality_demo.py
```

This runs a worked example (22 hardcoded sample answers) and prints:

```
Fruit type: <winning fruit>
Subtype: <ID>, <subtype name>
Dimensions (D1-D8): [8 scores, 0-100]
Top 3 matches:
  <ID> (<fruit>, <name>): <score>
  ...
```

To score your own answers, edit `example_answers` at the bottom of the file. It's a list of 22 integers (0-3), one per question, corresponding to which answer choice was selected.

## Relationship to the live app

This demo shows the quiz-scoring algorithm: the part of PairGo that turns quiz answers into a fruit type and subtype. That piece is live in the app today, along with profile setup, pairing-code connections, and in-app messaging between paired users.

PairGo's next build phase is the matching engine itself: automatically pairing users with each other based on fruit-type/subtype compatibility (rather than users pairing manually via a shared code). That piece is in active development and isn't reflected in this demo yet.

## Links

- Live quiz / app: [pairgoapp.com](https://www.pairgoapp.com)

---

*Questions about the approach or want to see more? Reach out through the contact info on [pairgoapp.com](https://www.pairgoapp.com).*
