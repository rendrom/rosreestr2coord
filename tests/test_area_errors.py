import pytest
from rosreestr2coord.parser import Area


@pytest.mark.unit
def test_invalid_area_type_raises_value_error():
    with pytest.raises(ValueError) as exc:
        Area("75:09-123", area_type=999).get_geometry()
    assert "Invalid area_type" in str(exc.value)


@pytest.mark.unit
def test_nonexistent_code_returns_none(monkeypatch):
    def mock_request(*args, **kwargs):
        return {"data": {"features": []}}  # empty result

    monkeypatch.setattr("rosreestr2coord.parser.Area.make_request", mock_request)

    area = Area("99:99:999999", area_type=1)
    result = area.get_geometry()
    assert result is None
    assert area.feature is None


@pytest.mark.unit
def test_make_request_timeout(monkeypatch):
    def mock_request(*args, **kwargs):
        raise TimeoutError("timeout")

    monkeypatch.setattr("rosreestr2coord.parser.Area.make_request", mock_request)

    area = Area("75:09-999", area_type=1)
    # make sure it doesn't raise on __init__, but logs the error
    assert area.feature is None
