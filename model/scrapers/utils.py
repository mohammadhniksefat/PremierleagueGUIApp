import re

class UrlValidator:
    @staticmethod
    def validate_squad_page_url(url: str) -> bool:
        pattern = r"^https:\/\/www\.premierleague\.com\/clubs\/\d+\/[A-Za-z\-]+\/squad\?se=\d+$"
        return bool(re.match(pattern, url))

    @staticmethod
    def validate_club_page_url(url: str) -> bool:
        pattern = r"^https:\/\/www\.premierleague\.com\/clubs\/\d+\/[A-Za-z\-]+\/overview$"
        return bool(re.match(pattern, url))

    @staticmethod
    def validate_match_page_url(url: str) -> bool:
        pattern = r"^https:\/\/www\.premierleague\.com\/match\/\d+$"
        return bool(re.match(pattern, url))

    @staticmethod
    def validate_player_page_url(url: str) -> bool:
        pattern = r"^https:\/\/www\.premierleague\.com\/players\/\d+\/[^\/]+\/overview$"
        return bool(re.match(pattern, url))