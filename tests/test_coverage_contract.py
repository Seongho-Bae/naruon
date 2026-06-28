"""Regression test for the OpenCode coverage evidence contract."""

from coverage_contract.contract import coverage_contract_status


def test_coverage_contract_status_is_ok() -> None:
    """Keep the generic coverage evidence contract fully exercised."""

    assert coverage_contract_status() == "ok"

