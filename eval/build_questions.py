"""Writes eval/questions.jsonl and checks every evidence quote against the corpus.

    uv run python -m eval.build_questions

A retrieved chunk counts as relevant when it belongs to the expected PEP and contains the
evidence quote (case and whitespace are normalized). Quotes are short so that chunking
rarely splits them.
"""

import json
import re
from pathlib import Path

from eval.corpus import CORPUS_DIR, filename

OUT = Path(__file__).parent / "questions.jsonl"

# (language, question, pep, evidence)
ANSWERABLE: list[tuple[str, str, int, str]] = [
    ("en", "How many spaces should be used per indentation level?", 8,
     "Use 4 spaces per indentation level"),
    ("es", "¿Cuál es la longitud máxima de línea recomendada en la guía de estilo de Python?", 8,
     "maximum of 79 characters"),
    ("es", "¿Cómo se deben nombrar las clases según la guía de estilo?", 8,
     "Class names should normally use the CapWords convention"),
    ("en", "Why should I avoid a bare except clause?", 8,
     "bare ``except:`` clause will catch SystemExit"),
    ("en", "Are absolute or relative imports recommended?", 8,
     "Absolute imports are recommended"),
    ("es", "¿Cuántas líneas en blanco deben rodear las funciones y clases de nivel superior?", 8,
     "Surround top-level function and class definitions with two blank"),
    ("en", "How should module-level constants be named?", 8,
     "Constants are usually defined on a module level"),
    ("es", "¿Cómo se debe comparar un valor con None?", 8,
     "Comparisons to singletons like None should always be done with"),
    ("en", "What does the Zen of Python say about errors?", 20,
     "Errors should never pass silently"),
    ("es", "¿Qué dice el Zen de Python sobre cuántas formas obvias debe haber de hacer algo?", 20,
     "preferably only one --obvious way to do it"),
    ("en", "What kind of quotes should docstrings use?", 257,
     "triple double quotes"),
    ("es", "¿Cuándo conviene usar un docstring de una sola línea?", 257,
     "One-liners are for really obvious cases"),
    ("en", "Which attribute stores the docstring of an object?", 257,
     "becomes the ``__doc__`` special attribute"),
    ("en", "Which methods must a context manager provide for the with statement?", 343,
     "context managers provide ``__enter__()`` and ``__exit__()``"),
    ("es", "¿Qué decorador permite escribir un context manager como un generador?", 343,
     "``@contextmanager`` decorator"),
    ("en", "What syntax lets a generator delegate part of its operations to another one?", 380,
     "a generator to delegate part of its"),
    ("es", "¿Qué pasa cuando la llamada al subgenerador lanza StopIteration en yield from?", 380,
     "call raises StopIteration, the delegating generator is resumed"),
    ("en", "Where does Python look for the pyvenv.cfg file?", 405,
     "file is found either adjacent to the Python executable"),
    ("es", "¿Qué variable de entorno existente controla el prefijo de Python?", 405,
     "The ``PYTHONHOME`` environment variable"),
    ("en", "What is an enumeration?", 435,
     "An enumeration is a set of symbolic names bound to unique, constant values"),
    ("es", "¿Cuál es la diferencia clave entre Enum e IntEnum?", 435,
     "The key dividing issue between ``Enum`` and ``IntEnum``"),
    ("en", "How can I create an enum with the functional API?", 435,
     "Animal = Enum('Animal', 'ant bee cat dog')"),
    ("en", "What does PEP 448 propose for iterable unpacking?", 448,
     "extended usages of the ``*`` iterable unpacking"),
    ("es", "¿De qué módulo vienen las anotaciones de tipo estándar?", 484,
     "from a pure-Python module ``typing``"),
    ("en", "What are stub files used for?", 484,
     "Stub files are files containing type hints that are only for use by"),
    ("es", "¿Cómo se escribe un comentario de tipo para una variable?", 484,
     "# type: Vector[float]"),
    ("en", "Which type is consistent with every other type?", 484,
     "named ``Any`` which is consistent with"),
    ("en", "Are async def functions always coroutines?", 492,
     "``async def`` functions are always coroutines"),
    ("es", "¿Qué métodos mágicos nuevos se agregan para los context managers asíncronos?", 492,
     "Two new magic methods are added: ``__aenter__`` and"),
    ("en", "How do asynchronous iterators work with async for?", 492,
     'Asynchronous Iterators and "async for"'),
    ("en", "What are f-strings?", 498,
     "F-strings provide a way to embed expressions inside string literals"),
    ("es", "¿Qué conversiones como !r permite un f-string?", 498,
     "The allowed conversions are ``'!s'``, ``'!r'``"),
    ("es", "¿Qué mecanismos de formateo de cadenas existían antes de los f-strings?", 498,
     "``str.format()`` [#]_, and ``string.Template``"),
    ("en", "Where are variable annotations stored at runtime?", 526,
     "``__annotations__`` attribute of that module or class"),
    ("es", "¿Cómo se anota una variable de clase con ClassVar?", 526,
     "stats: ClassVar[Dict[str, int]] = {}"),
    ("en", "Which methods does the dataclass decorator add?", 557,
     "The ``@dataclass`` decorator will add the equivalent of these methods"),
    ("es", "¿Cuándo se llama a __post_init__ en una dataclass?", 557,
     "as ``self.__post_init__()``"),
    ("en", "What is the signature of the dataclasses field function?", 557,
     "def field(*, default=MISSING, default_factory=MISSING"),
    ("en", "What is the formal name of the walrus operator?", 572,
     'The construct\'s formal name is "Assignment Expressions"'),
    ("es", "¿Qué notación usan las expresiones de asignación?", 572,
     "expression using the notation ``NAME := expr``"),
    ("en", "Which operators does PEP 584 add to dict?", 584,
     "adding merge (``|``) and update (``|=``) operators"),
    ("es", "¿La unión de diccionarios es conmutativa?", 584,
     "Dict Union Is Not Commutative"),
    ("en", "Should I still import List and Dict from typing?", 585,
     "Importing those from ``typing`` is deprecated"),
    ("es", "¿Puedo anotar con dict[str, list[int]] usando los tipos de la biblioteca estándar?",
     585, "def find(haystack: dict[str, list[int]]) -> int:"),
    ("en", "How can I write Union[X, Y] more concisely?", 604,
     "writing ``Union[X, Y]`` as ``X | Y``"),
    ("es", "¿Se puede usar X | Y en isinstance?", 604,
     "``isinstance`` and ``issubclass`` calls"),
    ("en", "What happens with zip(strict=True) when the iterables have different lengths?", 618,
     "the resulting iterator will raise a ``ValueError`` if"),
    ("es", "¿Qué parámetro nuevo se propone para la función zip?", 618,
     "optional ``strict`` boolean keyword"),
    ("en", "What is a guard in a match statement?", 634,
     "guard: 'if' named_expression"),
    ("en", "Can a class pattern repeat the same keyword?", 634,
     "A class pattern may not repeat the same keyword multiple times"),
    ("es", "¿Cuál es la gramática de un bloque case?", 634,
     'case_block: "case" patterns [guard]'),
    ("en", "What does TypeVarTuple enable?", 646,
     "we introduce ``TypeVarTuple``, enabling parameterisation"),
    ("es", "¿Cómo se usa el operador estrella para desempaquetar tipos variádicos?", 646,
     "a new use for the star operator: to 'unpack'"),
    ("en", "How do I mark a single TypedDict key as not required?", 655,
     "``NotRequired[]``, which can be used on individual items"),
    ("es", "¿Qué hace total=False en un TypedDict?", 655,
     "class Movie(TypedDict, total=False):"),
    ("en", "How do I annotate a method that returns an instance of its own class?", 673,
     "def set_scale(self, scale: float) -> Self:"),
    ("en", "Is there a new statement for declaring type aliases?", 695,
     "a new statement for declaring type aliases"),
    ("es", "¿Cómo se declara una función genérica con la nueva sintaxis de parámetros de tipo?",
     695, "def func[T](a: T, b: T) -> T:"),
    ("en", "Is the variance of new-style type parameters inferred?", 695,
     "Type parameters are inferred to be"),
    ("en", "Can f-string expressions contain backslashes?", 701,
     "lack of support for backslashes"),
    ("es", "¿Se pueden reutilizar las mismas comillas dentro de un f-string anidado?", 701,
     "string quotes cannot be reused"),
    ("en", "What does the global interpreter lock prevent?", 703,
     "prevents multiple threads from executing Python code at the same time"),
    ("es", "¿Qué técnica de conteo de referencias propone el PEP para quitar el GIL?", 703,
     "Biased reference counting (BRC)"),
    ("es", "¿Qué opción de configuración compila CPython sin el GIL?", 703,
     "a build configuration (``--disable-gil``)"),
    ("en", "How do I declare dependencies inside a single-file script?", 723,
     "# /// script"),
    ("es", "¿Qué campos de nivel superior puede incluir el bloque de metadatos de un script?", 723,
     "top-level fields ``dependencies`` and ``requires-python``"),
]  # fmt: skip

