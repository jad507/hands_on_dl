"""
Tests for the phase-1 chunker.

This function is now load-bearing for the project's main finding: the claim is
that a block's classification changes when the batch it is judged inside is
composed differently, and `--chunk-offset` is how that gets tested under control
rather than as a natural experiment.

The invariant that matters is coverage. A chunker that dropped a block would
lower N; one that duplicated a block would raise it and double-count a
classification. Either changes the denominator of every rate in the study while
producing output that looks entirely normal. So coverage is asserted across the
whole parameter grid rather than spot-checked.

Run:  python -m pytest tests/ -v
"""

import os

import pytest

# The module builds its config at import time and resolve_model_path needs a
# root; nothing here loads a model.
os.environ.setdefault("HODL_MODELS_ROOT", "D:\\LLM")

from llm_classify_human_themes import p1_chunks  # noqa: E402


@pytest.mark.parametrize("n", [0, 1, 2, 3, 4, 7, 10, 31, 100])
@pytest.mark.parametrize("size", [1, 2, 3, 5, 8])
@pytest.mark.parametrize("offset", [0, 1, 2, 3, 7])
def test_every_block_appears_exactly_once_in_order(n, size, offset):
    """The invariant. Across the whole grid, chunking is a partition of the
    block list that preserves order."""
    blocks = list(range(n))
    flat = [b for chunk in p1_chunks(blocks, size, offset) for b in chunk]
    assert flat == blocks


@pytest.mark.parametrize("size", [1, 2, 3, 5])
@pytest.mark.parametrize("offset", [0, 1, 2])
def test_no_chunk_is_empty(size, offset):
    """An empty chunk would become an LLM call with no blocks in it."""
    for chunk in p1_chunks(list(range(20)), size, offset):
        assert chunk


@pytest.mark.parametrize("size", [1, 2, 3, 5, 8])
def test_no_chunk_exceeds_the_size(size):
    for chunk in p1_chunks(list(range(50)), size, 0):
        assert len(chunk) <= size


def test_default_chunking_is_unchanged():
    """The committed corpus was produced at size 3, offset 0. If this grouping
    ever changes, nothing in the corpus is comparable to anything new."""
    assert p1_chunks(list(range(10)), 3, 0) == [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]


def test_offset_shifts_every_boundary_after_the_first():
    """The whole point of the parameter: block 3 moves from the head of its
    chunk to the middle of a different one, while the block list is untouched."""
    assert p1_chunks(list(range(10)), 3, 1) == [[0], [1, 2, 3], [4, 5, 6], [7, 8, 9]]
    assert p1_chunks(list(range(10)), 3, 2) == [[0, 1], [2, 3, 4], [5, 6, 7], [8, 9]]


def test_offset_equal_to_size_is_the_same_as_no_offset():
    """offset wraps modulo size, so offset 3 at size 3 is a no-op rather than
    dropping three blocks."""
    assert p1_chunks(list(range(10)), 3, 3) == p1_chunks(list(range(10)), 3, 0)
    assert p1_chunks(list(range(10)), 3, 6) == p1_chunks(list(range(10)), 3, 0)


def test_offset_changes_company_for_most_blocks():
    """Quantifies what the offset actually does, which is the manipulation the
    experiment applies: at size 3 offset 1, all but the first block gets a
    different set of neighbours."""
    blocks = list(range(30))
    def company(chunks):
        out = {}
        for c in chunks:
            for b in c:
                out[b] = tuple(x for x in c if x != b)
        return out
    a = company(p1_chunks(blocks, 3, 0))
    b = company(p1_chunks(blocks, 3, 1))
    changed = sum(1 for k in a if a[k] != b[k])
    assert changed >= 28, f"offset changed company for only {changed} of 30 blocks"


def test_chunk_size_one_gives_every_block_its_own_call():
    """The no-context condition. If the effect is chunk company, this should
    remove it entirely."""
    chunks = p1_chunks(list(range(7)), 1, 0)
    assert chunks == [[0], [1], [2], [3], [4], [5], [6]]
    for c in chunks:
        assert len(c) == 1


def test_empty_block_list_gives_no_chunks():
    assert p1_chunks([], 3, 0) == []
    assert p1_chunks([], 3, 2) == []


def test_size_smaller_than_one_is_refused():
    """Silently coercing to 1 would produce a run whose provenance says one
    thing and whose behaviour is another."""
    with pytest.raises(ValueError):
        p1_chunks([1, 2, 3], 0)
    with pytest.raises(ValueError):
        p1_chunks([1, 2, 3], -1)


def test_size_larger_than_the_block_list():
    assert p1_chunks([1, 2], 10, 0) == [[1, 2]]
