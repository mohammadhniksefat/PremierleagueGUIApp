import pytest
from bs4 import BeautifulSoup
from unittest.mock import patch, AsyncMock, MagicMock
from tests.utils import load_fixture
from model.scrapers.club_data_scraper import ClubDataScraper
from model.scrapers.request_handler import RequestHandler

@pytest.fixture
def main_page_html():
    return load_fixture('club_main_page.html')

@pytest.fixture
def directory_page_html_1():
    return load_fixture('club_directory_page_1.html')

@pytest.fixture
def directory_page_html_2():
    return load_fixture('club_directory_page_2.html')

@pytest.fixture
def directory_page_html_3():
    return load_fixture('club_directory_page_3.html')

@pytest.mark.asyncio
async def test_initialize_sets_correct_state_and_mocks_side_effects():
    # Arrange
    fake_url = "https://www.premierleague.com/clubs/1/FakeFC/overview"
    main_page_html = '<html><body><h2 class="club-header__team-name">Fake Club</h2></body></html>'
    directory_page_html = '<html><body><span>Manager</span></body></html>'

    with patch("model.scrapers.utils.UrlValidator.validate_club_page_url", return_value=True):
        scraper = ClubDataScraper(fake_url)

        handler = RequestHandler()  # Get the real singleton instance

        with patch.object(handler, "configure", new_callable=AsyncMock) as mock_configure, \
             patch.object(handler, "get", new_callable=AsyncMock) as mock_get:

            # Set mock return values
            mock_get.side_effect = [main_page_html, directory_page_html]

            # Act
            await scraper.initialize()

            # Assert - side effects
            mock_configure.assert_awaited_once()
            assert mock_get.await_count == 2, "Expected two requests (main and directory page) but got a different count"

            # Assert - correct URLs used in get calls
            expected_main_url = fake_url
            expected_directory_url = fake_url.replace("overview", "directory")
            mock_get.assert_any_await(expected_main_url)
            mock_get.assert_any_await(expected_directory_url)

            # Assert - state changes
            assert scraper._initialized is True, "Scraper should be initialized after calling initialize()"
            assert isinstance(scraper._structures, dict), "Structures should be a dictionary"
            assert 'main_page' in scraper._structures, "'main_page' key missing in structures"
            assert 'directory_page' in scraper._structures, "'directory_page' key missing in structures"
            assert isinstance(scraper._structures['main_page'], BeautifulSoup), "main_page structure should be a BeautifulSoup object"
            assert isinstance(scraper._structures['directory_page'], BeautifulSoup), "directory_page structure should be a BeautifulSoup object"

            # Confirm correct HTML structure parsing (reverse-loaded for testing)
            assert scraper._structures['main_page'].select_one('span').text == 'Manager', "Expected 'Manager' in main_page span"
            assert scraper._structures['directory_page'].select_one('h2').text == 'Fake Club', "Expected 'Fake Club' in directory_page h2"


@pytest.mark.asyncio
async def test_get_all_data_calls_all_methods_and_returns_data():
    fake_url = "https://www.premierleague.com/clubs/1/FakeFC/overview"
    with patch("model.scrapers.utils.UrlValidator.validate_club_page_url", return_value=True):
        scraper = ClubDataScraper(fake_url)
        scraper._initialized = True  # manually set initialized

        with patch.multiple(
            scraper,
            get_club_name=AsyncMock(return_value="Fake FC"),
            get_establishment_year=AsyncMock(return_value="1892"),
            get_manager_name=AsyncMock(return_value="John Doe"),
            get_city_name=AsyncMock(return_value="Fake City"),
            get_stadium_name=AsyncMock(return_value="Fake Stadium"),
            get_club_logo=AsyncMock(return_value=b"fake-bytes"),
            get_squad_page_url=AsyncMock(return_value="https://example.com/squad")
        ) as mocks:
            data = await scraper.get_all_data()

            for method in mocks.values():
                method.assert_awaited_once()

            assert data == {
                'club_name': "Fake FC",
                'establishment_year': "1892",
                'manager_name': "John Doe",
                'city': "Fake City",
                'stadium': "Fake Stadium",
                'logo': b"fake-bytes",
                'squad_page_url': "https://example.com/squad"
            }, "Returned data dictionary doesn't match expected values"

@pytest.mark.asyncio
@pytest.mark.parametrize("method_name", [
    "get_all_data",
    "get_club_name",
    "get_establishment_year",
    "get_manager_name",
    "get_city_name",
    "get_stadium_name",
    "get_club_logo",
    "get_squad_page_url",
])
async def test_all_get_methods_raise_if_not_initialized(method_name):
    with patch("model.scrapers.utils.UrlValidator.validate_club_page_url", return_value=True):
        scraper = ClubDataScraper("https://www.premierleague.com/clubs/1/FakeFC/overview")

        method = getattr(scraper, method_name)

        with pytest.raises(RuntimeError, match='scraper'):
            await method()

