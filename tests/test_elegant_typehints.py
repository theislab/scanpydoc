import inspect
import typing as t

import pytest
from sphinx.application import Sphinx
from sphinx_autodoc_typehints import process_docstring

from scanpydoc.elegant_typehints import format_annotation, _format_terse, _format_full


@pytest.fixture
def app(make_app_no_setup) -> Sphinx:
    app = make_app_no_setup()
    app.setup_extension("scanpydoc.elegant_typehints")
    return app


@pytest.fixture
def process_doc(app):
    app.config.typehints_fully_qualified = True

    def process(fn: t.Callable) -> t.List[str]:
        lines = inspect.getdoc(fn).split("\n")
        process_docstring(app, "function", fn.__name__, fn, None, lines)
        return lines

    return process


def test_default(app):
    assert format_annotation(str) == ":py:class:`str`"


def test_alternatives(process_doc):
    def fn_test(s: str):
        """
        :param s: Test
        """

    assert process_doc(fn_test) == [
        ":type s: "
        r":annotation-terse:`:py:class:\`str\``\ "
        r":annotation-full:`:py:class:\`str\``",
        ":param s: Test",
    ]


def test_defaults_simple(process_doc):
    def fn_test(s: str = "foo", n: None = None, i: int = 1):
        """
        :param s: Test S
        :param n: Test N
        :param i: Test I
        """

    assert process_doc(fn_test) == [
        ":type s: "
        r":annotation-terse:`:py:class:\`str\``\ "
        r":annotation-full:`:py:class:\`str\`` "
        "(default: ``'foo'``)",
        ":param s: Test S",
        ":type n: "
        r":annotation-terse:`\`\`None\`\``\ "
        r":annotation-full:`\`\`None\`\`` "
        "(default: ``None``)",
        ":param n: Test N",
        ":type i: "
        r":annotation-terse:`:py:class:\`int\``\ "
        r":annotation-full:`:py:class:\`int\`` "
        "(default: ``1``)",
        ":param i: Test I",
    ]


def test_defaults_complex(process_doc):
    def fn_test(m: t.Mapping[str, int] = {}):
        """
        :param m: Test M
        """

    assert process_doc(fn_test) == [
        ":type m: "
        r":annotation-terse:`:py:class:\`typing.Mapping\``\ "
        r":annotation-full:`"
        r":py:class:\`typing.Mapping\`\[:py:class:\`str\`, :py:class:\`int\`]"
        "` (default: ``{}``)",
        ":param m: Test M",
    ]


def test_mapping(app):
    assert _format_terse(t.Mapping[str, t.Any]) == ":py:class:`~typing.Mapping`"
    assert _format_full(t.Mapping[str, t.Any]) == (
        r":py:class:`~typing.Mapping`\["
        r":py:class:`str`, "
        r":py:data:`~typing.Any`"
        r"]"
    )


def test_dict(app):
    assert _format_terse(t.Dict[str, t.Any]) == (
        "{:py:class:`str`: :py:data:`~typing.Any`}"
    )


def test_qualname_overrides(app):
    sparse = pytest.importorskip("scipy.sparse")

    assert sparse.spmatrix.__module__ == "scipy.sparse.base"
    assert _format_terse(sparse.spmatrix) == ":py:class:`~scipy.sparse.spmatrix`"


def test_qualname_overrides_recursive(app):
    sparse = pytest.importorskip("scipy.sparse")

    assert _format_terse(t.Union[sparse.spmatrix, str]) == (
        r":py:class:`~scipy.sparse.spmatrix`, :py:class:`str`"
    )
    assert _format_full(t.Union[sparse.spmatrix, str]) == (
        r":py:data:`~typing.Union`\["
        r":py:class:`~scipy.sparse.spmatrix`, "
        r":py:class:`str`"
        r"]"
    )


def test_fully_qualified(app):
    sparse = pytest.importorskip("scipy.sparse")

    assert _format_terse(t.Union[sparse.spmatrix, str], True) == (
        r":py:class:`scipy.sparse.spmatrix`, :py:class:`str`"
    )
    assert _format_full(t.Union[sparse.spmatrix, str], True) == (
        r":py:data:`typing.Union`\["
        r":py:class:`scipy.sparse.spmatrix`, "
        r":py:class:`str`"
        r"]"
    )


def test_classes_get_added(app, parse):
    doc = parse(app, r":annotation-full:`:py:class:\`str\``")
    assert doc[0].tagname == "paragraph"
    assert doc[0][0].tagname == "inline"
    assert doc[0][0]["classes"] == ["annotation", "full"]
    # print(doc.asdom().toprettyxml())


@pytest.mark.parametrize("formatter", [_format_terse, _format_full], ids="tf")
# These guys aren’t listed as classes in Python’s intersphinx index:
@pytest.mark.parametrize(
    "annotation",
    [
        t.Any,
        t.AnyStr,
        # t.NoReturn,
        t.Callable[[int], None],
        # t.ClassVar[t.Any],
        t.Optional[int],
        t.Tuple[int, str],
        t.Tuple[float, ...],
        t.Union[int, str],
    ],
    ids=lambda p: str(p).replace("typing.", ""),
)
def test_typing_classes(app, annotation, formatter):
    name = (
        getattr(annotation, "_name", None)
        or getattr(annotation, "__name__", None)
        or getattr(getattr(annotation, "__origin__", None), "_name", None)
        # 3.6 _Any and _Union
        or annotation.__class__.__name__[1:]
    )
    if name == "Union":
        if formatter is _format_terse:
            pytest.skip("Tested elsewhere")
        elif len(annotation.__args__) == 2 and type(None) in annotation.__args__:
            name = "Optional"
    assert formatter(annotation, True).startswith(f":py:data:`typing.{name}")


def test_typing_class_nested(app):
    assert _format_full(t.Optional[t.Tuple[int, str]]) == (
        ":py:data:`~typing.Optional`\\["
        ":py:data:`~typing.Tuple`\\[:py:class:`int`, :py:class:`str`]"
        "]"
    )
