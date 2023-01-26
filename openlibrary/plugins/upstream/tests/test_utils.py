from openlibrary.mocks.mock_infobase import MockSite
from .. import utils
from openlibrary.catalog.add_book.tests.conftest import add_languages
import web
import pytest


def test_url_quote():
    assert utils.url_quote('https://foo bar') == 'https%3A%2F%2Ffoo+bar'
    assert utils.url_quote('abc') == 'abc'
    assert utils.url_quote('Kabitā') == 'Kabit%C4%81'
    assert utils.url_quote('Kabit\u0101') == 'Kabit%C4%81'


def test_urlencode():
    f = utils.urlencode
    assert f({}) == '', 'empty dict'
    assert f([]) == '', 'empty list'
    assert f({'q': 'hello'}) == 'q=hello', 'basic dict'
    assert f({'q': ''}) == 'q=', 'empty param value'
    assert f({'q': None}) == 'q=None', 'None param value'
    assert f([('q', 'hello')]) == 'q=hello', 'basic list'
    assert f([('x', '3'), ('x', '5')]) == 'x=3&x=5', 'list with multi keys'
    assert f({'q': 'a b c'}) == 'q=a+b+c', 'handles spaces'
    assert f({'q': 'a$$'}) == 'q=a%24%24', 'handles special ascii chars'
    assert f({'q': 'héé'}) == 'q=h%C3%A9%C3%A9'
    assert f({'q': 'héé'}) == 'q=h%C3%A9%C3%A9', 'handles unicode without the u?'
    assert f({'q': 1}) == 'q=1', 'numbers'
    assert f({'q': ['test']}) == 'q=%5B%27test%27%5D', 'list'
    assert f({'q': 'αβγ'}) == 'q=%CE%B1%CE%B2%CE%B3', 'unicode without the u'
    assert f({'q': 'αβγ'.encode()}) == 'q=%CE%B1%CE%B2%CE%B3', 'uf8 encoded unicode'
    assert f({'q': 'αβγ'}) == 'q=%CE%B1%CE%B2%CE%B3', 'unicode'


def test_entity_decode():
    assert utils.entity_decode('&gt;foo') == '>foo'
    assert utils.entity_decode('<h1>') == '<h1>'


def test_set_share_links():
    class TestContext:
        def __init__(self):
            self.share_links = None

    test_context = TestContext()
    utils.set_share_links(url='https://foo.com', title="bar", view_context=test_context)
    assert test_context.share_links == [
        {
            'text': 'Facebook',
            'url': 'https://www.facebook.com/sharer/sharer.php?u=https%3A%2F%2Ffoo.com',
        },
        {
            'text': 'Twitter',
            'url': 'https://twitter.com/intent/tweet?url=https%3A%2F%2Ffoo.com&via=openlibrary&text=Check+this+out%3A+bar',
        },
        {
            'text': 'Pinterest',
            'url': 'https://pinterest.com/pin/create/link/?url=https%3A%2F%2Ffoo.com&description=Check+this+out%3A+bar',
        },
    ]


def test_set_share_links_unicode():
    # example work that has a unicode title: https://openlibrary.org/works/OL14930766W/Kabit%C4%81
    class TestContext:
        def __init__(self):
            self.share_links = None

    test_context = TestContext()
    utils.set_share_links(
        url='https://foo.\xe9', title='b\u0101', view_context=test_context
    )
    assert test_context.share_links == [
        {
            'text': 'Facebook',
            'url': 'https://www.facebook.com/sharer/sharer.php?u=https%3A%2F%2Ffoo.%C3%A9',
        },
        {
            'text': 'Twitter',
            'url': 'https://twitter.com/intent/tweet?url=https%3A%2F%2Ffoo.%C3%A9&via=openlibrary&text=Check+this+out%3A+b%C4%81',
        },
        {
            'text': 'Pinterest',
            'url': 'https://pinterest.com/pin/create/link/?url=https%3A%2F%2Ffoo.%C3%A9&description=Check+this+out%3A+b%C4%81',
        },
    ]