# Questions the corpus cannot answer. "hard" ones are about Python but outside these PEPs.
UNANSWERABLE: list[tuple[str, str, bool]] = [
    ("en", "How do I configure a Kubernetes ingress controller?", False),
    ("en", "What is the capital of Australia?", False),
    ("en", "How do I center a div with CSS flexbox?", False),
    ("en", "How do I set up streaming replication in PostgreSQL?", False),
    ("es", "¿Cuál es la receta tradicional del gallo pinto?", False),
    ("es", "¿Cómo se configura un router wifi doméstico?", False),
    ("es", "¿Qué es la fotosíntesis?", False),
    ("es", "¿Cuántos jugadores tiene un equipo de fútbol en la cancha?", False),
    ("es", "¿Cómo se instala Java en Ubuntu?", False),
    ("es", "¿Cómo funciona el recolector de basura de la JVM?", False),
    ("en", "What does the WSGI specification require from a web application callable?", True),
    ("en", "How does the asyncio event loop schedule callbacks on Windows?", True),
    ("es", "¿Qué propone el PEP de las expresiones lambda con varias líneas?", True),
    ("en", "How do I publish a package to PyPI with twine?", True),
    ("es", "¿Cómo se configura el logging con un archivo dictConfig?", True),
    ("en", "What are the rules for Python wheel file names?", True),
]  # fmt: skip


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def build() -> int:
    missing = []
    rows = []
    for i, (lang, question, pep, evidence) in enumerate(ANSWERABLE, start=1):
        source = (CORPUS_DIR / filename(pep)).read_text("utf-8")
        if normalize(evidence) not in normalize(source):
            missing.append((pep, evidence))
        rows.append(
            {
                "id": f"a{i:03d}",
                "lang": lang,
                "question": question,
                "doc": filename(pep),
                "evidence": evidence,
                "answerable": True,
            }
        )
    for i, (lang, question, hard) in enumerate(UNANSWERABLE, start=1):
        rows.append(
            {
                "id": f"u{i:03d}",
                "lang": lang,
                "question": question,
                "doc": None,
                "evidence": None,
                "answerable": False,
                "hard_negative": hard,
            }
        )
    for pep, evidence in missing:
        print(f"MISSING in pep {pep}: {evidence}")
    OUT.write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8"
    )
    print(f"{len(ANSWERABLE)} answerable, {len(UNANSWERABLE)} unanswerable -> {OUT.name}")
    return len(missing)


if __name__ == "__main__":
    raise SystemExit(build())
