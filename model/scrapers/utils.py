import re, requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter


class Utils:
    def create_session_dec(func):
        def new_func(*args, **kwargs):

            session = requests.Session()
            retry = Retry(connect=3, backoff_factor=0.5)
            adapter = HTTPAdapter(max_retries=retry)
            session.mount('https://', adapter)
            session.mount('http://', adapter)

            func(session, *args, **kwargs)

        return new_func
    
    def create_session():
        session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('https://', adapter)
        session.mount('http://', adapter)



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