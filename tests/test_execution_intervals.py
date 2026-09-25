import asyncio

import pytest

from home_ai_cluster.core.execution_intervals import ExecutionIntervalCardinality


@pytest.mark.parametrize("limit", [0, -1])
def test_execution_interval_limit_must_be_positive(limit: int) -> None:
    with pytest.raises(ValueError, match="positive integer"):
        ExecutionIntervalCardinality(limit=limit)


def test_execution_interval_limit_defaults_to_one() -> None:
    async def run() -> None:
        intervals = ExecutionIntervalCardinality()

        assert await intervals.try_enter() is True
        assert intervals.value == 1
        assert await intervals.try_enter() is False
        assert intervals.value == 1
        await intervals.exit()
        assert intervals.value == 0

    asyncio.run(run())


def test_execution_interval_limit_two_bounds_concurrent_entries() -> None:
    async def run() -> None:
        intervals = ExecutionIntervalCardinality(limit=2)

        entered = await asyncio.gather(
            intervals.try_enter(), intervals.try_enter(), intervals.try_enter()
        )

        assert entered.count(True) == 2
        assert entered.count(False) == 1
        assert intervals.value == 2
        await intervals.exit()
        await intervals.exit()
        assert intervals.value == 0

    asyncio.run(run())
