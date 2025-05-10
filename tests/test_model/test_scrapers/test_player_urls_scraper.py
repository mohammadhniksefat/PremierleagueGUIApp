# tests/test_player_urls_scraper.py
import pytest
from unittest.mock import patch, AsyncMock, Mock, MagicMock
from bs4 import BeautifulSoup
from model.scrapers.player_urls_scraper import PlayerUrlsScraper
from tests.utils import load_fixture

@pytest.fixture
def club_page():
    return load_fixture('club_main_page.html')

@pytest.mark.asyncio
@patch('model.scrapers.player_urls_scraper.UrlValidator.validate_squad_page_url', return_value=True)
@patch('model.scrapers.player_urls_scraper.BeautifulSoup')
@patch('model.scrapers.player_urls_scraper.RequestHandler')
async def test_initialize_behavior(mock_request_handler_class, mock_bs_constructor, mock_validate_url):
    HTML_WITH_PLAYERS = '''
    <ul>
    <li class="stats-card" data-widget="featured-player">
        <a class="stats-card__wrapper" href="/players/12345/player-name/overview">
        <span class="stats-card__player-first">John</span>
        <span class="stats-card__player-last">Doe</span>
        </a>
    </li>
    </ul>
    '''
        
    # Mock the BeautifulSoup return value
    mock_soup = Mock(spec=BeautifulSoup)
    mock_bs_constructor.return_value = mock_soup

    # Mock the RequestHandler and its methods
    mock_request_handler = AsyncMock()
    mock_request_handler.get.return_value = HTML_WITH_PLAYERS
    mock_request_handler_class.return_value = mock_request_handler

    url = "https://some.club/squad"
    scraper = PlayerUrlsScraper(url=url)
    await scraper.initialize()

    # Assertions
    mock_validate_url.assert_called_once_with(url)
    mock_request_handler.configure.assert_awaited_once()
    mock_request_handler.get.assert_awaited_once_with(url)
    mock_bs_constructor.assert_called_once_with(HTML_WITH_PLAYERS, 'html.parser')
    assert scraper._initialized is True
    assert scraper.structure == mock_soup
    assert scraper._request_handler is mock_request_handler



@pytest.mark.asyncio
async def test_get_club_player_urls():
    # Sample HTML with multiple player cards
    html = '''
    <ul>
      <li class="stats-card" data-widget="featured-player">
        <a class="stats-card__wrapper" href="/players/1111/john-doe/overview">
          <span class="stats-card__player-first">John</span>
          <span class="stats-card__player-last">Doe</span>
        </a>
      </li>
      <li class="stats-card" data-widget="featured-player">
        <a class="stats-card__wrapper" href="/players/2222/jane-smith/overview">
          <span class="stats-card__player-first">Jane</span>
          <span class="stats-card__player-last">Smith</span>
        </a>
      </li>
    </ul>
    '''

    # Setup scraper manually (skipping full async init)
    scraper = PlayerUrlsScraper()
    scraper._initialized = True
    scraper._website_url = "https://www.premierleague.com"
    scraper.structure = BeautifulSoup(html, 'html.parser')

    expected_result = {
        "JohnDoe": "https://www.premierleague.com/players/1111/john-doe/overview",
        "JaneSmith": "https://www.premierleague.com/players/2222/jane-smith/overview"
    }

    result = await scraper.get_club_player_urls()

    assert result == expected_result

@pytest.mark.asyncio
async def test_raise_if_not_initialized_raises_error():
    scraper = PlayerUrlsScraper()
    scraper._initialized = False

    with pytest.raises(RuntimeError, match="scraper doesn't initialized yet"):
        await scraper.get_club_player_urls()

@pytest.mark.asyncio
async def test_raise_if_not_initialized_passes_when_initialized():
    scraper = PlayerUrlsScraper()
    scraper._initialized = True
    scraper.structure = None  # It won’t reach structure parsing because the test just checks initialization
    
    try:
        await scraper.get_club_player_urls()  # Should raise AttributeError due to structure=None, but NOT RuntimeError
    except AttributeError:
        pass  # We only care that RuntimeError was not raised

@pytest.mark.asyncio
async def test_scrap_squad_page_url_with_club_page_url(club_page):
    scraper = PlayerUrlsScraper()
    mock_handler = MagicMock()
    scraper._request_handler = mock_handler

    mock_handler.get = AsyncMock(return_value=club_page)

    club_page_url = "https://www.premierleague.com/clubs/1/Arsenal/overview"
    result = await scraper._scrap_squad_page_url(club_page_url=club_page_url)

    expected_url = "https://www.premierleague.com/clubs/1/Arsenal/squad?se=719"
    assert result == expected_url


@pytest.mark.asyncio
async def test_scrap_squad_page_url_with_club_name(club_page):
    scraper = PlayerUrlsScraper()
    mock_handler = MagicMock()
    mock_handler.get = AsyncMock(return_value=club_page)
    scraper._request_handler = mock_handler

    club_name = "Arsenal"
    club_page_url = "https://www.premierleague.com/clubs/1/Arsenal/overview"
    expected_url = "https://www.premierleague.com/clubs/1/Arsenal/squad?se=719"

    with patch("model.scrapers.player_urls_scraper.ClubUrlsScraper") as MockScraper:
        mock_scraper_instance = MockScraper.return_value
        mock_scraper_instance.initialize = AsyncMock()
        mock_scraper_instance.get_club_urls.return_value = {club_name: club_page_url}

        result = await scraper._scrap_squad_page_url(club_name=club_name)
        assert result == expected_url
