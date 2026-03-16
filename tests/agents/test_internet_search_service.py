from core.services.web_search.internet_search_service import InternetSearchService


def test_decode_duckduckgo_redirect_url():
    raw = "//duckduckgo.com/l/?uddg=https%3A%2F%2Fwww.who.int%2Fnews-room"
    decoded = InternetSearchService._decode_result_url(raw)
    assert decoded == "https://www.who.int/news-room"


def test_clean_html_text():
    value = "<div>Hello <b>world</b>&nbsp;from <a>EDQM</a></div>"
    assert InternetSearchService._clean_html_text(value) == "Hello world from EDQM"