def test_item_image():
    assert utils.item_image('//foo') == 'https://foo'
    assert utils.item_image(None, 'bar') == 'bar'
    assert utils.item_image(None) is None


def test_canonical_url():
    web.ctx.path = '/authors/Ayn_Rand'
    web.ctx.query = ''
    web.ctx.host = 'www.openlibrary.org'
    request = utils.Request()

    url = 'https://www.openlibrary.org/authors/Ayn_Rand'
    assert request.canonical_url == url

    web.ctx.query = '?sort=newest'
    url = 'https://www.openlibrary.org/authors/Ayn_Rand'
    assert request.canonical_url == url

    web.ctx.query = '?page=2'
    url = 'https://www.openlibrary.org/authors/Ayn_Rand?page=2'
    assert request.canonical_url == url

    web.ctx.query = '?page=2&sort=newest'
    url = 'https://www.openlibrary.org/authors/Ayn_Rand?page=2'
    assert request.canonical_url == url

    web.ctx.query = '?sort=newest&page=2'
    url = 'https://www.openlibrary.org/authors/Ayn_Rand?page=2'
    assert request.canonical_url == url

    web.ctx.query = '?sort=newest&page=2&mode=e'
    url = 'https://www.openlibrary.org/authors/Ayn_Rand?page=2'
    assert request.canonical_url == url

    web.ctx.query = '?sort=newest&page=2&mode=e&test=query'
    url = 'https://www.openlibrary.org/authors/Ayn_Rand?page=2&test=query'
    assert request.canonical_url == url

    web.ctx.query = '?sort=new&mode=2'
    url = 'https://www.openlibrary.org/authors/Ayn_Rand'
    assert request.canonical_url == url


def test_get_coverstore_url(monkeypatch):
    from infogami import config

    monkeypatch.delattr(config, "coverstore_url", raising=False)
    assert utils.get_coverstore_url() == "https://covers.openlibrary.org"

    monkeypatch.setattr(config, "coverstore_url", "https://0.0.0.0:80", raising=False)
    assert utils.get_coverstore_url() == "https://0.0.0.0:80"

    # make sure trailing / is always stripped
    monkeypatch.setattr(config, "coverstore_url", "https://0.0.0.0:80/", raising=False)
    assert utils.get_coverstore_url() == "https://0.0.0.0:80"


def test_reformat_html():
    f = utils.reformat_html

    input_string = '<p>This sentence has 32 characters.</p>'
    assert f(input_string, 10) == 'This sente...'
    assert f(input_string) == 'This sentence has 32 characters.'
    assert f(input_string, 5000) == 'This sentence has 32 characters.'

    multi_line_string = """<p>This sentence has 32 characters.</p>
                           <p>This new sentence has 36 characters.</p>"""
    assert (
        f(multi_line_string) == 'This sentence has 32 '
        'characters.<br>This new sentence has 36 characters.'
    )
    assert f(multi_line_string, 34) == 'This sentence has 32 ' 'characters.<br>T...'

    assert f("<script>alert('hello')</script>", 34) == "alert(&#39;hello&#39;)"
    assert f("&lt;script&gt;") == "&lt;script&gt;"


def test_strip_accents():
    f = utils.strip_accents
    assert f('Plain ASCII text') == 'Plain ASCII text'
    assert f('Des idées napoléoniennes') == 'Des idees napoleoniennes'
    # It only modifies Unicode Nonspacing Mark characters:
    assert f('Bokmål : Standard Østnorsk') == 'Bokmal : Standard Østnorsk'


