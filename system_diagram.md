# System Architecture — Bedtime Story-Teller Agent

## Block Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER (Terminal)                             │
│  • Enters a story request ("A story about a brave little dragon")  │
│  • Optionally provides feedback to revise the story                │
└──────────────┬──────────────────────────────────────▲───────────────┘
               │ story request                       │ final story +
               │                                     │ judge scores +
               ▼                                     │ safety status
┌──────────────────────────────────────────────────────────────────────┐
│                        🎯 ORCHESTRATOR                               │
│                                                                      │
│  Coordinates the pipeline and manages TWO independent gates.         │
│  All arrows below happen THROUGH the Orchestrator — the agents       │
│  never talk to each other directly.                                  │
│                                                                      │
│  Pipeline Flow:                                                      │
│                                                                      │
│  ┌──────────┐    ┌────────────┐    ┌───────────┐                     │
│  │📂 CATEGO-│    │📐 STORY ARC│    │✍️ STORY-  │                     │
│  │  RIZER   │    │  PLANNER   │    │  TELLER   │                     │
│  │          │    │            │    │           │                     │
│  │Classifies│    │Creates a   │    │Generates, │                     │
│  │request   │    │5-beat arc: │    │refines, & │                     │
│  │into:     │    │            │    │rewrites   │                     │
│  │• category│    │1. Setup    │    │stories    │                     │
│  │• themes  │    │2. Rising   │    │           │                     │
│  │• chars   │    │3. Climax   │    │Has 4 modes│                     │
│  │• tone    │    │4. Falling  │    │• generate │                     │
│  │• settings│    │5. Resolve  │    │• refine   │                     │
│  │          │    │+ moral     │    │• user rev │                     │
│  │Temp: 0.1 │    │+ char arc  │    │• safety   │                     │
│  │(precise) │    │            │    │  rewrite  │                     │
│  │          │    │Temp: 0.1   │    │           │                     │
│  │          │    │(precise)   │    │Temp: 0.8  │                     │
│  │          │    │            │    │(creative) │                     │
│  └────┬─────┘    └─────┬──────┘    └──┬────────┘                     │
│       │                │              │                              │
│       │ category       │ arc          │ story draft                  │
│       ▼                ▼              ▼                              │
│  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   │
│                                                                      │
│       GATE 1: QUALITY (Judge)        GATE 2: SAFETY (Filter)         │
│       Runs FIRST                     Runs SECOND (after Judge pass)  │
│                                                                      │
│  ┌──────────────────────┐       ┌──────────────────────┐             │
│  │ ⚖️  JUDGE             │       │ 🛡️ SAFETY FILTER     │             │
│  │                      │       │                      │             │
│  │ Scores on 6 criteria │       │ Scans for 6 types of │             │
│  │ (each 1-10):         │       │ harmful content:     │             │
│  │                      │       │                      │             │
│  │ 1. Age Appropriate   │       │ • Frightening imagery│             │
│  │ 2. Engage+Bedtime    │       │ • Violence/aggression│             │
│  │ 3. Narrative Struct  │       │ • Inappropriate theme│             │
│  │ 4. Language/Vocab    │       │ • Scary scenarios    │             │
│  │ 5. Moral/Lesson      │       │ • Negative emot tone │             │
│  │ 6. Request Following │       │ • Inappropriate lang │             │
│  │                      │       │                      │             │
│  │ Pass: avg ≥ 7/10     │       │ Pass: binary YES/NO  │             │
│  │ Fail: → Storyteller  │       │ Fail: → Storyteller  │             │
│  │  gets feedback to    │       │  gets flags to do a  │             │
│  │  refine (up to 3x)   │       │  safety rewrite (2x) │             │
│  │                      │       │                      │             │
│  │ Temp: 0.1 (precise)  │       │ Temp: 0.1 (precise)  │             │
│  └──────────────────────┘       └──────────────────────┘             │
│                                                                      │
│  WHY TWO GATES?                                                      │
│  The Judge uses AVERAGES. With 6 criteria, a story scoring:          │
│    age_appropriateness = 0, all others = 10                          │
│    → average = 8.3 → PASSES the Judge!                               │
│  The Safety Filter catches this with a hard pass/fail.               │
│                                                                      │
│  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   │
│                                                                      │
│  FEEDBACK LOOPS (all managed by the Orchestrator):                   │
│                                                                      │
│  Loop 1: Judge → Storyteller (quality refinement)                    │
│    Judge sends scores + feedback → Storyteller refines → re-judge    │
│    Up to 3 rounds. Stops when avg score ≥ 7.                         │
│                                                                      │
│  Loop 2: Safety Filter → Storyteller (safety rewrite)                │
│    Filter sends flags + suggested changes → Storyteller rewrites     │
│    Up to 2 rounds. Stops when is_safe = true.                        │
│                                                                      │
│  Loop 3: User → Storyteller (user feedback)                          │
│    User sends change requests → Storyteller revises                  │
│    → re-runs Judge AND Safety Filter on revised story.               │
│    Unlimited rounds until user is satisfied.                         │
└──────────────────────────────────────────────────────────────────────┘
```

## Why Two Independent Gates?

The **Judge** evaluates overall story *quality* using an **average** of 6 scores.
This creates a critical vulnerability for children's content:

```
Example: A story with scary violence but beautiful prose

  Age Appropriateness:    0/10  ← DANGEROUS
  Engagement & Bedtime:  10/10
  Narrative Structure:   10/10
  Language & Vocabulary: 10/10
  Moral & Lesson:        10/10
  Request Following:     10/10
  ──────────────────────────────
  Average:              8.3/10  ← PASSES the Judge (threshold 7)!
