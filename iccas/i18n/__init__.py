import locale
from contextlib import contextmanager
from pathlib import Path

from iccas.i18n.lib import TranslationsManager

# These should work both on Windows and Linux (provided that the corresponding
# language packs are installed, e.g. language-pack-it)
LANG_TO_LOCALE = {
    'it': 'it_IT.UTF-8',
    'en': 'en_US.UTF-8'
}

_TRANSLATIONS_PATH = Path(__file__).parent / "translations.yml"
TRANSLATIONS = TranslationsManager(_TRANSLATIONS_PATH)

# Decorator for injecting global translations + optional scoped translations
translated = TRANSLATIONS.injector


def set_language(lang):
    """
    Sets the language. Supported languages: Italian ("it") and English ("en")
    """
    TRANSLATIONS.current_language = lang


@contextmanager
def language(lang):
    entry_lang = TRANSLATIONS.current_language
    TRANSLATIONS.current_language = lang
    yield
    TRANSLATIONS.current_language = entry_lang


def set_locale(lang):
    """ Apart from setting the internal language of the package, also sets the
    locale accordingly so that pandas/matplotlib displays translated dates """
    if lang not in TRANSLATIONS.languages:
        raise ValueError(f'language not supported: {lang}')
    locale.setlocale(locale.LC_ALL, LANG_TO_LOCALE[lang])
    set_language(lang)
