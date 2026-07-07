"""
PairGo Fruit Personality Algorithm — standalone demo
=====================================================

This is a minimal, self-contained mirror of the scoring logic that powers
the PairGo personality quiz. It takes 22 quiz answers and returns one of
12 "fruit" personality types plus one of 96 finer-grained "subtypes".

HOW IT WORKS (high level)
--------------------------
1. Each of the 22 questions has up to 4 answer choices. Each choice nudges
   a set of 8 abstract personality dimensions (D1-D8) up or down by a
   small amount. All dimensions start at a neutral baseline of 50 and are
   clamped to the 0-100 range.

2. In parallel, each answer choice is also associated with one of 12
   fruit types (the "spine" mapping). We tally how often each fruit was
   picked, normalize by the number of questions answered, and apply a
   per-fruit weight (some fruits are "rarer" answer choices, so they get
   boosted to keep the scoring fair — this is "coverage compensation").

3. Every one of the 96 subtypes has a fixed 8-dimensional "fingerprint"
   (its ideal D1-D8 profile). We compute how close the user's own D1-D8
   profile is to every fingerprint (Euclidean distance -> similarity %).

4. Each subtype's final score blends:
       45% weight  -> how strongly the user's answers pointed at that
                       subtype's fruit (the "spine" score)
       55% weight  -> how close the user's dimensions are to that
                       subtype's fingerprint (the "dimensional" score)

5. The subtype with the highest final score wins. Its parent fruit is the
   user's fruit type, and the subtype itself is the finer-grained result.

Run this file directly for a worked example (see bottom of file).
"""

import math
from typing import Dict, List, Tuple

# ─────────────────────────────────────────────────────────────────────────
# 1. CONFIG: which fruit each answer choice "votes" for (the "spine")
# ─────────────────────────────────────────────────────────────────────────
# QUESTION_FRUITS[q][a] = fruit name voted for by answer `a` on question `q`
QUESTION_FRUITS: List[List[str]] = [
    ["Apple", "Cherry", "Kiwi", "Lemon"],
    ["Lemon", "Blueberry", "Passionfruit", "Blackberry"],
    ["Grape", "Apple"],
    ["Pineapple", "Cherry", "Kiwi", "Lemon"],
    ["Pear", "Passionfruit", "Blackberry", "Cherry"],
    ["Apple", "Blueberry", "Strawberry", "Pineapple"],
    ["Blackberry", "Kiwi", "Pear", "Blueberry"],
    ["Grape", "Apple"],
    ["Lemon", "Blackberry", "Blueberry", "Passionfruit"],
    ["Cherry", "Blackberry", "Papaya", "Blueberry"],
    ["Grape", "Blueberry", "Passionfruit", "Papaya"],
    ["Kiwi", "Apple", "Lemon", "Passionfruit"],
    ["Cherry", "Blackberry", "Apple", "Pineapple"],
    ["Passionfruit", "Grape", "Apple", "Blackberry"],
    ["Lemon", "Apple", "Strawberry", "Pear"],
    ["Pineapple", "Apple", "Kiwi", "Papaya"],
    ["Blackberry", "Cherry", "Blueberry", "Kiwi"],
    ["Grape", "Passionfruit", "Pineapple", "Papaya"],
    ["Passionfruit", "Pear", "Lemon", "Kiwi"],
    ["Apple", "Grape", "Cherry", "Pear"],
    ["Apple", "Strawberry", "Cherry", "Blueberry"],
    ["Grape", "Strawberry", "Apple", "Passionfruit"],
]

ALL_FRUITS: List[str] = [
    "Grape", "Apple", "Pear", "Blackberry", "Lemon", "Pineapple",
    "Blueberry", "Cherry", "Kiwi", "Passionfruit", "Strawberry", "Papaya",
]

# Coverage-compensation weights: some fruits appear as an answer option
# less often, so their raw vote counts are boosted to be comparable.
SPINE_WEIGHTS: Dict[str, float] = {
    "Apple": 0.6, "Grape": 0.85, "Blackberry": 0.85, "Passionfruit": 0.85,
    "Blueberry": 0.85, "Kiwi": 0.9, "Cherry": 0.9, "Lemon": 0.9,
    "Pineapple": 0.95, "Pear": 1.4, "Papaya": 1.4, "Strawberry": 1.6,
}

