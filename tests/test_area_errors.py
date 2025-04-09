import pytest
from rosreestr2coord.parser import Area, NoCoordinatesException
from rosreestr2coord.request.exceptions import RequestException, TimeoutException


@pytest.mark.unit
def test_usage_handles_invalid_area_type():
    """Catch ValueError from invalid area_type"""
    try:
        Area("75:09:999", area_type=999, with_log=False)
    except ValueError as e:
        assert "Invalid area_type specified" in str(e)
        return
    pytest.fail("Expected ValueError was not raised")


@pytest.mark.unit
def test_usage_handles_timeout_exception(monkeypatch):
    """Catch TimeoutException during make_request"""

    def raise_timeout(*args, **kwargs):
        raise TimeoutException("timeout simulated")

    monkeypatch.setattr("rosreestr2coord.parser.Area.make_request", raise_timeout)

    try:
        Area("75:09:999", area_type=1, with_log=False)
    except TimeoutException as e:
        assert "timeout" in str(e)
        return
    pytest.fail("Expected TimeoutException was not raised")


@pytest.mark.unit
def test_usage_handles_request_exception(monkeypatch):
    """Catch generic RequestException"""

    def raise_error(*args, **kwargs):
        raise RequestException("API failure")

    monkeypatch.setattr("rosreestr2coord.parser.Area.make_request", raise_error)

    try:
        Area("75:09:999", area_type=1, with_log=False)
    except RequestException as e:
        assert "API failure" in str(e)
        return
    pytest.fail("Expected RequestException was not raised")


@pytest.mark.unit
def test_usage_handles_to_kml_without_feature():
    """Catch NoCoordinatesException from .to_kml()"""
    area = Area("75:09:000000", area_type=1, with_log=False)
    area.feature = None

    try:
        area.to_kml()
    except NoCoordinatesException as e:
        assert "No geometry feature" in str(e)
        return
    pytest.fail("Expected NoCoordinatesException was not raised")
