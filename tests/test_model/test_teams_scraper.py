import pytest
from model.scraper import TeamsDataScraper

def test_extract_all_teams_data(mocker):

    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.text = text

    mocker.patch("Session.get", return_value=mock_response)

    expected_result = {
            "url":"https://www.premierleague.com/clubs/1/Arsenal/overview",
            "club_name":"Arsenal",
            "stablishment_year":1886,
            "manager": "Mikel Arteta",
            "city": "London",
            "stadium": "Emirates Stadium",
            "capacity": 60704
        }
    
    scraper = TeamsDataScraper()
    result = scraper.extract_all_teams_data()

    # Session.get.assert_called_once_with("https://www.premierleague.com/clubs")

    assert result["url"] == expected_result["url"]
    assert result["club_name"] == expected_result["club_name"]
    assert result["stablishment_year"] == expected_result["stablishment_year"]
    assert result["manager"] == expected_result["manager"]
    assert result["city"] == expected_result["city"]
    assert result["stadium"] == expected_result["stadium"]
    assert result["capacity"] == expected_result["capacity"]

    assert result["logo"] is not None, "Logo was not downloaded successfully."
    assert len(result["logo"]) > 0, "Downloaded logo is empty."
    assert result["logo"][:4] == b'\x89PNG', "Downloaded file is not a PNG image."