# ─────────────────────────────────────────────────────────────────────────
# 2. CONFIG: how each answer nudges the 8 abstract dimensions (D1-D8)
# ─────────────────────────────────────────────────────────────────────────
# ANSWER_DIMENSIONS[q][a] = list of [dimension(1-8), direction(+1/-1), magnitude(1-3)]
# points applied = magnitude * 4 (so 1->4, 2->8, 3->12)
ANSWER_DIMENSIONS: List[List[List[Tuple[int, int, int]]]] = [
    [[(3, -1, 1), (4, -1, 1), (6, 1, 2)], [(2, 1, 2), (7, 1, 2), (1, 1, 1)],
     [(3, -1, 1), (4, -1, 2), (6, -1, 1)], [(3, 1, 2), (4, 1, 2), (5, 1, 1)]],
    [[(2, 1, 3), (7, 1, 2), (5, 1, 2)], [(2, -1, 3), (7, -1, 3), (5, -1, 3)],
     [(1, 1, 3), (6, -1, 3), (8, 1, 2)], [(5, -1, 2), (6, -1, 1), (1, 1, 1)]],
    [[(2, 1, 3), (7, 1, 3), (4, 1, 1)], [(6, 1, 1), (4, -1, 1), (1, -1, 1)]],
    [[(6, 1, 3), (4, 1, 2), (8, 1, 2)], [(2, 1, 3), (7, 1, 2), (1, 1, 1)],
     [(5, -1, 2), (1, -1, 1), (8, -1, 2)], [(4, 1, 2), (3, 1, 2), (2, 1, 1)]],
    [[(5, -1, 3), (7, -1, 3), (2, -1, 2)], [(1, 1, 2), (6, -1, 2), (5, 1, 1)],
     [(5, -1, 2), (7, -1, 2), (2, -1, 2)], [(2, 1, 2), (7, 1, 2), (5, 1, 1)]],
    [[(2, 1, 2), (4, 1, 1), (8, -1, 1)], [(5, -1, 3), (7, -1, 2), (2, -1, 2)],
     [(8, 1, 3), (2, 1, 2), (7, 1, 1)], [(2, 1, 2), (1, 1, 1), (4, 1, 1)]],
    [[(1, 1, 2), (5, -1, 2), (3, 1, 1)], [(1, 1, 1), (3, 1, 1), (6, -1, 1)],
     [(3, 1, 2), (2, 1, 1), (4, 1, 1)], [(5, -1, 1), (1, 1, 1), (2, -1, 1)]],
    [[(2, 1, 3), (5, 1, 2), (7, 1, 2)], [(5, -1, 2), (2, -1, 2), (7, -1, 1)]],
    [[(2, 1, 3), (4, 1, 2), (7, 1, 2)], [(5, -1, 2), (1, 1, 2), (6, 1, 1)],
     [(2, 1, 1), (8, 1, 2), (5, -1, 1)], [(1, 1, 3), (3, 1, 2), (5, -1, 1)]],
    [[(2, 1, 3), (5, 1, 2), (4, 1, 2)], [(5, -1, 2), (2, -1, 1), (8, -1, 1)],
     [(2, 1, 2), (3, 1, 2), (7, 1, 1)], [(5, -1, 1), (2, -1, 1), (1, 1, 1)]],
    [[(2, 1, 3), (7, 1, 3), (4, 1, 2)], [(7, -1, 3), (2, -1, 3), (5, -1, 2)],
     [(1, 1, 2), (2, 1, 2), (6, -1, 1)], [(3, 1, 2), (7, -1, 1), (4, 1, 1)]],
    [[(3, -1, 2), (7, -1, 2), (5, -1, 1)], [(4, -1, 3), (3, -1, 2), (6, 1, 2)],
     [(3, 1, 3), (4, 1, 2), (5, 1, 1)], [(3, 1, 2), (4, 1, 1), (1, 1, 1)]],
    [[(7, 1, 2), (4, 1, 1), (6, 1, 1)], [(5, -1, 3), (7, -1, 2), (2, -1, 1)],
     [(4, -1, 2), (6, 1, 1), (3, -1, 1)], [(6, 1, 2), (4, 1, 1), (8, 1, 1)]],
    [[(1, 1, 3), (8, 1, 2), (3, 1, 1)], [(2, 1, 2), (7, 1, 2), (5, 1, 1)],
     [(6, -1, 2), (5, -1, 1), (1, 1, 1)], [(1, 1, 2), (5, -1, 2), (7, 1, 1)]],
    [[(3, 1, 2), (1, 1, 1), (2, 1, 1)], [(4, -1, 2), (3, -1, 2), (6, 1, 1)],
     [(8, 1, 3), (1, 1, 2), (7, 1, 1)], [(4, -1, 2), (5, -1, 2), (7, -1, 2)]],
    [[(5, -1, 2), (7, -1, 2), (2, -1, 1)], [(6, 1, 1), (4, -1, 1), (8, -1, 1)],
     [(1, 1, 1), (8, 1, 1), (3, 1, 1)], [(5, -1, 1), (1, 1, 2), (6, -1, 1)]],
    [[(1, 1, 2), (5, -1, 2), (3, 1, 1)], [(7, 1, 3), (2, 1, 3), (5, 1, 2)],
     [(7, -1, 3), (5, -1, 3), (8, 1, 1)], [(6, -1, 2), (1, 1, 2), (5, -1, 1)]],
    [[(6, 1, 2), (8, 1, 1), (4, 1, 1)], [(3, 1, 2), (1, 1, 2), (4, 1, 1)],
     [(4, 1, 1), (5, 1, 1), (3, 1, 1)], [(4, -1, 2), (6, -1, 1), (3, -1, 1)]],
    [[(1, 1, 3), (5, -1, 2), (4, -1, 2)], [(5, -1, 2), (7, -1, 2), (4, -1, 1)],
     [(3, 1, 2), (4, 1, 2), (2, 1, 1)], [(1, 1, 2), (5, -1, 1), (6, -1, 1)]],
    [[(6, 1, 2), (8, 1, 1), (4, -1, 1)], [(6, 1, 1), (8, 1, 2), (4, -1, 1)],
     [(2, 1, 2), (7, 1, 1), (8, -1, 2)], [(5, -1, 2), (6, -1, 2), (4, 1, 1)]],
    [[(6, 1, 2), (8, 1, 1), (4, -1, 1)], [(8, 1, 3), (2, 1, 2), (6, -1, 2)],
     [(2, 1, 2), (7, 1, 2), (8, -1, 1)], [(8, 1, 2), (5, -1, 2), (7, -1, 2)]],
    [[(4, 1, 2), (5, 1, 1), (8, -1, 1)], [(8, 1, 2), (1, 1, 2), (4, -1, 2)],
     [(4, -1, 2), (6, 1, 1), (3, -1, 1)], [(1, 1, 3), (4, -1, 2), (8, 1, 2)]],
]