```

The **Safety Filter** catches this. It does not score — it scans for specific
harmful content categories and returns a binary **PASS/FAIL**. A story that
the Judge loves can still be blocked if the Safety Filter finds:
- Frightening imagery
- Violence or aggression
- Inappropriate themes
- Scary scenarios
- Negative emotional tone
- Inappropriate language

**Both gates must pass before a story reaches a child.**

## Data Flow Summary

```
User Request
    │
    ▼
Categorizer  ──►  { category, themes, characters, tone, settings }
    │
    ▼
Arc Planner  ──►  { setup, rising_action, climax, falling_action,
    │                resolution, moral, character_arc }
    ▼
Storyteller  ──►  story text (400-600 words)
    │
    ▼
Judge        ──►  { scores (6 criteria × 1-10), overall_score,
    │                feedback, strengths, areas_for_improvement }
    │
    ├── score < 7 ──► Orchestrator sends feedback to Storyteller
    │                  (up to 3 rounds, then re-evaluates via Judge)
    ▼
Safety       ──►  { is_safe, flags, severity, explanation,
Filter             suggested_changes }
    │
    ├── unsafe ──► Orchestrator sends flags to Storyteller
    │               (up to 2 rounds, then re-checks via Safety Filter)
    ▼
User         ◄──  Final story + judge scores + safety status
    │
    └── feedback ──► Orchestrator → Storyteller → Judge → Safety Filter
```

## Component Descriptions

| Component | File | Role | Temperature | Gate Type |
|---|---|---|---|---|
| **Orchestrator** | `orchestrator.py` | Coordinates the full pipeline, manages both gates | N/A | — |
| **Categorizer** | `categorizer.py` | Classifies story request into category + metadata | 0.1 (precise) | — |
| **Arc Planner** | `story_arc.py` | Creates structured 5-beat narrative outline | 0.1 (precise) | — |
| **Storyteller** | `storyteller.py` | Generates, refines, rewrites, and safety-fixes stories | 0.8 (creative) | — |
| **Judge** | `judge.py` | Scores stories on 6 quality criteria | 0.1 (precise) | Quality (avg ≥ 7) |
| **Safety Filter** | `safety_filter.py` | Scans for harmful/inappropriate content | 0.1 (precise) | Safety (hard pass/fail) |
| **Config** | `config.py` | Shared LLM client, model settings, `call_model()` | N/A | — |
| **Prompts** | `prompts.py` | All prompt templates + category guidelines | N/A | — |

## Judge Evaluation Criteria (6)

| # | Criterion | What It Measures |
|---|---|---|
| 1 | **Age Appropriateness** | Content, vocabulary, and complexity suitable for ages 5-10 |
| 2 | **Engagement & Bedtime Flow** | Holds attention AND winds down calmly toward sleep |
| 3 | **Narrative Structure** | Clear arc (beginning, middle, end), coherent plot |
| 4 | **Language & Vocabulary** | Vivid, age-appropriate language with sensory details |
| 5 | **Moral & Lesson** | Positive message woven naturally, not preachy |
| 6 | **Request Following** | Story faithfully addresses the user's original request |

## Category-Tailored Generation

The Storyteller uses different guidelines depending on the category detected by the Categorizer:

| Category | Key Guidelines |
|---|---|
| Adventure | Vivid action language, sensory details, wonder & discovery |
| Fantasy | Sparkle words, magical creatures, whimsical world-building |
| Animal | Gentle anthropomorphism, nature settings, animal bonds |
| Friendship | Emotional warmth, conflict resolution, celebrating uniqueness |
| Mystery | Fun clues, curiosity over suspense, teamwork |
| Educational | Show-don't-tell, learning as discovery |
| Fairy-tale | Classic language, transformation, happy endings |
| General | Warm language, excitement + coziness, gentle humor |