@pytest.mark.parametrize("method_name, cache_key, expected_value", [
    ("get_club_name", "club_name", "Cached Club"),
    ("get_establishment_year", "establishment_year", "1990"),
    ("get_manager_name", "manager_name", "Cached Manager"),
    ("get_city_name", "city", "Cached City"),
    ("get_stadium_name", "stadium", "Cached Stadium"),
    ("get_club_logo", "logo", b"cached-logo-bytes"),
    ("get_squad_page_url", "squad_page_url", "https://example.com/squad"),
])
@pytest.mark.asyncio
async def test_get_methods_return_cached_value(method_name, cache_key, expected_value):
    scraper = ClubDataScraper("https://www.premierleague.com/clubs/1/FakeFC/overview")
    scraper._initialized = True
    scraper.club_data[cache_key] = expected_value

    method = getattr(scraper, method_name)
    result = await method()

    assert result == expected_value, f"Expected cached value '{expected_value}' for {method_name}, got '{result}'"

def setup_scraper_with_html(html: str, page: str = "main_page"):
    with patch('model.scrapers.utils.UrlValidator.validate_club_page_url', return_value=True):
        scraper = ClubDataScraper("https://...")
        scraper._initialized = True
        scraper._structures = {page: BeautifulSoup(html, "html.parser")}
        return scraper

@pytest.mark.asyncio
async def test_get_club_name_returns_expected_value(main_page_html):
    scraper = setup_scraper_with_html(main_page_html, page="main_page")
    club_name = await scraper.get_club_name()
    assert club_name == "Arsenal", f"Expected club name 'Arsenal', got '{club_name}'"

    assert scraper.club_data.get("club_name") == 'Arsenal', "club name were not cached correctly in club_data"

@pytest.mark.asyncio
async def test_get_establishment_year_returnes_expected_value(main_page_html):
    scraper = setup_scraper_with_html(main_page_html)
    establishment_year = await scraper.get_establishment_year()
    assert establishment_year == '1886', f"Expected '1886', got '{establishment_year}'"

    assert scraper.club_data.get("establishment_year") == '1886', "establishment year name were not cached correctly in club_data"

@pytest.mark.parametrize(('fixture_name', 'expected_manager_name'),  [
    ('directory_page_html_1', 'First-team Manager'),
    ('directory_page_html_2', 'Head Coach'),
    ('directory_page_html_3', 'Manager')
])
@pytest.mark.asyncio
async def test_get_manager_name_returns_expected_value(request, fixture_name, expected_manager_name):
    directory_page_html = request.getfixturevalue(fixture_name)
    scraper = setup_scraper_with_html(directory_page_html, page="directory_page")
    manager_name = await scraper.get_manager_name()
    assert manager_name == expected_manager_name, f"Expected manager name {expected_manager_name}, got '{manager_name}'"

    assert scraper.club_data.get("manager_name") == expected_manager_name, "manager name were not cached correctly in club_data"

@pytest.mark.asyncio
async def test_get_city_name_returns_expected_value(main_page_html):
    scraper = setup_scraper_with_html(main_page_html)
    city_name = await scraper.get_city_name()
    assert city_name == "London", f"Expected city name 'London', got '{city_name}'"

    assert scraper.club_data.get("city") == 'London', "city name were not cached correctly in club_data"

@pytest.mark.asyncio
async def test_get_stadium_name_returns_expected_value(main_page_html):
    scraper = setup_scraper_with_html(main_page_html)
    stadium_name = await scraper.get_stadium_name()
    assert stadium_name == "Emirates Stadium", f"Expected stadium name 'Emirates Stadium', got '{stadium_name}'"

    assert scraper.club_data.get("stadium") == 'Emirates Stadium', "stadium name were not cached correctly in club_data"

@pytest.mark.asyncio
async def test_get_club_squad_page_url_returns_expected_value(main_page_html):
    scraper = setup_scraper_with_html(main_page_html)
    scraper._base_url = "https://www.premierleague.com/clubs/1/FakeFC/overview"

    squad_url = await scraper.get_squad_page_url()
    expected_url = "https://www.premierleague.com/clubs/1/FakeFC/squad?se=719"
    assert squad_url == expected_url, f"Expected squad page URL '{expected_url}', got '{squad_url}'"

    assert scraper.club_data.get("squad_page_url") == expected_url, "squad page url were not cached correctly in club_data"

@pytest.mark.asyncio
async def test_get_club_logo_returns_image_bytes(main_page_html):
    # Arrange
    scraper = setup_scraper_with_html(main_page_html)

    # Inject mocked request handler
    fake_bytes = b"fake-image-bytes"

    handler = RequestHandler()  # Get the real singleton instance

    with patch.object(handler, "get", new_callable=AsyncMock) as mock_get:

        mock_get.return_value.content = fake_bytes
        scraper._request_handler = handler

        # Act
        result = await scraper.get_club_logo()

        # Assert
        assert result == fake_bytes, f"Expected logo bytes {fake_bytes}, but got {result}"
        mock_get.assert_awaited_once_with('https://resources.premierleague.com/premierleague/badges/t3.png'), "Expected one call to request_handler.get() with the 'https://resources.premierleague.com/premierleague/badges/t3.png' url for logo"

        assert scraper.club_data.get("logo") == fake_bytes, "Logo bytes were not cached correctly in club_data"
