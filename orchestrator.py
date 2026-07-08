"""
Orchestrator
────────────
Coordinates the full story-generation pipeline:

    User Request
        → Categorizer    (classify request)
        → Arc Planner    (build 5-beat outline)
        → Storyteller     (generate draft)
        → Judge           (evaluate quality)
        ↺ Storyteller     (refine if score < threshold, up to N times)
        → Safety Filter   (hard gate — independent of Judge)
        ↺ Storyteller     (rewrite if safety flags found, up to N times)
        → User            (present final story + scores)
        ↺ User Feedback   (optional revisions)

Why the Safety Filter is separate from the Judge:
    The Judge scores on 5 criteria and uses the *average* to determine a
    pass/fail.  This means a story could score 0 on age_appropriateness
    but 10 on everything else — and still pass a 7/10 threshold.  For
    children's content this is unacceptable.  The Safety Filter acts as
    an independent hard gate: if ANY safety concern is flagged, the story
    is blocked and must be rewritten regardless of the Judge's scores.
"""

from config import MAX_REFINEMENT_ITERATIONS
from categorizer import categorize
from story_arc import plan_arc
from storyteller import (
    generate_story,
    refine_story,
    apply_user_feedback,
    fix_safety_issues,
)
from judge import evaluate_story, passes_threshold
from safety_filter import check_safety, is_safe

# Maximum safety-rewrite attempts before giving up
MAX_SAFETY_REWRITES = 2


# ── Pretty-printing helpers ───────────────────────────────────────────────

def _print_header(text: str) -> None:
    width = 60
    print()
    print("═" * width)
    print(f"  {text}")
    print("═" * width)


def _print_step(icon: str, label: str, detail: str = "") -> None:
    msg = f"  {icon}  {label}"
    if detail:
        msg += f" — {detail}"
    print(msg)


def _print_scores(evaluation: dict) -> None:
    """Display the judge's scores in a readable table."""
    scores = evaluation.get("scores", {})
    overall = evaluation.get("overall_score", "?")
    strengths = evaluation.get("strengths", [])
    areas = evaluation.get("areas_for_improvement", [])

    print()
    print("  ┌─────────────────────────────────┬───────┐")
    print("  │  Criterion                      │ Score │")
    print("  ├─────────────────────────────────┼───────┤")
    for key, value in scores.items():
        label = key.replace("_", " ").title()
        print(f"  │  {label:<31} │  {value:>3}  │")
    print("  ├─────────────────────────────────┼───────┤")
    print(f"  │  {'Overall':31} │  {overall:>3}  │")
    print("  └─────────────────────────────────┴───────┘")

    if strengths:
        print("\n  ✅ Strengths:")
        for s in strengths:
            print(f"     • {s}")
    if areas:
        print("\n  📝 Areas for improvement:")
        for a in areas:
            print(f"     • {a}")
    print()


def _print_safety_result(safety_result: dict) -> None:
    """Display the safety filter's evaluation."""
    safe = safety_result.get("is_safe", False)
    severity = safety_result.get("severity", "unknown")
    flags = safety_result.get("flags", [])
    explanation = safety_result.get("explanation", "")

    if safe:
        print(f"\n  🛡️  Safety Check: ✅ PASSED (severity: {severity})")
    else:
        print(f"\n  🛡️  Safety Check: ❌ FAILED (severity: {severity})")
        if explanation:
            print(f"     {explanation}")
        if flags:
            print("     Flags:")
            for flag in flags:
                print(f"       ⚠  {flag}")
    print()


# ── Main pipeline ─────────────────────────────────────────────────────────

def run() -> None:
    """Run the interactive story-generation loop."""
    _print_header("🌙  Bedtime Story-Teller Agent  🌙")
    print("  Tell me what kind of story you'd like to hear!")
    print("  (Type 'quit' or 'exit' to leave)\n")

    while True:
        user_input = input("  📖  Your story request: ").strip()
        if not user_input:
            print("  Please enter a story request.\n")
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("\n  🌟 Goodnight! Sweet dreams! 🌟\n")
            break

        story = _generate_pipeline(user_input)
        if story is None:
            continue

        # ── User feedback loop ────────────────────────────────────────
        _user_feedback_loop(story, user_input)

        # ── Another story? ────────────────────────────────────────────
        print("\n" + "─" * 60)
        again = input("  Would you like another story? (yes/no): ").strip().lower()
        if again not in ("yes", "y", "sure", "yeah", "yep"):
            print("\n  🌟 Goodnight! Sweet dreams! 🌟\n")
            break
        print()


