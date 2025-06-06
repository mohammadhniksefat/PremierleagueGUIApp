import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bs4 import BeautifulSoup
from tests.utils import load_fixture
from model.scrapers.club_urls_scraper import ClubUrlsScraper

@pytest.fixture
def clubs_page_html():
    return load_fixture('clubs_page.html')

@pytest.mark.asyncio
@patch("model.scrapers.club_urls_scraper.BeautifulSoup")
@patch("model.scrapers.club_urls_scraper.RequestHandler.__new__")
async def test_initialize_calls_handler_and_parses_html(mock_new, mock_bs):
    # Mock RequestHandler singleton instance
    mock_handler_instance = AsyncMock()
    mock_new.return_value = mock_handler_instance

    # Define expected HTML return
    fake_html = "<html><body><h1>Test</h1></body></html>"
    mock_handler_instance.get.return_value = fake_html

    # Mock BeautifulSoup instance
    mock_soup_instance = MagicMock()
    mock_bs.return_value = mock_soup_instance

    scraper = ClubUrlsScraper()
    expected_url = scraper._base_url

    # Act
    await scraper.initialize()

    # Assert
    # 1. __new__ returns singleton handler
    mock_new.assert_called_once()

    # 2. configure was called
    mock_handler_instance.configure.assert_awaited_once()

    # 3. get was called with the correct URL
    mock_handler_instance.get.assert_awaited_once_with(expected_url)

    # 4. BeautifulSoup was called with the correct HTML
    mock_bs.assert_called_once_with(fake_html, 'html.parser')

    # 5. structure was set properly
    assert scraper._structure == mock_soup_instance

@pytest.mark.asyncio
async def test_get_club_urls_return_expected_value(clubs_page_html):
    expected_value = [
        ('club_name', 'club_page_url'),
        ('Arsenal', 'https://www.premierleague.com/clubs/1/Arsenal/overview'),
        ('Aston Villa', 'https://www.premierleague.com/clubs/2/Aston-Villa/overview')
    ]

    scraper = ClubUrlsScraper()
    scraper._structure = BeautifulSoup(clubs_page_html, 'html.parser')

    result = await scraper.get_club_urls()

    assert result == expected_value