from __future__ import annotations

from typing import List, Tuple

import pytest

from tetra3 import breadth_first_combinations


@pytest.mark.parametrize(
    ("seq", "r", "expected"),
    [
        ([1, 2, 3], 1, [(1,), (2,), (3,)]),
        ([1, 2, 3], 2, [(1, 2), (1, 3), (2, 3)]),
        ([1, 2, 3], 3, [(1, 2, 3)]),
        ([1, 2, 3, 4, 5, 6], 3, [(1, 2, 3), (1, 2, 4), (1, 3, 4), (2, 3, 4), (1, 2, 5), (1, 3, 5),
                                 (2, 3, 5), (1, 4, 5), (2, 4, 5), (3, 4, 5), (1, 2, 6), (1, 3, 6),
                                 (2, 3, 6), (1, 4, 6), (2, 4, 6), (3, 4, 6), (1, 5, 6), (2, 5, 6),
                                 (3, 5, 6), (4, 5, 6)]),
        ([1, 2, 3, 4, 5, 6], 4, [(1, 2, 3, 4), (1, 2, 3, 5), (1, 2, 4, 5), (1, 3, 4, 5),
                                 (2, 3, 4, 5), (1, 2, 3, 6), (1, 2, 4, 6), (1, 3, 4, 6),
                                 (2, 3, 4, 6), (1, 2, 5, 6), (1, 3, 5, 6), (2, 3, 5, 6),
                                 (1, 4, 5, 6), (2, 4, 5, 6), (3, 4, 5, 6)]),
    ]
)
def test_breadth_first_combinations(seq: List[int], r: int, expected: List[Tuple]):
    result = list(breadth_first_combinations.breadth_first_combinations(seq, r))
    assert result == expected
