import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from premierleague.model.scrapers.tables_data_scraper import TablesDataScraper
from premierleague.model.scrapers.premierleague_website_scraper import PremierleagueWebsiteScraper
from premierleague.tests.utils import load_fixture
from collections import Counter
from bs4 import BeautifulSoup   

@pytest.fixture
def tables_page():
    # Fixture to load HTML content of the tables page for testing
    return load_fixture('tables_page.html')

@pytest.fixture
def expected_tables_data():
    # Fixture to provide expected parsed data from the tables page
    return [
  {
    "position": 1,
    "team_name": "arsenal",
    "played": 38,
    "won": 26,
    "drawn": 12,
    "lost": 0,
    "goals_for": 73,
    "goals_against": 26,
    "goals_difference": 47,
    "points": 90
  },
  {
    "position": 2,
    "team_name": "chelsea",
    "played": 38,
    "won": 24,
    "drawn": 7,
    "lost": 7,
    "goals_for": 67,
    "goals_against": 30,
    "goals_difference": 37,
    "points": 79
  }
]

@patch.object(PremierleagueWebsiteScraper, '__init__', return_value=None) 
def test_init_sets_up_state_correctly(mock_parent_initializer):
    # Test that TablesDataScraper initializes its state properly,
    # including calling its parent class initializer and setting attributes
    scraper = TablesDataScraper()

    # Assert parent class __init__ was called exactly once with scraper instance
    mock_parent_initializer.assert_called_once()

    # Assert that _base_url attribute exists and is a string
    assert hasattr(scraper, '_base_url')
    assert isinstance(scraper._base_url, str)

    # Assert that _initialized attribute exists and is initially False
    assert hasattr(scraper, '_initialized')
    assert scraper._initialized == False

    # Test that providing a custom URL sets _base_url accordingly
    custom_url = "https://example.com"
    scraper = TablesDataScraper(url=custom_url)
    assert scraper._base_url == custom_url


@pytest.mark.asyncio
@patch('premierleague.model.scrapers.request_handler.RequestHandler.__new__')
async def test_initialize_method_behavior(mock_request_handler, tables_page):
    # Mock instance of RequestHandler with async configure and get methods
    mock_request_handler_object = MagicMock()
    mock_configure_method = AsyncMock()
    mock_get_method = AsyncMock(return_value=tables_page)

    mock_request_handler_object.configure = mock_configure_method
    mock_request_handler_object.get = mock_get_method
    mock_request_handler.return_value = mock_request_handler_object

    scraper = TablesDataScraper()
    await scraper.initialize()

    # Assert RequestHandler class was instantiated once
    mock_request_handler.assert_called_once()
    # Assert configure coroutine was awaited exactly once
    mock_request_handler_object.configure.assert_awaited_once()
    # Assert get coroutine was awaited once with the scraper's base URL
    mock_request_handler_object.get.assert_awaited_once_with(scraper._base_url)

    # Assert _request_handler attribute is set correctly
    assert scraper._request_handler == mock_request_handler_object
    # Assert _initialized flag is True
    assert scraper._initialized is True

    # Assert _structure is a BeautifulSoup object created from the returned HTML
    assert isinstance(scraper._structure, BeautifulSoup)
    assert scraper._structure.decode() == BeautifulSoup(tables_page, 'html.parser').decode()
    

@pytest.mark.asyncio
async def test_scrape_tables_data_method_raise_if_not_initialized():
    # Test that calling get_tables_data without initializing raises RuntimeError
    scraper = TablesDataScraper()

    # Expect RuntimeError with message if scraper is not initialized
    with pytest.raises(RuntimeError, match="scraper doesn't initialized yet"):
        await scraper.get_tables_data()


@pytest.mark.asyncio
async def test_scrape_tables_data(tables_page, expected_tables_data):
    # Test get_tables_data returns correct parsed data from the given HTML structure
    scraper = TablesDataScraper()
    scraper._initialized = True
    scraper._structure = BeautifulSoup(tables_page, 'html.parser')  # Manually set HTML structure (simulate initialized state)

    result = await scraper.get_tables_data()  # Parse tables data

    # Assert the parsed result matches expected data regardless of order
    assert result == expected_tables_data
