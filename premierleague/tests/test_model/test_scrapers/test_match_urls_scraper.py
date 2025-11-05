import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from premierleague.model.scrapers.match_urls_scraper import MatchUrlsScraper, async_playwright, PlaywrightRequestHandler

def test_init_set_state():
    def parent_initializer_side_effect(self):
        self._website_url = 'https://www.premierleague.com'

    with patch('premierleague.model.scrapers.match_urls_scraper.PremierleagueWebsiteScraper.__init__', side_effect=parent_initializer_side_effect) as parent_mock:
        scraper_without_url = MatchUrlsScraper()
        
        # assert if parent's initializer was called
        parent_mock.assert_called_once()

        # check current state 
        assert scraper_without_url._base_url == 'https://www.premierleague.com/matchweek/18390/blog?match=true'
        assert scraper_without_url._initialized == False

        matches_page_custom_url = 'https://www.premierleague.com/matchweek'
        
        scraper_with_url = MatchUrlsScraper(matches_page_custom_url)

        # check current state if pass custom url
        assert scraper_with_url._base_url == matches_page_custom_url
        assert scraper_without_url._initialized == False


@pytest.mark.asyncio
@patch('premierleague.model.scrapers.match_urls_scraper.PlaywrightRequestHandler.__new__')
async def test_initilizer_sets_state(mock_handler_cls):
    mock_handler_obj = MagicMock(spec=PlaywrightRequestHandler)
    mock_handler_obj.configure = AsyncMock(return_value=None)
    mock_handler_cls.return_value = mock_handler_obj

    scraper = MatchUrlsScraper()
    await scraper.initialize()

    mock_handler_cls.assert_called_once()
    mock_handler_obj.configure.assert_awaited_once()

    assert scraper._request_handler == mock_handler_obj
    assert scraper._initialized == True


async def goto_side_effect(page, url):
    await page.goto(url)


@pytest.mark.asyncio
@patch('premierleague.model.scrapers.match_urls_scraper.PlaywrightRequestHandler.__new__')
async def test_get_week_page_urls(mock_handler_cls):
    expected_result =[
        "https://www.premierleague.com/matchweek/18390/blog?match=true",
        "https://www.premierleague.com/matchweek/18391/blog?match=true",
        "https://www.premierleague.com/matchweek/18392/blog?match=true",
        "https://www.premierleague.com/matchweek/18393/blog?match=true",
        "https://www.premierleague.com/matchweek/18394/blog?match=true",
        "https://www.premierleague.com/matchweek/18395/blog?match=true",
        "https://www.premierleague.com/matchweek/18396/blog?match=true",
        "https://www.premierleague.com/matchweek/18397/blog?match=true",
        "https://www.premierleague.com/matchweek/18398/blog?match=true",
        "https://www.premierleague.com/matchweek/18399/blog?match=true",
        "https://www.premierleague.com/matchweek/18400/blog?match=true",
        "https://www.premierleague.com/matchweek/18401/blog?match=true",
        "https://www.premierleague.com/matchweek/18402/blog?match=true",
        "https://www.premierleague.com/matchweek/18403/blog?match=true",
        "https://www.premierleague.com/matchweek/18404/blog?match=true",
        "https://www.premierleague.com/matchweek/18405/blog?match=true",
        "https://www.premierleague.com/matchweek/18406/blog?match=true",
        "https://www.premierleague.com/matchweek/18407/blog?match=true",
        "https://www.premierleague.com/matchweek/18408/blog?match=true",
        "https://www.premierleague.com/matchweek/18409/blog?match=true",
        "https://www.premierleague.com/matchweek/18410/blog?match=true",
        "https://www.premierleague.com/matchweek/18411/blog?match=true",
        "https://www.premierleague.com/matchweek/18412/blog?match=true",
        "https://www.premierleague.com/matchweek/18413/blog?match=true",
        "https://www.premierleague.com/matchweek/18414/blog?match=true",
        "https://www.premierleague.com/matchweek/18415/blog?match=true",
        "https://www.premierleague.com/matchweek/18416/blog?match=true",
        "https://www.premierleague.com/matchweek/18417/blog?match=true",
        "https://www.premierleague.com/matchweek/18418/blog?match=true",
        "https://www.premierleague.com/matchweek/18419/blog?match=true",
        "https://www.premierleague.com/matchweek/18420/blog?match=true",
        "https://www.premierleague.com/matchweek/18421/blog?match=true",
        "https://www.premierleague.com/matchweek/18422/blog?match=true",
        "https://www.premierleague.com/matchweek/18423/blog?match=true",
        "https://www.premierleague.com/matchweek/18424/blog?match=true",
        "https://www.premierleague.com/matchweek/18425/blog?match=true",
        "https://www.premierleague.com/matchweek/18426/blog?match=true",
        "https://www.premierleague.com/matchweek/18427/blog?match=true"
]
    
    scraper = MatchUrlsScraper()
    mock_handler_obj = MagicMock(spec=PlaywrightRequestHandler)
    mock_handler_obj.goto = AsyncMock(side_effect=goto_side_effect)
    mock_handler_cls.return_value = mock_handler_obj
    scraper._request_handler = mock_handler_obj
    
    async with async_playwright() as p:
        async with await p.chromium.launch(headless=True) as browser:
            week_page_urls = await scraper._get_week_page_urls(browser)
    
    # mock_handler_obj.goto.assert_awaited_once_with(scraper._base_url)
    assert week_page_urls == expected_result