# ─────────────────────────────────────────────────────────────────────────
# 3. CONFIG: the 96 subtypes and their ideal 8-dimensional fingerprints
# ─────────────────────────────────────────────────────────────────────────
# subtype_id -> (fruit, display_name, [D1,D2,D3,D4,D5,D6,D7,D8])
SUBTYPE_FINGERPRINTS: Dict[str, Tuple[str, str, List[int]]] = {
    "GR1": ("Grape", "The Cellar", [45, 40, 30, 25, 30, 55, 35, 55]),
    "GR2": ("Grape", "The Vine", [50, 55, 45, 40, 55, 60, 55, 50]),
    "GR3": ("Grape", "The Barrel", [40, 45, 25, 20, 35, 60, 30, 50]),
    "GR4": ("Grape", "The Press", [45, 65, 50, 70, 65, 75, 60, 45]),
    "GR5": ("Grape", "The Pour", [50, 60, 45, 35, 60, 65, 50, 60]),
    "GR6": ("Grape", "The Shade", [55, 50, 35, 30, 50, 45, 40, 65]),
    "GR7": ("Grape", "The Ripen", [55, 45, 40, 25, 40, 55, 45, 50]),
    "GR8": ("Grape", "The Cluster", [45, 40, 35, 20, 35, 50, 35, 45]),
    "AP1": ("Apple", "The Orchard", [40, 45, 35, 30, 45, 70, 40, 45]),
    "AP2": ("Apple", "The Stem", [40, 40, 30, 25, 40, 65, 35, 50]),
    "AP3": ("Apple", "The Shine", [35, 50, 30, 30, 45, 70, 45, 40]),
    "AP4": ("Apple", "The Core", [45, 45, 25, 20, 35, 65, 35, 45]),
    "AP5": ("Apple", "The Seed", [45, 45, 40, 30, 40, 65, 40, 45]),
    "AP6": ("Apple", "The Branch", [40, 50, 40, 35, 55, 70, 45, 45]),
    "AP7": ("Apple", "The Crisp", [40, 55, 30, 25, 45, 65, 45, 40]),
    "AP8": ("Apple", "The Cider", [35, 50, 35, 35, 50, 75, 40, 40]),
    "PE1": ("Pear", "The Bough", [50, 35, 30, 20, 25, 45, 20, 65]),
    "PE2": ("Pear", "The Cradle", [60, 45, 25, 15, 25, 35, 20, 80]),
    "PE3": ("Pear", "The Balance", [45, 35, 30, 20, 30, 45, 25, 60]),
    "PE4": ("Pear", "The Listen", [65, 35, 30, 15, 20, 25, 15, 80]),
    "PE5": ("Pear", "The Soften", [55, 40, 30, 20, 30, 35, 25, 70]),
    "PE6": ("Pear", "The Mend", [50, 35, 25, 15, 25, 50, 20, 65]),
    "PE7": ("Pear", "The Hearth", [55, 40, 25, 15, 25, 40, 25, 70]),
    "PE8": ("Pear", "The Heirloom", [60, 35, 20, 15, 20, 40, 20, 70]),
    "BB1": ("Blackberry", "The Thicket", [65, 20, 40, 25, 15, 35, 15, 45]),
    "BB2": ("Blackberry", "The Nightjar", [60, 20, 35, 20, 15, 40, 20, 40]),
    "BB3": ("Blackberry", "The Seedcode", [55, 25, 30, 20, 20, 50, 25, 40]),
    "BB4": ("Blackberry", "The Blackglass", [65, 15, 35, 25, 15, 35, 20, 40]),
    "BB5": ("Blackberry", "The Midnight", [60, 35, 45, 35, 30, 30, 55, 45]),
    "BB6": ("Blackberry", "The Rouge", [60, 25, 35, 20, 20, 35, 25, 45]),
    "BB7": ("Blackberry", "The Basket", [50, 20, 25, 15, 20, 50, 20, 50]),
    "BB8": ("Blackberry", "The Tart", [55, 45, 40, 40, 35, 45, 40, 40]),
    "LE1": ("Lemon", "The Peel", [30, 75, 55, 55, 70, 50, 70, 60]),
    "LE2": ("Lemon", "The Zest", [35, 80, 60, 65, 75, 45, 75, 55]),
    "LE3": ("Lemon", "The Squeeze", [35, 60, 45, 40, 55, 65, 50, 50]),
    "LE4": ("Lemon", "The Twist", [40, 70, 60, 55, 65, 45, 65, 55]),
    "LE5": ("Lemon", "The Pith", [40, 55, 40, 30, 50, 60, 45, 55]),
    "LE6": ("Lemon", "The Slice", [35, 65, 45, 40, 55, 65, 55, 45]),
    "LE7": ("Lemon", "The Spritz", [35, 65, 55, 50, 65, 55, 60, 50]),
    "LE8": ("Lemon", "The Parade", [40, 70, 55, 50, 70, 50, 70, 55]),
    "PI1": ("Pineapple", "The Crown", [50, 70, 50, 55, 65, 60, 75, 50]),
    "PI2": ("Pineapple", "The Ring", [55, 65, 50, 50, 65, 50, 65, 60]),
    "PI3": ("Pineapple", "The Spine", [45, 55, 35, 30, 50, 65, 50, 50]),
    "PI4": ("Pineapple", "The Cut", [45, 55, 40, 35, 50, 65, 50, 45]),
    "PI5": ("Pineapple", "The Bite", [50, 65, 55, 65, 60, 65, 60, 45]),
    "PI6": ("Pineapple", "The Grid", [40, 55, 40, 35, 55, 70, 45, 45]),
    "PI7": ("Pineapple", "The Glaze", [40, 60, 35, 30, 50, 65, 55, 45]),
    "PI8": ("Pineapple", "The Crate", [40, 55, 35, 30, 55, 70, 40, 45]),
    "BL1": ("Blueberry", "The Bush", [35, 25, 30, 20, 20, 55, 15, 50]),
    "BL2": ("Blueberry", "The Cluster", [40, 35, 30, 25, 30, 55, 25, 55]),
    "BL3": ("Blueberry", "The Bloom", [40, 45, 45, 40, 40, 55, 35, 45]),
    "BL4": ("Blueberry", "The Ripen", [45, 35, 35, 25, 30, 50, 25, 50]),
    "BL5": ("Blueberry", "The Burst", [40, 40, 35, 35, 35, 60, 30, 45]),
    "BL6": ("Blueberry", "The Masher", [40, 40, 30, 30, 35, 60, 25, 45]),
    "BL7": ("Blueberry", "The Jam", [45, 35, 25, 20, 25, 55, 20, 50]),
    "BL8": ("Blueberry", "The Garnish", [40, 45, 35, 30, 35, 55, 35, 45]),
    "CH1": ("Cherry", "The Pop", [40, 75, 60, 75, 75, 65, 80, 40]),
    "CH2": ("Cherry", "The Snap", [40, 65, 55, 70, 65, 70, 65, 35]),
    "CH3": ("Cherry", "The Flick", [40, 60, 55, 65, 60, 60, 60, 40]),
    "CH4": ("Cherry", "The Flare", [45, 75, 55, 60, 70, 55, 80, 40]),
    "CH5": ("Cherry", "The Cherrybomb", [45, 70, 65, 75, 70, 55, 75, 35]),
    "CH6": ("Cherry", "The Gloss", [40, 65, 45, 50, 60, 65, 65, 40]),
    "CH7": ("Cherry", "The Double", [45, 65, 55, 60, 65, 60, 70, 40]),
    "CH8": ("Cherry", "The Pit", [50, 55, 40, 40, 55, 60, 55, 45]),
    "KI1": ("Kiwi", "The Ring", [65, 40, 35, 20, 35, 50, 35, 60]),
    "KI2": ("Kiwi", "The Halo", [70, 45, 30, 15, 30, 35, 30, 75]),
    "KI3": ("Kiwi", "The Heart", [70, 35, 30, 15, 25, 45, 25, 65]),
    "KI4": ("Kiwi", "The Grove", [65, 55, 40, 25, 55, 35, 55, 65]),
    "KI5": ("Kiwi", "The Counsel", [70, 40, 35, 20, 30, 40, 30, 65]),
    "KI6": ("Kiwi", "The Ember", [60, 35, 25, 15, 25, 50, 25, 60]),
    "KI7": ("Kiwi", "The Pattern", [70, 35, 35, 20, 25, 40, 30, 55]),
    "KI8": ("Kiwi", "The Fuzz", [65, 40, 30, 15, 25, 40, 25, 70]),
    "PF1": ("Passionfruit", "The Pulse", [65, 75, 65, 70, 70, 65, 70, 60]),
    "PF2": ("Passionfruit", "The Bloom", [65, 75, 55, 55, 70, 50, 70, 65]),
    "PF3": ("Passionfruit", "The Forge", [70, 60, 55, 50, 50, 70, 50, 65]),
    "PF4": ("Passionfruit", "The Current", [65, 60, 70, 55, 60, 55, 55, 55]),
    "PF5": ("Passionfruit", "The Devotion", [80, 55, 40, 30, 35, 50, 40, 75]),
    "PF6": ("Passionfruit", "The Sparkle", [65, 80, 60, 65, 75, 50, 80, 60]),
    "PF7": ("Passionfruit", "The Stormchild", [80, 55, 60, 35, 25, 30, 45, 75]),
    "PF8": ("Passionfruit", "The Drift", [70, 50, 75, 50, 45, 35, 40, 60]),
    "ST1": ("Strawberry", "The Patch", [60, 50, 35, 30, 40, 55, 30, 75]),
    "ST2": ("Strawberry", "The Sweetener", [60, 55, 35, 25, 40, 45, 35, 80]),
    "ST3": ("Strawberry", "The Carton", [55, 50, 30, 25, 40, 60, 30, 70]),
    "ST4": ("Strawberry", "The Spoon", [65, 50, 30, 20, 35, 45, 25, 80]),
    "ST5": ("Strawberry", "The Quilt", [65, 55, 30, 20, 35, 45, 30, 80]),
    "ST6": ("Strawberry", "The Porch", [60, 60, 35, 30, 50, 50, 45, 75]),
    "ST7": ("Strawberry", "The Ribbon", [60, 55, 30, 25, 40, 55, 40, 70]),
    "ST8": ("Strawberry", "The Little", [65, 50, 25, 15, 30, 45, 25, 80]),
    "PA1": ("Papaya", "The Sun", [55, 70, 60, 55, 70, 50, 70, 60]),
    "PA2": ("Papaya", "The Pulp", [55, 65, 60, 55, 65, 50, 60, 60]),
    "PA3": ("Papaya", "The Cavity", [55, 65, 55, 50, 65, 45, 65, 60]),
    "PA4": ("Papaya", "The Pattern", [50, 60, 55, 50, 60, 55, 55, 50]),
    "PA5": ("Papaya", "The Split", [55, 65, 60, 60, 65, 50, 65, 55]),
    "PA6": ("Papaya", "The Lime Squeeze", [50, 70, 60, 60, 65, 55, 65, 50]),
    "PA7": ("Papaya", "The Boat", [50, 60, 55, 45, 60, 60, 55, 55]),
    "PA8": ("Papaya", "The Seedswater", [60, 50, 50, 40, 45, 50, 40, 60]),
}

