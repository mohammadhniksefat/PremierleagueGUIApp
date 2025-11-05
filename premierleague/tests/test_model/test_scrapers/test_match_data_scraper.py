import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from model.scrapers.match_data_scraper import MatchDataScraper, PlaywrightRequestHandler

VALID_URL = "https://www.premierleague.com/match/116057"
INVALID_URL = "https://google.com"

EXPECTED = {
    "timestamp": 1738513800000,
    "round_number": 24,
    "referee_name": "Peter Bankes",
    "home_team_data":{
        "name": "Arsenal",
        "score": 5 
    },
    "away_team_data":{
        "name": "Manchester City",
        "score": 1
    }
}

GET_METHODS = [
    "get_all_data",
    "get_timestamp",
    "get_round_number",
    "get_referee_name",
    "get_home_team_data",
    "get_away_team_data"
]


def test_init_raises_value_error_for_invalid_url():
    with patch("model.scrapers.match_data_scraper.UrlValidator.validate_match_page_url", return_value=False):
        with pytest.raises(ValueError, match="the url provided isn't valid"):
            MatchDataScraper(INVALID_URL)

@patch("model.scrapers.match_data_scraper.UrlValidator.validate_match_page_url", return_value=True)
def test_init_sets_internal_state(mock_validate):
    scraper = MatchDataScraper(VALID_URL)

    # URL is stored correctly
    assert scraper._base_url == VALID_URL
    assert scraper._initialized is False

    # Check match_data structure
    assert isinstance(scraper.match_data, dict)
    assert "timestamp" in scraper.match_data
    assert "home_team_data" in scraper.match_data
    assert scraper.match_data["home_team_data"] == {
        "name": str(),
        "score": int()
    }

    assert scraper.match_data["away_team_data"] == {
        "name": str(),
        "score": int()
    }


def test_match_data_scraper_calls_super_init():
    with patch("model.scrapers.match_data_scraper.UrlValidator.validate_match_page_url", return_value=True), \
         patch("model.scrapers.match_data_scraper.PremierleagueWebsiteScraper.__init__", return_value=None) as mock_super_init:

        scraper = MatchDataScraper(VALID_URL)

        mock_super_init.assert_called_once()


@pytest.mark.asyncio
@patch("model.scrapers.match_data_scraper.UrlValidator.validate_match_page_url", return_value=True)
@patch("model.scrapers.match_data_scraper.PlaywrightRequestHandler")
async def test_initialize_sets_state(mock_handler_class, mock_validator):
    # Arrange
    mock_handler_instance = AsyncMock()
    mock_handler_class.return_value = mock_handler_instance

    scraper = MatchDataScraper(VALID_URL)

    # Act
    await scraper.initialize()

    # Assert
    # Check if handler is assigned
    assert scraper._request_handler == mock_handler_instance

    # Check if configure was awaited
    mock_handler_instance.configure.assert_awaited_once()

    # Check if initialized flag is set
    assert scraper._initialized is True


@pytest.mark.asyncio
@pytest.mark.parametrize("method_name", GET_METHODS)
async def test_get_methods_raise_if_not_initialized(method_name):
    scraper = MatchDataScraper(VALID_URL)

    method = getattr(scraper, method_name)

    with pytest.raises(RuntimeError, match="scraper doesn't initialized yet"):
        await method()

        
@pytest.mark.asyncio
@pytest.mark.parametrize("method_name, data_key", [
    ("get_timestamp", "timestamp"),
    ("get_round_number", "round_number"),
    ("get_referee_name", "referee_name"),
    ("get_home_team_data", "home_team_data"),
    ("get_away_team_data", "away_team_data")
])
async def test_get_methods_uses_cache(method_name, data_key):
    # Initialize scraper and set the data in match_data
    scraper = MatchDataScraper(VALID_URL)
    scraper._initialized = True
    scraper.match_data[data_key] = "cached_value" if data_key != "home_team_data" and data_key != "away_team_data" else {
        "name": "Arsenal",
        "score": 5
    }

    # Patch _create_context_then_callback to avoid real requests
    with patch.object(scraper, "_create_context_then_callback", new_callable=AsyncMock) as mock_callback:
        # Call the method
        method = getattr(scraper, method_name)
        result = await method()

        # Check if the method returned the cached value
        if data_key == "home_team_data" or data_key == "away_team_data":
            expected = {"name": "Arsenal", "score": 5}
        else:
            expected = "cached_value"

        assert result == expected
        mock_callback.assert_not_called()  # Ensure _create_context_then_callback was not called

async def goto_side_effect(page, url):
    await page.goto(url)

@pytest.mark.asyncio
async def test_get_timestamp():
    scraper = MatchDataScraper(VALID_URL)
    scraper._request_handler = MagicMock(spec=PlaywrightRequestHandler)
    scraper._request_handler.goto = AsyncMock(side_effect=goto_side_effect)
    scraper._initialized = True

    result = await scraper.get_timestamp()
    assert isinstance(result, int)
    assert result == EXPECTED["timestamp"]
    assert scraper.match_data["timestamp"] == result

@pytest.mark.asyncio
async def test_get_round_number():
    scraper = MatchDataScraper(VALID_URL)
    scraper._request_handler = MagicMock(spec=PlaywrightRequestHandler)
    scraper._request_handler.goto = AsyncMock(side_effect=goto_side_effect)
    scraper._initialized = True

    result = await scraper.get_round_number()
    assert isinstance(result, int)
    assert result == EXPECTED["round_number"]
    assert scraper.match_data["round_number"] == result

@pytest.mark.asyncio
async def test_get_referee_name():
    scraper = MatchDataScraper(VALID_URL)
    scraper._request_handler = MagicMock(spec=PlaywrightRequestHandler)
    scraper._request_handler.goto = AsyncMock(side_effect=goto_side_effect)
    scraper._initialized = True

    result = await scraper.get_referee_name()
    assert isinstance(result, str)
    assert result == EXPECTED["referee_name"]
    assert scraper.match_data["referee_name"] == result

@pytest.mark.asyncio
async def test_get_home_team_data():
    scraper = MatchDataScraper(VALID_URL)
    scraper._request_handler = MagicMock(spec=PlaywrightRequestHandler)
    scraper._request_handler.goto = AsyncMock(side_effect=goto_side_effect)
    scraper._initialized = True

    result = await scraper.get_home_team_data()
    assert isinstance(result, dict)
    assert "name" in result and "score" in result
    assert result == EXPECTED["home_team_data"]
    assert scraper.match_data["home_team_data"] == result

@pytest.mark.asyncio
async def test_get_away_team_data():
    scraper = MatchDataScraper(VALID_URL)
    scraper._request_handler = MagicMock(spec=PlaywrightRequestHandler)
    scraper._request_handler.goto = AsyncMock(side_effect=goto_side_effect)
    scraper._initialized = True

    result = await scraper.get_away_team_data()
    assert isinstance(result, dict)
    assert "name" in result and "score" in result
    assert result == EXPECTED["away_team_data"]
    assert scraper.match_data["away_team_data"] == result
