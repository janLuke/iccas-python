"""
A simple and crappy i18n library written "for fun" and because neither
gettext and python-i18n were optimal for my use case which requires
reloading of translations when a change is made without restarting the
interpreter/kernel and possibly without reloading the module.
"""
import locale
from collections import ChainMap
from dataclasses import dataclass
from io import StringIO
from itertools import chain
from pathlib import Path
from typing import Optional, Union

import yaml

from iccas.types import PathType


class Translation:
    def __init__(self, lang, strings):
        self.lang = lang
        self.strings = strings

    def __getitem__(self, str_id: str):
        return self.strings[str_id]

    def get(self, str_id: str, count: int, few_max: int = 5, varname="count") -> str:
        if count < 0:
            raise ValueError("negative count")

        plural_strings = self.strings[str_id]
        if isinstance(plural_strings, str):
            return plural_strings.format(**{varname: count})

        if count == 0:
            keys = ("zero", "many")
        elif count == 1:
            keys = ("one", "many")
        elif count <= few_max:
            keys = ("few", "many")
        else:
            keys = ("many",)

        for key in keys:
            if key not in plural_strings:
                continue
            return plural_strings[key].format(**{varname: count})
        else:
            raise KeyError(
                f"pluralization error for key '{str_id}' and count {count}: "
                f"none of keys in {keys} were specified"
            )


class NullTranslation(Translation):
    def __getitem__(self, str_id: str) -> str:
        return str_id

    def get(self, str_id: str, count: int, few_max: int = 5, varname="count") -> str:
        return str_id


@dataclass
class TranslationFile:
    path: Path
    content: dict
    last_modified: int

    def reload_if_modified(self) -> bool:
        last_modified = self.path.stat().st_mtime_ns
        if self.last_modified != last_modified:
            self.content = self.read(self.path)
            self.last_modified = self.last_modified
            return True
        return False

    @staticmethod
    def load(path: PathType) -> "TranslationFile":
        path = Path(path)
        content = TranslationFile.read(path)
        last_modified = path.stat().st_mtime_ns
        return TranslationFile(path=path, content=content, last_modified=last_modified)

    @staticmethod
    def read(path: PathType):
        with open(path, encoding="utf-8") as f:
            return yaml.full_load(f)


class TranslationsManager:
    def __init__(self, *paths):
        self.files = [TranslationFile.load(path) for path in set(paths)]
        self.languages = set(chain.from_iterable(f.content.keys() for f in self.files))
        default_lang = locale.getdefaultlocale()[0].split("_")[0]
        self.current_language = default_lang if default_lang in self.languages else "en"

    def _reload_modified_files(self):
        for file in self.files:
            file.reload_if_modified()

    def injector(self, scoped_translations: Union[None, str, dict] = None):
        """
        Decorator that adds a ``lang`` argument to the signature and injects a
        ``strings`` argument of type :class:`Translation`.
        If the translation files are modified, they are automatically reloaded.

        You can also pass extra translations as dict or YAML string to the wrapped
        function. Nonetheless, any modification will require to reload the module
        to take effect.

        Args:
            scoped_translations: yaml string or dictionary
        """
        if scoped_translations and isinstance(scoped_translations, str):
            with StringIO(scoped_translations) as s:
                scoped_translations = yaml.full_load(s) or {}
        elif scoped_translations is None:
            scoped_translations = {}

        def decorator(func):
            def wrapper(*args, lang: Optional[str] = None, **kwargs):
                lang = lang or self.current_language
                self._reload_modified_files()
                mappings = (
                    [scoped_translations[lang]] if lang in scoped_translations else []
                )
                mappings += [f.content[lang] for f in self.files if lang in f.content]
                strings = ChainMap(*mappings)
                strings = Translation(lang, strings)
                return func(*args, strings=strings, **kwargs)

            wrapper.translation_manager = self
            wrapper.wrapped_function = func
            return wrapper

        return decorator
