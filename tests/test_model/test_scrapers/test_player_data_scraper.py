import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from bs4 import BeautifulSoup
from model.scrapers.player_data_scraper import PlayerDataScraper
from tests.utils import load_fixture

@pytest.fixture
def player_page():
    return load_fixture('player_page.html')

@patch('model.scrapers.player_data_scraper.UrlValidator')
def test_init_sets_up_state_correctly(mock_validator):
    mock_validator.validate_player_page_url.return_value = True
    scraper = PlayerDataScraper("https://valid.com/player")

    assert scraper._base_url == "https://valid.com/player"
    assert scraper._initialized is False
    assert isinstance(scraper.player_data, dict)

    expected_keys = [
        'firstname', 'lastname', 'club_name', 'position', 'nationality',
        'date_of_birth', 'shirt_number', 'age', 'height', 'picture'
    ]
    for key in expected_keys:
        assert key in scraper.player_data

@patch('model.scrapers.player_data_scraper.UrlValidator')
def test_invalid_url_raises_exception(mock_validator):
    mock_validator.validate_player_page_url.return_value = False
    with pytest.raises(ValueError):
        PlayerDataScraper("invalid_url")

@pytest.mark.asyncio
@patch('model.scrapers.player_data_scraper.BeautifulSoup')
@patch('model.scrapers.player_data_scraper.RequestHandler.__new__')
@patch('model.scrapers.player_data_scraper.UrlValidator')
async def test_initialize_sets_up_scraper(mock_validator, mock_request_handler_cls, mock_beautifulsoup):
    # Mock URL validation
    mock_validator.validate_player_page_url.return_value = True

    # Setup mock RequestHandler
    mock_handler = AsyncMock()
    fake_html = "<html><div class='player-header__name-first'>John</div></html>"
    mock_handler.get.return_value = fake_html
    mock_request_handler_cls.return_value = mock_handler

    # Setup mock BeautifulSoup
    mock_soup_instance = MagicMock(spec=BeautifulSoup)
    mock_beautifulsoup.return_value = mock_soup_instance

    # Create and initialize the scraper
    scraper = PlayerDataScraper("https://valid-url.com/player")
    await scraper.initialize()

    # Assertions
    mock_validator.validate_player_page_url.assert_called_once_with("https://valid-url.com/player")
    mock_request_handler_cls.assert_called_once()
    mock_handler.configure.assert_awaited_once()
    mock_handler.get.assert_awaited_once_with("https://valid-url.com/player")
    mock_beautifulsoup.assert_called_once_with(fake_html, 'html.parser')

    assert scraper._initialized is True
    assert 'main' in scraper._structures
    assert scraper._structures['main'] is mock_soup_instance


@pytest.mark.asyncio
@pytest.mark.parametrize("method_name", [
    "get_all_data",
    "get_firstname",
    "get_lastname",
    "get_club_name",
    "get_position",
    "get_nationality",
    "get_shirt_number",
    "get_date_of_birth",
    "get_age",
    "get_height",
    "get_picture"
])
async def test_get_methods_raise_if_not_initialized(method_name):
    with patch('model.scrapers.player_data_scraper.UrlValidator.validate_player_page_url', return_value=True):
        # Arrange
        scraper = PlayerDataScraper("https://valid.com/player")
        
        # Act
        method = getattr(scraper, method_name)

        # Assert
        with pytest.raises(RuntimeError, match="scraper doesn't initialized yet"):
            await method()

@pytest.mark.asyncio
@patch.multiple(
    PlayerDataScraper,
    get_firstname=AsyncMock(return_value="John"),
    get_lastname=AsyncMock(return_value="Doe"),
    get_club_name=AsyncMock(return_value="Awesome FC"),
    get_position=AsyncMock(return_value="Midfielder"),
    get_nationality=AsyncMock(return_value="England"),
    get_shirt_number=AsyncMock(return_value="10"),
    get_date_of_birth=AsyncMock(return_value="1995-08-20"),
    get_age=AsyncMock(return_value=29),
    get_height=AsyncMock(return_value=180),
    get_picture=AsyncMock(return_value=b"binarydata")
)
async def test_get_all_data_returns_and_caches_values(**mocked_methods):
    with patch('model.scrapers.player_data_scraper.UrlValidator.validate_player_page_url', return_value=True):
        scraper = PlayerDataScraper("https://valid-url.com/player")
        scraper._initialized = True  # Bypass initialization requirement

        result = await scraper.get_all_data()

        expected = {
            'firstname': "John",
            'lastname': "Doe",
            'club_name': "Awesome FC",
            'position': "Midfielder",
            'nationality': "England",
            'shirt_number': "10",
            'date_of_birth': "1995-08-20",
            'age': 29,
            'height': 180,
            'picture': b"binarydata"
        }

        assert result == expected
        assert scraper.player_data == expected

        for _, method in mocked_methods.items():
            method.assert_awaited_once()

import pytest
from model.scrapers.player_data_scraper import PlayerDataScraper

