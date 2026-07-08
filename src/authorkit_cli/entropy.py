"""Code-driven entropy for names and numbers.

LLM prose drifts toward the same stock names (Elena, Marcus, Kael…) and the
same default numbers (three, a dozen, forty, 1,247). This module hands the
writer *real* randomness to break that attractor: random numeric values within
author-chosen bounds, and random name-construction *seeds* (syllable skeletons,
an initial-letter constraint, a length target) the writer builds a setting-fit
name from — not finished names.

Randomness is true (`random.SystemRandom`, os.urandom-backed — the same source
`secrets` wraps) by default; the chosen value is rolled once at draft time and
becomes canon in the prose. Pure helpers take an optional ``rng`` (a
``random.Random``) so tests can pin output; the Typer layer never passes one.

Author:
    mdemarne
"""

from __future__ import annotations

import json
import math
import random
from dataclasses import asdict, dataclass

import typer
from rich.console import Console

console = Console()
# Registered as `authorkit entropy`.
entropy_app = typer.Typer(help="Code-driven randomness for names and numbers")

NUMBER_KINDS = ("int", "float", "year", "time")

# Phoneme banks per culture signal. Modest on purpose — these seed a name, they
# do not finish it. Unknown/empty culture falls back to "generic".
_ONSETS = {
    "generic": ["b", "d", "f", "g", "k", "l", "m", "n", "p", "r", "s", "t", "v", "th", "br", "tr", "st", "kr"],
    "latin": ["c", "d", "f", "g", "l", "m", "n", "p", "qu", "r", "s", "t", "v", "cl", "gr"],
    "norse": ["b", "d", "f", "g", "h", "k", "r", "s", "t", "th", "sk", "sv", "fr", "gn"],
    "slavic": ["b", "d", "g", "k", "l", "m", "n", "r", "s", "t", "v", "z", "vl", "dr", "zw"],
    "japanese": ["k", "s", "t", "n", "h", "m", "y", "r", "w", "sh", "ch"],
    "arabic": ["b", "d", "f", "h", "j", "k", "l", "m", "n", "q", "r", "s", "t", "z", "kh", "sh"],
}
_VOWELS = {
    "generic": ["a", "e", "i", "o", "u", "ae", "ei", "ou"],
    "latin": ["a", "e", "i", "o", "u", "au", "ae"],
    "norse": ["a", "e", "i", "o", "u", "y", "ei", "au"],
    "slavic": ["a", "e", "i", "o", "u", "y", "ya"],
    "japanese": ["a", "e", "i", "o", "u"],
    "arabic": ["a", "i", "u", "aa", "ee", "ou"],
}
_CODAS = {
    "generic": ["", "", "n", "r", "s", "l", "th", "ld", "rn", "st"],
    "latin": ["", "", "s", "n", "m", "x", "us", "or"],
    "norse": ["", "n", "r", "k", "rn", "ld", "vik", "ulf"],
    "slavic": ["", "v", "n", "k", "sk", "ov", "ev"],
    "japanese": ["", "", "n"],
    "arabic": ["", "n", "r", "d", "m", "q"],
}
# Syllable shapes (C=onset, V=vowel, c=coda); weighted toward CV / CVC.
_SHAPES = ["CV", "CV", "CVc", "CVc", "VC", "CVV"]


@dataclass(slots=True)
class NameSeed:
    """A name-construction seed — scaffolding for the writer, not a final name."""

    culture: str
    skeleton: str
    scaffold: str
    initial: str
    length_target: int


def _int_bounds(lo: float, hi: float) -> tuple[int, int]:
    """Integer bounds inside the inclusive ``[lo, hi]`` — ceil/floor, never
    truncation toward zero, so a rolled int can't escape the requested range."""
    ilo, ihi = math.ceil(lo), math.floor(hi)
    if ihi < ilo:
        raise ValueError(f"no integers in [{lo}, {hi}]")
    return ilo, ihi