def test_get_abbrev_from_full_lang_name(
    mock_site: MockSite, monkeypatch, add_languages  # noqa F811
) -> None:
    utils.get_languages.cache_clear()

    monkeypatch.setattr(web, "ctx", web.storage())
    web.ctx.site = mock_site

    web.ctx.site.save(
        {
            "code": "eng",
            "key": "/languages/eng",
            "name": "English",
            "type": {"key": "/type/language"},
            "name_translated": {
                "tg": ["ингилисӣ"],
                "en": ["English"],
                "ay": ["Inlish aru"],
                "pnb": ["انگریزی"],
                "na": ["Dorerin Ingerand"],
            },
        }
    )

    web.ctx.site.save(
        {
            "code": "fre",
            "key": "/languages/fre",
            "name": "French",
            "type": {"key": "/type/language"},
            "name_translated": {
                "ay": ["Inlish aru"],
                "fr": ["anglais"],
                "es": ["spanish"],
            },
        }
    )

    web.ctx.site.save(
        {
            "code": "spa",
            "key": "/languages/spa",
            "name": "Spanish",
            "type": {"key": "/type/language"},
        }
    )

    assert utils.get_abbrev_from_full_lang_name("EnGlish") == "eng"
    assert utils.get_abbrev_from_full_lang_name("Dorerin Ingerand") == "eng"
    assert utils.get_abbrev_from_full_lang_name("ингилисӣ") == "eng"
    assert utils.get_abbrev_from_full_lang_name("ингилиси") == "eng"
    assert utils.get_abbrev_from_full_lang_name("Anglais") == "fre"

    # See openlibrary/catalog/add_book/tests/conftest.py for imported languages.
    with pytest.raises(utils.LanguageMultipleMatchError):
        utils.get_abbrev_from_full_lang_name("frisian")

    with pytest.raises(utils.LanguageMultipleMatchError):
        utils.get_abbrev_from_full_lang_name("inlish aru")

    with pytest.raises(utils.LanguageMultipleMatchError):
        utils.get_abbrev_from_full_lang_name("Spanish")

    with pytest.raises(utils.LanguageNoMatchError):
        utils.get_abbrev_from_full_lang_name("Missing or non-existent language")


def test_get_isbn_10_and_13() -> None:
    # isbn 10 only
    result = utils.get_isbn_10_and_13(["1576079457"])
    assert result == (["1576079457"], [])

    # isbn 13 only
    result = utils.get_isbn_10_and_13(["9781576079454"])
    assert result == ([], ["9781576079454"])

    # mixed isbn 10 and 13, with multiple elements in each, one which has an extra space.
    result = utils.get_isbn_10_and_13(
        ["9781576079454", "1576079457", "1576079392 ", "9781280711190"]
    )
    assert result == (["1576079457", "1576079392"], ["9781576079454", "9781280711190"])

    # an empty list
    result = utils.get_isbn_10_and_13([])
    assert result == ([], [])

    # not an isbn
    result = utils.get_isbn_10_and_13(["flop"])
    assert result == ([], [])

    # isbn 10 string, with an extra space.
    result = utils.get_isbn_10_and_13(" 1576079457")
    assert result == (["1576079457"], [])

    # isbn 13 string
    result = utils.get_isbn_10_and_13("9781280711190")
    assert result == ([], ["9781280711190"])


def test_get_publisher_and_place() -> None:
    # Just a publisher, as a string
    result = utils.get_publisher_and_place("Simon & Schuster")
    assert result == (["Simon & Schuster"], [])

    # Publisher and place, as a string
    result = utils.get_publisher_and_place("New York : Simon & Schuster")
    assert result == (["Simon & Schuster"], ["New York"])

    # Publisher and place, as a list
    result = utils.get_publisher_and_place(["New York : Simon & Schuster"])
    assert result == (["Simon & Schuster"], ["New York"])

    # A mix of publishers and places
    result = utils.get_publisher_and_place(
        [
            "New York : Simon & Schuster",
            "Random House",
            "Boston : Harvard University Press",
        ]
    )
    assert result == (
        ["Simon & Schuster", "Random House", "Harvard University Press"],
        ["New York", "Boston"],
    )