MAX_EUCLIDEAN = math.sqrt(8 * 100 * 100)  # max possible distance across 8 dims of 0-100


# ─────────────────────────────────────────────────────────────────────────
# 4. SCORING LOGIC
# ─────────────────────────────────────────────────────────────────────────
def compute_dimension_scores(answers: List[int]) -> List[float]:
    """
    Turn 22 answers into 8 dimension scores (0-100, baseline 50).
    `answers[q]` = the chosen option index (0-3) for question q.
    """
    dims = [50.0] * 8
    for q_index, answer_index in enumerate(answers):
        question_mappings = ANSWER_DIMENSIONS[q_index] if q_index < len(ANSWER_DIMENSIONS) else None
        if not question_mappings:
            continue
        answer_signals = question_mappings[answer_index] if answer_index < len(question_mappings) else None
        if not answer_signals:
            continue
        for dim_index, direction, magnitude in answer_signals:
            points = magnitude * 4  # 1->4, 2->8, 3->12
            dims[dim_index - 1] += direction * points  # dims are 1-based in config

    return [max(0.0, min(100.0, d)) for d in dims]


def compute_spine_scores(answers: List[int]) -> Dict[str, float]:
    """
    Tally which fruit each answer "voted" for, normalize by number of
    questions answered, then apply the coverage-compensation weight.
    """
    raw = {fruit: 0 for fruit in ALL_FRUITS}
    for q_index, answer_index in enumerate(answers):
        fruit_map = QUESTION_FRUITS[q_index] if q_index < len(QUESTION_FRUITS) else None
        if not fruit_map or answer_index >= len(fruit_map):
            continue
        raw[fruit_map[answer_index]] += 1

    total_answers = len(answers)
    return {
        fruit: (raw[fruit] / total_answers) * 100 * SPINE_WEIGHTS.get(fruit, 1.0)
        for fruit in ALL_FRUITS
    }


