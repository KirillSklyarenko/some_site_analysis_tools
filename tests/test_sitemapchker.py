import random

from pathlib import Path
import pytest
import responses
from requests.exceptions import ConnectionError


import sitemapchker as s


@pytest.fixture(name="mocked_response")
@responses.activate
def fixture_mocked_response():
    "xml structure with url tags"
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


@pytest.fixture(name="returned_list")
def fixture_returned_list():
    "list of urls to be obtained from the xml structure"
    returned_list = ['https://site.ru/', 'https://site.ru/1/',
                     'https://site.ru/2/', 'https://site.ru/3/',
                     'https://site.ru/4/', 'https://site.ru/5/']
    return returned_list


@pytest.fixture(name="response_tuples")
def fixture_mocked_responseurls(returned_list):
    "list of (url, status) tuples"
    random_status = [200, 300, 404, 503, "ConnectionError"]
    response_tuples = [(i, random.choice(random_status)) for i in returned_list]
    return response_tuples


class TestSitemapurl:

    @responses.activate
    def test_correct(self, monkeypatch, mocked_response):
        "mock input func and provided xml sitemap"
        url = 'https://example.com/sitemap=xml'
        responses.add(responses.GET, url, body=mocked_response, status=200)
        monkeypatch.setattr('builtins.input', lambda x: url)
        assert isinstance(s.sitemapurl(), str)

    @pytest.mark.parametrize("inputs", ['e', 'E'])
    def test_e(self, monkeypatch, inputs):
        "user wants to exit and inputs e or E as a selection"
        monkeypatch.setattr('builtins.input', lambda x: inputs)
        with pytest.raises(SystemExit):
            s.sitemapurl()


def test_sitemaplist(mocked_response, returned_list):
    assert s.sitemaplist(mocked_response) == returned_list


@responses.activate
def test_checker(response_tuples):
    """response_tuples list is used to prepare responses with responses.add()
        and the list returned by the tested func shall be equal to response_tuples
    """
    responses_list = []
    for i in response_tuples:
        if isinstance(i[1], int):
            responses.add(responses.GET, i[0], status=i[1])
            returned_tuple = s.checker(i[0])
            responses_list.append(returned_tuple)
        else:
            with pytest.raises(ConnectionError):
                returned_tuple = s.checker(i[0])
                responses_list.append(returned_tuple)
                raise ConnectionError
    assert response_tuples == responses_list


class TestAskforoutput:

    @pytest.mark.parametrize("inputs", ['y', 'Y'])
    def test_answer_y(self, monkeypatch, inputs):
        "mock input func and provided positive input. Func shall return True"
        monkeypatch.setattr('builtins.input', lambda x: inputs)
        assert s.ask_for_output() is True

    @pytest.mark.parametrize("inputs", ['n', 'N'])
    def test_answer_n(self, monkeypatch, inputs):
        "mock input func and provided negative input. Func shall terminate"
        monkeypatch.setattr('builtins.input', lambda x: inputs)
        with pytest.raises(SystemExit):
            s.ask_for_output()


def test_createdoutput(response_tuples):
    """response_tuples list is used to create a dict
        with statuses as keys and urls as their list
        assert that all urls from response_tuples appear
        in the return of the tested func
    """
    result = s.created_output(response_tuples)
    for k, v in response_tuples:
        assert k in result[v]


def test_outputtofile(response_tuples):
    """file is created with the result, the latter is checked
    and then the file is deleted"""
    result = s.created_output(response_tuples)
    s.output_to_file(result)
    if Path('sitemap_output.txt').is_file() is True:
        with open('sitemap_output.txt', 'r') as f:
            for k, v in response_tuples:
                assert k or v in f.readlines()
        Path.unlink(Path('sitemap_output.txt'))
    else:
        print("sitemap_output.txt was not created")
