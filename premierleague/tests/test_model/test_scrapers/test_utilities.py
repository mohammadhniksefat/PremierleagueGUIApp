import pytest
from premierleague.model.scrapers.utils import UrlValidator  # replace with actual import

@pytest.mark.parametrize("url", [
    "https://www.premierleague.com/clubs/1/Arsenal/squad?se=719",
    "https://www.premierleague.com/clubs/34/Fulham/squad?se=719"
])
def test_validate_squad_page_url_valid(url):
    assert UrlValidator.validate_squad_page_url(url) is True

@pytest.mark.parametrize("url", [
    "https://www.premierleague.com/clubs/1/Arsenal/overview",
    "https://www.premierleague.com/clubs/34/Fulham/overview"
])
def test_validate_club_page_url_valid(url):
    assert UrlValidator.validate_club_page_url(url) is True

@pytest.mark.parametrize("url", [
    "https://www.premierleague.com/match/116192",
    "https://www.premierleague.com/match/116187"
])
def test_validate_match_page_url_valid(url):
    assert UrlValidator.validate_match_page_url(url) is True

@pytest.mark.parametrize("url", [
    "https://www.premierleague.com/players/7975/David-Raya/overview",
    "https://www.premierleague.com/players/15202/Declan-Rice/overview"
])
def test_validate_player_page_url_valid(url):
    assert UrlValidator.validate_player_page_url(url) is True

@pytest.mark.parametrize("url", [
    "https://www.premierleague.com/clubs/1/Arsenal/squad",            # missing ?se=
    "https://www.premierleague.com/clubs/Arsenal/1/squad?se=719",    # wrong order
    "http://www.premierleague.com/clubs/1/Arsenal/squad?se=719",     # http instead of https
    "https://www.premierleague.com/clubs/1/Arsenal/overviewX",       # extra char
    "https://www.premierleague.com/match/abc123",                    # non-digit match id
    "https://www.premierleague.com/players/7975/David-Raya",         # missing /overview
    "https://www.premierleague.com/players/abc/David-Raya/overview"  # non-digit player id
])
def test_url_validator_invalid(url):
    assert not any([
        UrlValidator.validate_squad_page_url(url),
        UrlValidator.validate_club_page_url(url),
        UrlValidator.validate_match_page_url(url),
        UrlValidator.validate_player_page_url(url)
    ])