def _generate_pipeline(user_input: str) -> str | None:
    """Run categorizer → arc planner → storyteller → judge → safety → user.

    Returns the final story text, or None on failure.
    """
    # Step 1 — Categorize
    _print_step("📂", "Categorizing your request…")
    category = categorize(user_input)
    _print_step(
        "✓",
        f"Category: {category.get('category', 'general')}",
        f"Themes: {', '.join(category.get('themes', []))}",
    )

    # Step 2 — Plan the arc
    _print_step("📐", "Planning the story arc…")
    arc = plan_arc(user_input, category)
    _print_step("✓", "Story arc ready")

    # Step 3 — Generate the first draft
    _print_step("✍️", "Writing your story…")
    story = generate_story(user_input, category, arc)
    _print_step("✓", "First draft complete")

    # Step 4 — Judge → Refine loop (quality gate)
    for iteration in range(1, MAX_REFINEMENT_ITERATIONS + 1):
        _print_step("⚖️", f"Evaluating story (round {iteration})…")
        evaluation = evaluate_story(story, user_input)
        _print_scores(evaluation)

        if passes_threshold(evaluation):
            _print_step("🎉", "Story passed quality check!")
            break

        _print_step("🔄", f"Refining story (round {iteration})…")
        story = refine_story(story, evaluation)
        _print_step("✓", "Refinement complete")
    else:
        # Ran out of iterations — present the best we have
        _print_step(
            "⚠️",
            "Max refinement rounds reached — presenting best version.",
        )

    # Step 5 — Safety Filter (independent hard gate)
    #
    # This runs AFTER the judge because it is a separate concern.
    # The judge's average score can mask a low age_appropriateness
    # score (e.g., 0 on safety + 10 on everything else = 8.0 avg,
    # which would pass a 7/10 threshold).  The safety filter catches
    # exactly these cases.
    story = _run_safety_gate(story)

    # Step 6 — Present the final story
    _print_header("📖  Your Bedtime Story")
    print()
    print(story)
    print()

    return story


def _run_safety_gate(story: str) -> str:
    """Run the safety filter and rewrite the story if needed.

    Returns the (potentially rewritten) story that has passed safety
    checks, or the best version after MAX_SAFETY_REWRITES attempts.
    """
    for attempt in range(1, MAX_SAFETY_REWRITES + 1):
        _print_step("🛡️", f"Running safety filter (check {attempt})…")
        safety_result = check_safety(story)
        _print_safety_result(safety_result)

        if is_safe(safety_result):
            _print_step("✅", "Story passed safety check!")
            return story

        _print_step(
            "🔒",
            f"Safety issue detected — rewriting (attempt {attempt})…",
        )
        story = fix_safety_issues(story, safety_result)
        _print_step("✓", "Safety rewrite complete")

    # Final safety check after last rewrite
    _print_step("🛡️", "Final safety verification…")
    final_check = check_safety(story)
    _print_safety_result(final_check)

    if not is_safe(final_check):
        _print_step(
            "⚠️",
            "Story could not pass safety after max rewrites — "
            "presenting with caution.",
        )

    return story


def _user_feedback_loop(story: str, original_request: str) -> None:
    """Let the user request changes to the story, re-judging & re-checking safety after each."""
    while True:
        print("─" * 60)
        feedback = input(
            "  💬 Any changes you'd like? (press Enter to skip): "
        ).strip()
        if not feedback:
            break

        _print_step("✍️", "Revising the story with your feedback…")
        story = apply_user_feedback(story, feedback)

        # Re-evaluate the revised story
        _print_step("⚖️", "Re-evaluating revised story…")
        evaluation = evaluate_story(story, original_request)
        _print_scores(evaluation)

        # Re-run safety filter on revised story
        story = _run_safety_gate(story)

        _print_header("📖  Your Revised Story")
        print()
        print(story)
        print()
