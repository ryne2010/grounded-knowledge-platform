from __future__ import annotations

from app.retrieval_profile import LEXICAL_INDEX_NAME, VECTOR_INDEX_NAME, summarize_plan_json


def test_summarize_plan_json_detects_expected_index_usage() -> None:
    plan = {
        "Plan": {
            "Node Type": "Limit",
            "Plan Rows": 40,
            "Total Cost": 23.4,
            "Plans": [
                {
                    "Node Type": "Bitmap Heap Scan",
                    "Relation Name": "chunks",
                    "Plans": [
                        {
                            "Node Type": "Bitmap Index Scan",
                            "Index Name": LEXICAL_INDEX_NAME,
                        }
                    ],
                }
            ],
        },
        "Planning Time": 0.8,
        "Execution Time": 1.9,
    }

    summary = summarize_plan_json(plan, expected_index=LEXICAL_INDEX_NAME)

    assert summary.index_used is True
    assert summary.indexes_seen == (LEXICAL_INDEX_NAME,)
    assert summary.seq_scan_relations == ()
    assert summary.plan_rows == 40
    assert summary.total_cost == 23.4
    assert summary.error is None


def test_summarize_plan_json_flags_seq_scan_and_missing_index() -> None:
    plan = {
        "Plan": {
            "Node Type": "Seq Scan",
            "Relation Name": "embeddings",
            "Plan Rows": 100,
            "Total Cost": 99.0,
            "Plans": [],
        },
        "Planning Time": 1.2,
        "Execution Time": 8.7,
    }

    summary = summarize_plan_json(plan, expected_index=VECTOR_INDEX_NAME)

    assert summary.index_used is False
    assert summary.indexes_seen == ()
    assert summary.seq_scan_relations == ("embeddings",)
    assert summary.plan_rows == 100
    assert summary.total_cost == 99.0
    assert summary.error is None