@pytest.mark.asyncio
@pytest.mark.parametrize("key, method_name, fake_value", [
    ("firstname", "get_firstname", "John"),
    ("lastname", "get_lastname", "Doe"),
    ("club_name", "get_club_name", "Awesome FC"),
    ("position", "get_position", "Midfielder"),
    ("nationality", "get_nationality", "England"),
    ("shirt_number", "get_shirt_number", "10"),
    ("date_of_birth", "get_date_of_birth", "1995-08-20"),
    ("age", "get_age", 29),
    ("height", "get_height", 180),
    ("picture", "get_picture", b"fakebinarydata"),
])
async def test_get_methods_return_cached_value(key, method_name, fake_value):
    with patch('model.scrapers.player_data_scraper.UrlValidator.validate_player_page_url', return_value=True):
        scraper = PlayerDataScraper("https://valid.com/player")
        scraper._initialized = True
        scraper.player_data[key] = fake_value  # Pre-cache the value

        method = getattr(scraper, method_name)
        result = await method()

        assert result == fake_value

def setup_scraper(player_page_html):
    scraper = PlayerDataScraper("https://valid.com/player")
    scraper._initialized = True
    scraper._structures = {
        'main': BeautifulSoup(player_page_html, 'html.parser'),
    }
    return scraper

@pytest.mark.asyncio
async def test_get_firstname(player_page):
    with patch('model.scrapers.player_data_scraper.UrlValidator.validate_player_page_url', return_value=True):
        scraper = setup_scraper(player_page)

        firstname = await scraper.get_firstname()
        assert firstname == "Declan"
        assert scraper.player_data['firstname'] == "Declan"


@pytest.mark.asyncio
async def test_get_lastname(player_page):
    with patch('model.scrapers.player_data_scraper.UrlValidator.validate_player_page_url', return_value=True):
        scraper = setup_scraper(player_page)

        lastname = await scraper.get_lastname()
        assert lastname == "Rice"
        assert scraper.player_data['lastname'] == "Rice"


@pytest.mark.asyncio
async def test_get_club_name(player_page):
    with patch('model.scrapers.player_data_scraper.UrlValidator.validate_player_page_url', return_value=True):
        scraper = setup_scraper(player_page)

        club_name = await scraper.get_club_name()
        assert club_name == "Arsenal"
        assert scraper.player_data['club_name'] == "Arsenal"


@pytest.mark.asyncio
async def test_get_position(player_page):
    with patch('model.scrapers.player_data_scraper.UrlValidator.validate_player_page_url', return_value=True):
        scraper = setup_scraper(player_page)

        position = await scraper.get_position()
        assert position == "Midfielder"
        assert scraper.player_data['position'] == "Midfielder"


@pytest.mark.asyncio
async def test_get_nationality(player_page):
    with patch('model.scrapers.player_data_scraper.UrlValidator.validate_player_page_url', return_value=True):
        scraper = setup_scraper(player_page)

        nationality = await scraper.get_nationality()
        assert nationality == "England"
        assert scraper.player_data['nationality'] == "England"


@pytest.mark.asyncio
async def test_get_shirt_number(player_page):
    with patch('model.scrapers.player_data_scraper.UrlValidator.validate_player_page_url', return_value=True):
        scraper = setup_scraper(player_page)

        shirt_number = await scraper.get_shirt_number()
        assert shirt_number == "41"
        assert scraper.player_data['shirt_number'] == "41"


@pytest.mark.asyncio
async def test_get_date_of_birth(player_page):
    with patch('model.scrapers.player_data_scraper.UrlValidator.validate_player_page_url', return_value=True):
        scraper = setup_scraper(player_page)

        dob = await scraper.get_date_of_birth()
        assert dob == "14/01/1999"
        assert scraper.player_data['date_of_birth'] == "14/01/1999"


@pytest.mark.asyncio
async def test_get_age(player_page):
    with patch('model.scrapers.player_data_scraper.UrlValidator.validate_player_page_url', return_value=True):
        scraper = setup_scraper(player_page)

        age = await scraper.get_age()
        assert age == 26
        assert scraper.player_data['age'] == 26


@pytest.mark.asyncio
async def test_get_height(player_page):
    with patch('model.scrapers.player_data_scraper.UrlValidator.validate_player_page_url', return_value=True):
        scraper = setup_scraper(player_page)

        height = await scraper.get_height()
        assert height == 188
        assert scraper.player_data['height'] == 188


@pytest.mark.asyncio
@patch('model.scrapers.player_data_scraper.RequestHandler.__new__')
async def test_get_picture(mock_request_handler, player_page):
    with patch('model.scrapers.player_data_scraper.UrlValidator.validate_player_page_url', return_value=True):
        mock_handler_instance = AsyncMock()
        mock_handler_instance.get.return_value = b"fakebytes"
        mock_request_handler.return_value = mock_handler_instance

        scraper = setup_scraper(player_page)
        scraper._request_handler = mock_handler_instance

        picture = await scraper.get_picture()
        assert picture == b"fakebytes"
        assert scraper.player_data['picture'] == b"fakebytes"
        mock_handler_instance.get.assert_awaited_once_with(url="https://resources.premierleague.com/premierleague/photos/players/250x250/p204480.png", raw=True)