def roll_numbers(kind: str, lo: float, hi: float, count: int = 1, *, rng=None) -> list:
    """Roll ``count`` random values of ``kind`` within the inclusive bounds.

    ``int``/``year`` return ints, ``float`` returns floats rounded to 2 dp,
    ``time`` returns ``HH:MM`` strings with the hour in ``[lo, hi]`` (0–23).
    """
    if kind not in NUMBER_KINDS:
        raise ValueError(f"kind must be one of {', '.join(NUMBER_KINDS)}")
    if count < 1:
        raise ValueError("count must be >= 1")
    if hi < lo:
        raise ValueError("max must be >= min")
    rng = rng if rng is not None else random.SystemRandom()

    out: list = []
    for _ in range(count):
        if kind in ("int", "year"):
            ilo, ihi = _int_bounds(lo, hi)
            out.append(rng.randint(ilo, ihi))
        elif kind == "float":
            # Round for prose-friendly values, then clamp: rounding is the last
            # step and could otherwise nudge the value past an inclusive bound
            # (e.g. hi=0.999 rolling 0.9985 -> round 1.0).
            out.append(float(min(hi, max(lo, round(rng.uniform(lo, hi), 2)))))
        else:  # time
            ilo, ihi = _int_bounds(lo, hi)
            if not (0 <= ilo <= 23 and 0 <= ihi <= 23):
                raise ValueError("time bounds must be hours in 0..23")
            out.append(f"{rng.randint(ilo, ihi):02d}:{rng.randint(0, 59):02d}")
    return out


def make_name_seed(culture: str = "generic", syllables: int | None = None, *, rng=None) -> NameSeed:
    """Build one name-construction seed for ``culture``.

    ``syllables`` defaults to a random 2–3. The scaffold samples real phonemes
    from the culture bank so the writer has a concrete starting shape, but it is
    explicitly a seed to refine, not a finished name.
    """
    key = (culture or "generic").strip().lower()
    onsets, vowels, codas = _ONSETS.get(key), _VOWELS.get(key), _CODAS.get(key)
    if onsets is None:
        key, onsets, vowels, codas = "generic", _ONSETS["generic"], _VOWELS["generic"], _CODAS["generic"]
    rng = rng if rng is not None else random.SystemRandom()

    n = syllables if syllables is not None else rng.randint(2, 3)
    if n < 1:
        raise ValueError("syllables must be >= 1")

    shapes, parts = [], []
    for _ in range(n):
        shape = rng.choice(_SHAPES)
        shapes.append(shape)
        piece = ""
        for ch in shape:
            if ch == "C":
                piece += rng.choice(onsets)
            elif ch == "V":
                piece += rng.choice(vowels)
            else:  # c — optional coda
                piece += rng.choice(codas)
        parts.append(piece)

    scaffold = "-".join(p for p in parts if p)
    flat = scaffold.replace("-", "")
    initial = (flat[:1] or rng.choice(vowels)).upper()
    return NameSeed(
        culture=key,
        skeleton="-".join(shapes),
        scaffold=scaffold,
        initial=initial,
        length_target=max(len(flat), 3),
    )


@entropy_app.command("number")
def number_cmd(
    min_: float = typer.Option(..., "--min", help="Lower bound (inclusive)."),
    max_: float = typer.Option(..., "--max", help="Upper bound (inclusive)."),
    count: int = typer.Option(1, "--count", help="How many values to roll."),
    kind: str = typer.Option("int", "--kind", help="int | float | year | time (time bounds are hours 0..23)."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    """Roll genuinely random number(s) within bounds the context justifies."""
    try:
        values = roll_numbers(kind, min_, max_, count)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc

    if json_output:
        console.print(
            json.dumps({"kind": kind, "min": min_, "max": max_, "values": values}),
            markup=False,
            highlight=False,
            soft_wrap=True,
        )
        return
    for value in values:
        console.print(value, markup=False, highlight=False)


@entropy_app.command("name")
def name_cmd(
    culture: str = typer.Option("generic", "--culture", help="Culture/era signal for the phoneme bank."),
    syllables: int | None = typer.Option(None, "--syllables", help="Syllable count (default: random 2-3)."),
    count: int = typer.Option(1, "--count", help="How many seeds to produce."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    """Produce name-construction seed(s) — scaffolding to build a name from, not a final name."""
    if count < 1:
        raise typer.BadParameter("count must be >= 1")
    try:
        seeds = [make_name_seed(culture, syllables) for _ in range(count)]
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc

    if json_output:
        # The seeds carry the *resolved* culture (an unknown bank key falls back to
        # "generic" in make_name_seed) — echo that, not the raw option, so the
        # top-level field and the seeds can't disagree.
        console.print(
            json.dumps({"culture": seeds[0].culture, "seeds": [asdict(s) for s in seeds]}),
            markup=False,
            highlight=False,
            soft_wrap=True,
        )
        return
    console.print(
        "Build a setting-fit name from each seed (honor the initial + rough shape; refine for sound):",
        markup=False,
        highlight=False,
    )
    for seed in seeds:
        console.print(
            f"- scaffold={seed.scaffold}  initial={seed.initial}  "
            f"skeleton={seed.skeleton}  ~{seed.length_target} letters",
            markup=False,
            highlight=False,
        )
