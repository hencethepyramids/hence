import pytest
import httpx
import respx


@pytest.fixture
def bm_server_id() -> str:
    return "12345678"


@pytest.fixture
def mock_bm_api():
    """Context manager that mocks BattleMetrics API responses."""
    with respx.mock(base_url="https://api.battlemetrics.com", assert_all_called=False) as mock:
        yield mock
