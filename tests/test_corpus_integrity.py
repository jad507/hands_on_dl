"""
Corpus integrity, pinned.

These tests run against the real corpus in `downloads/`, not a fixture. That is
deliberate: the problems they guard against are not code bugs, they are files
quietly drifting out of shape, and a fixture cannot detect that.

The known problems are listed explicitly rather than tolerated silently, so the
suite is green today and turns red the moment a *third* stale file appears or
one of the known two is cleaned up (at which point the pin should be removed).

The chain these numbers close, because it cost real time to work out:

    81  files in downloads/comments
    -3  meetings no model has ever coded
    ----
    78  coded "meetings" -- the number the ISLS audit and upgrade plan quote
    -2  stale pre-filtered duplicates of meetings already present as variants
    ----
    76  legitimately coded files, covering 50 distinct meetings

Skipped automatically when the corpus is absent, so the suite still runs on a
checkout without `downloads/`.

Run:  python -m pytest tests/ -v
"""

import pytest

import audit_corpus
import paths

pytestmark = pytest.mark.skipif(
    not (paths.COMMENTS_DIR.is_dir() and paths.OUTPUTS_ROOT.is_dir()),
    reason="corpus not present on this machine",
)

# The two files known to be in the superseded `commenter_blocks` schema.
# They shadow meetings that already exist as _standard/_exclusive pairs, and
# because get_blocks() falls back silently, all seven models coded them against
# a pre-filtered 31-block input instead of the full 243-block meeting.
KNOWN_LEGACY = {
    "City Council Committee Meeting - October 6, 2025 [bubudvmIB_E]",
    "City Council Meeting - August 12, 2025 [Pg4nxjg-PUw]",
}

# Meetings present in the corpus that no model has coded. Not a defect as such,
# but the reason every count in the planning documents is 78 and not 81.
KNOWN_UNCODED = {
    "City Council Meeting - April 22, 2025 [amJ3tiQPgZQ]",
    "City Council Meeting - October 14, 2025 [ExizLiftTlk]",
    "Historical Commission Meeting - April 21, 2025 [I8Bxek3mQvI]",
}


@pytest.fixture(scope="module")
def result():
    return audit_corpus.audit(paths.COMMENTS_DIR, paths.OUTPUTS_ROOT)


def test_no_unexpected_legacy_schema_files(result):
    """A third stale file appearing must fail loudly rather than quietly
    inflating a count that ends up in a paper."""
    found = set(result["findings"].get("legacy_schema", []))
    assert found == KNOWN_LEGACY, (
        f"legacy-schema files changed.\n"
        f"  newly stale: {sorted(found - KNOWN_LEGACY)}\n"
        f"  now clean:   {sorted(KNOWN_LEGACY - found)}\n"
        f"If these were cleaned up deliberately, update KNOWN_LEGACY."
    )


def test_stale_files_are_exactly_the_ones_shadowing_variant_pairs(result):
    """The two defects are the same two files: each stale plain file sits
    alongside a _standard/_exclusive pair for the same meeting."""
    shadows = set(result["findings"].get("plain_shadows_variants", []))
    assert shadows == KNOWN_LEGACY


def test_no_files_in_an_unrecognised_schema(result):
    """Unlike the legacy case, this one has no known instances and must stay
    empty: a file matching neither shape would be silently read as zero blocks."""
    assert result["findings"].get("unknown_schema", []) == []


def test_every_source_file_is_readable(result):
    assert result["findings"].get("unreadable", []) == []


def test_every_model_output_is_readable(result):
    assert result["findings"].get("unreadable_output", []) == []


def test_no_model_output_lacks_a_source_meeting(result):
    """An output with no source cannot be checked, compared or re-run."""
    assert result["findings"].get("output_without_source", []) == []


def test_no_output_cites_a_block_id_the_source_does_not_have(result):
    """Grammar-constrained decoding guarantees valid JSON, not valid block ids.
    A model could still emit an id that does not exist. Currently none do, and
    that is worth knowing rather than assuming."""
    assert result["findings"].get("unknown_block_ids", []) == []


def test_no_output_recorded_chunk_errors(result):
    """The resume logic re-runs any meeting with n_chunk_errors > 0, so a
    nonzero count here means a run was left unfinished."""
    assert result["findings"].get("chunk_errors", []) == []


def test_uncoded_meetings_are_the_known_three(result):
    found = set(result["findings"].get("uncoded_meetings", []))
    assert found == KNOWN_UNCODED, (
        f"the set of uncoded meetings changed: "
        f"newly uncoded {sorted(found - KNOWN_UNCODED)}, "
        f"newly coded {sorted(KNOWN_UNCODED - found)}"
    )


def test_the_count_chain_adds_up(result):
    """81 - 3 uncoded = 78 coded, of which 2 are stale duplicates.

    Every planning document in this project quotes 78. This test is what makes
    that number checkable instead of remembered."""
    n_files = result["n_files"]
    uncoded = len(result["findings"].get("uncoded_meetings", []))
    legacy = len(result["findings"].get("legacy_schema", []))
    assert n_files == 81
    assert n_files - uncoded == 78
    assert n_files - uncoded - legacy == 76


def test_distinct_meetings_after_collapsing_variants(result):
    """53 distinct meetings, not the 55 the ISLS audit states. The audit assumed
    26 pairs plus 29 singles; in fact two of those 'singles' are the stale files
    shadowing pairs, so the real split is 26 multi-variant meetings and 27
    single-variant ones."""
    assert result["n_meetings"] == 53
