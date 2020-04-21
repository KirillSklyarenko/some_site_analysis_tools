import sitemapchker as s
import responses


@responses.activate
def test_sitemapurl(monkeypatch):
    url = 'https://example.com/sitemap=xml'
    responses.add(responses.GET, url, status=200)
    monkeypatch.setattr('builtins.input', lambda: url)
    assert s.sitemapurl(url) == url