@pytest.mark.asyncio
@patch('premierleague.model.scrapers.match_urls_scraper.PlaywrightRequestHandler.__new__')
async def test_get_week_match_urls(mock_handler_cls):
    expected_result = {
        'round': 1,
        'urls': set(
            ['https://www.premierleague.com/match/115827',
            'https://www.premierleague.com/match/115830',
            'https://www.premierleague.com/match/115828',
            'https://www.premierleague.com/match/115829',
            'https://www.premierleague.com/match/115831',
            'https://www.premierleague.com/match/115832',
            'https://www.premierleague.com/match/115833',
            'https://www.premierleague.com/match/115834',
            'https://www.premierleague.com/match/115835',
            'https://www.premierleague.com/match/115836']
        )
    }

    scraper = MatchUrlsScraper()
    mock_handler_obj = MagicMock(spec=PlaywrightRequestHandler)
    mock_handler_obj.goto = AsyncMock(side_effect=goto_side_effect)
    mock_handler_cls.return_value = mock_handler_obj
    scraper._request_handler = mock_handler_obj
    
    async with async_playwright() as p:
        async with await p.chromium.launch(headless=True) as browser:
            result = await scraper._get_week_match_urls(browser, 'https://www.premierleague.com/matchweek/18390/blog?match=true')
    
    assert result == expected_result


@pytest.mark.asyncio
@patch("premierleague.model.scrapers.match_urls_scraper.async_playwright")
async def test_get_match_urls_builds_correct_result(mock_async_playwright):
    # Mock browser setup
    mock_playwright_context = AsyncMock()
    mock_browser = AsyncMock()
    mock_playwright_context.chromium.launch.return_value = mock_browser
    mock_async_playwright.return_value.__aenter__.return_value = mock_playwright_context

    # Setup MatchUrlsScraper instance
    scraper = MatchUrlsScraper("http://example.com")
    scraper._initialized = True

    # Mock internal methods
    scraper._get_week_page_urls = AsyncMock(return_value=["/week/1", "/week/2"])

    # Mock function that behaves based on input arguments
    async def mock_get_week_match_urls(browser, url):
        if url == "/week/1":
            return {"round": 1, "urls": ["/match/1a", "/match/1b"]}
        elif url == "/week/2":
            return {"round": 2, "urls": ["/match/2a", "/match/2b"]}
        else:
            return {"round": None, "urls": []}

    # Assign it to the mock
    scraper._get_week_match_urls = AsyncMock(side_effect=mock_get_week_match_urls)

    # Run method
    result = await scraper.get_match_urls()

    # Assert expected result
    expected = {
        1: ["/match/1a", "/match/1b"],
        2: ["/match/2a", "/match/2b"],
    }
    assert result == expected

    # Verify internal methods were called correctly
    scraper._get_week_page_urls.assert_awaited_once_with(mock_browser)
    assert scraper._get_week_match_urls.await_count == 2
    scraper._get_week_match_urls.assert_any_await(mock_browser, "/week/1")
    scraper._get_week_match_urls.assert_any_await(mock_browser, "/week/2")

    # Browser was closed
    mock_browser.close.assert_awaited_once()
