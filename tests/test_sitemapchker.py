import pytest
import responses

import sitemapchker as s


@pytest.fixture()
@responses.activate
def mocked_response():
    content = f"""
                <?xml version='1.0' encoding='UTF-8'?>
                <urlset>
                <url>
                <loc>https://site.ru/</loc>
                </url>
                <url>
                <loc>https://site.ru/1/</loc>
                </url>
                <url>
                <loc>https://site.ru/2/</loc>
                </url>
                <url>
                <loc>https://site.ru/3/</loc>
                </url>
                <url>
                <loc>https://site.ru/4/</loc>
                </url>
                <url>
                <loc>https://site.ru/5/</loc>
                </url>
                </urlset>
                """
    return content


class TestSitemapurl:

    @responses.activate
    def test_correct(self, monkeypatch, mocked_response):
        url = 'https://example.com/sitemap=xml'
        responses.add(responses.GET, url, body=mocked_response, status=200)
        monkeypatch.setattr('builtins.input', lambda x: url)
        assert isinstance(s.sitemapurl(), str)

    def test_e(self, monkeypatch):
        e_input = 'e'
        monkeypatch.setattr('builtins.input', lambda x: e_input)
        with pytest.raises(SystemExit):
            s.sitemapurl()

    def test_E(self, monkeypatch):
        E_input = 'E'
        monkeypatch.setattr('builtins.input', lambda x: E_input)
        with pytest.raises(SystemExit):
            s.sitemapurl()

    def test_sitemaplist(self, mocked_response):
        returned_list = ['https://site.ru/', 'https://site.ru/1/',
                         'https://site.ru/2/', 'https://site.ru/3/',
                         'https://site.ru/4/', 'https://site.ru/5/']
        assert s.sitemaplist(mocked_response) == returned_list

    @responses.activate
    def test_checkerfirstcall(self):
        url = 'https://site.ru/'
        url2 = 'https://site.ru/1/'
        responses.add(responses.GET, url, status=200)
        responses.add(responses.GET, url2, status=404)
        assert s.checker(url) == [(url, 200)]
        assert s.checker(url2) == [(url, 200), (url2, 404)]
