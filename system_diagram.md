# System Architecture — Bedtime Story-Teller Agent

## Block Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER (Terminal)                             │
│  • Enters a story request ("A story about a brave little dragon")   │
│  • Optionally provides feedback to revise the story                 │
└──────────────┬──────────────────────────────────────▲───────────────┘
               │ story request                        │ final story +
               │                                      │ judge scores +
               ▼                                      │ safety status
┌───────────────────────────────────────────────────────────────────────┐
│                       🎯 ORCHESTRATOR                                 │
│                                                                       │
│  Coordinates the pipeline and manages TWO independent gates:          │
│                                                                       │
│  Steps:                                                               │
│    1. Send request → Categorizer                                      │
│    2. Send category + request → Arc Planner                           │
│    3. Send arc + category + request → Storyteller                     │
│    4. Send draft → Judge (QUALITY GATE)                               │
│    5. If score < 7/10 and iterations < 3 → loop to Storyteller        │
│    6. Send story → Safety Filter (SAFETY GATE — independent)          │
│    7. If unsafe → loop to Storyteller for safety rewrite (up to 2x)   │
│    8. Present final story + scores + safety status to User            │
│    9. If user provides feedback → Storyteller → Judge → Safety again  │
│                                                                       │
│  ┌──────────┐ ┌────────────┐ ┌───────────┐ ┌──────────┐ ┌─────────┐   │
│  │CATEGO-   │ │  STORY ARC │ │   STORY-  │ │  JUDGE   │ │ SAFETY  │   │
│  │  RIZER   │ │  PLANNER   │ │  TELLER   │ │          │ │ FILTER  │   │
│  │          │ │            │ │           │ │          │ │         │   │
│  │Classifies│ │Creates a   │ │Generates, │ │Evaluates │ │Scans for│   │
│  │request   │ │5-beat arc: │ │refines, & │ │on 5      │ │unsafe   │   │
│  │into:     │ │            │ │rewrites   │ │criteria: │ │content: │   │
│  │• category│ │1. Setup    │ │stories    │ │          │ │         │   │
│  │• themes  │ │2. Rising   │ │           │ │1. Age    │ │• Fright │   │
│  │• chars   │ │3. Climax   │ │Has 3 modes│ │2. Engage │ │• Violent│   │
│  │• tone    │ │4. Falling  │ │• generate │ │3. Struct │ │• Themes │   │
│  │• settings│ │5. Resolve  │ │• refine   │ │4. Lang   │ │• Scary  │   │
│  │          │ │+ moral     │ │• safety   │ │5. Moral  │ │• Tone   │   │
│  │Temp: 0.1 │ │+ char arc  │ │  rewrite  │ │          │ │• Lang   │   │
│  │(precise) │ │            │ │           │ │Temp: 0.1 │ │         │   │
│  │          │ │Temp: 0.1   │ │Temp: 0.8  │ │(precise) │ │Temp: 0.1│   │
│  └────┬─────┘ └─────┬──────┘ └──┬───▲──▲─┘ └───┬───▲───┘ └──┬──▲──┘   │
│       │             │           │   │  │       │   │        │  │      │
│       │ category    │ arc       │   │  │       │   │        │  │      │
│       └────►────────┘───►───────┘   │  │       │   │        │  │      │
│                              draft  │  │  eval │   │ safety │  │      │
│                                     │  │       │   │ result │  │      │
│                            ┌────────┘  │  ┌────┘   │  ┌─────┘  │      │
│                            │           │  │        │  │        │      │
│                            ▼           │  ▼        │  ▼        │      │
│                      ┌─────────────────┴──────────────────────┐│      │
│                      │     QUALITY GATE        SAFETY GATE    ││      │
│                      │   (avg score ≥ 7)    (hard pass/fail)  ││      │
│                      │                                        ││      │
│                      │  These are INDEPENDENT gates.          ││      │
│                      │  A story must pass BOTH to be shown.   ││      │
│                      │                                        ││      │
│                      │  ⚠ The Judge uses AVERAGES, so a       ││      │
│                      │  score of 0 on age_appropriateness     ││      │
│                      │  + 10 on everything else = 8.0 avg     ││      │
│                      │  → would PASS the Judge (threshold 7)  ││      │
│                      │  → would FAIL the Safety Filter ✓      ││      │
│                      └────────────────────────────────────────┘│      │
└───────────────────────────────────────────────────────────────────────┘
```

## Why Two Independent Gates?

The **Judge** evaluates overall story *quality* using an **average** of 5 scores.
This creates a critical vulnerability for children's content:

```
Example: A story with scary violence but beautiful prose

  Age Appropriateness:    2/10  ← DANGEROUS
  Engagement & Pacing:   10/10
  Narrative Structure:    9/10
  Language & Vocabulary: 10/10
  Moral & Lesson:         9/10
  ─────────────────────────────
  Average:              8.0/10  ← PASSES the Judge (threshold 7)!
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
Judge        ──►  { scores (5 criteria × 1-10), overall_score,
    │                feedback, strengths, areas_for_improvement }
    │
    ├── score < 7 ──► Send feedback to Storyteller (up to 3 rounds)
    │
    ▼
Safety       ──►  { is_safe, flags, severity, explanation,
Filter             suggested_changes }
    │
    ├── unsafe ──► Send flags to Storyteller for safety rewrite (up to 2x)
    │
    ▼
User         ◄──  Final story + judge scores + safety status
    │
    └── feedback ──► Storyteller → Judge → Safety Filter (full re-check)
```

## Component Descriptions

| Component | File | Role | Temperature | Gate Type |
|---|---|---|---|---|
| **Orchestrator** | `orchestrator.py` | Coordinates the full pipeline, manages both gates | N/A | — |
| **Categorizer** | `categorizer.py` | Classifies story request into category + metadata | 0.1 (precise) | — |
| **Arc Planner** | `story_arc.py` | Creates structured 5-beat narrative outline | 0.1 (precise) | — |
| **Storyteller** | `storyteller.py` | Generates, refines, rewrites, and safety-fixes stories | 0.8 (creative) | — |
| **Judge** | `judge.py` | Scores stories on 5 quality criteria | 0.1 (precise) | Quality (avg ≥ 7) |
| **Safety Filter** | `safety_filter.py` | Scans for harmful/inappropriate content | 0.1 (precise) | Safety (hard pass/fail) |
| **Config** | `config.py` | Shared LLM client, model settings, `call_model()` | N/A | — |
| **Prompts** | `prompts.py` | All prompt templates + category guidelines | N/A | — |

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