def euclidean_distance(user_dims: List[float], fingerprint: List[int]) -> float:
    return math.sqrt(sum((user_dims[i] - fingerprint[i]) ** 2 for i in range(8)))


def calculate_personality(answers: List[int]) -> Dict:
    """
    Main entry point.
    `answers`: list of 22 ints, each 0-3 (the chosen option per question).
    Returns: { fruit_type, subtype_id, subtype_name, dimension_scores, top3 }
    """
    user_dims = compute_dimension_scores(answers)
    spine_scores = compute_spine_scores(answers)

    scored = []
    for subtype_id, (fruit, name, fingerprint) in SUBTYPE_FINGERPRINTS.items():
        distance = euclidean_distance(user_dims, fingerprint)
        dimensional_proximity = 100 - (distance / MAX_EUCLIDEAN * 100)
        spine_score = min(100.0, spine_scores.get(fruit, 0.0))
        final_score = (spine_score * 0.45) + (dimensional_proximity * 0.55)
        scored.append({
            "subtype_id": subtype_id,
            "fruit": fruit,
            "name": name,
            "final_score": final_score,
        })

    scored.sort(key=lambda s: s["final_score"], reverse=True)
    winner = scored[0]

    return {
        "fruit_type": winner["fruit"],
        "subtype_id": winner["subtype_id"],
        "subtype_name": winner["name"],
        "dimension_scores": [round(d) for d in user_dims],
        "top3": [
            {"subtype_id": s["subtype_id"], "fruit": s["fruit"], "name": s["name"],
             "score": round(s["final_score"], 2)}
            for s in scored[:3]
        ],
    }


# ─────────────────────────────────────────────────────────────────────────
# 5. WORKED EXAMPLE
# ─────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # 22 example answers (each 0-3), one per question
    example_answers = [2, 1, 1, 3, 0, 1, 3, 1, 2, 3, 1, 1, 3, 2, 1, 0, 2, 0, 3, 1, 3, 0]

    result = calculate_personality(example_answers)

    print(f"Fruit type: {result['fruit_type']}")
    print(f"Subtype:    {result['subtype_id']} — {result['subtype_name']}")
    print(f"Dimensions (D1-D8): {result['dimension_scores']}")
    print("Top 3 matches:")
    for match in result["top3"]:
        print(f"  {match['subtype_id']} ({match['fruit']} — {match['name']}): {match['score']}")