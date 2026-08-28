from typing import Dict, List, Type, Union

from app.ir.nodes import IRProgram
from .base_generator import BaseCodeGenerator
from .exceptions import GeneratorNotFoundError


class TranslationEngine:

    def __init__(self, register_defaults: bool = True):
        self._generators: Dict[str, Union[Type[BaseCodeGenerator], BaseCodeGenerator]] = {}
        if register_defaults:
            from .java_generator import JavaGenerator
            from .cpp_generator import CppGenerator
            from .javascript_generator import JavaScriptGenerator
            self.register_generator("java", JavaGenerator)
            self.register_generator("cpp", CppGenerator)
            self.register_generator("javascript", JavaScriptGenerator)

    def _normalize_lang(self, language: str) -> str:
        """Normalize language identifier for case-insensitive lookup."""
        lang = language.strip().lower()
        aliases = {
            "js": "javascript",
            "c++": "cpp",
            "py": "python",
        }
        return aliases.get(lang, lang)

    def register_generator(
        self,
        language: str,
        generator: Union[Type[BaseCodeGenerator], BaseCodeGenerator],
    ) -> None:
        """
        Register a target code generator class or instance for a specific language.

        Args:
            language (str): Target language identifier (e.g. 'java', 'cpp', 'javascript').
            generator (Type[BaseCodeGenerator] | BaseCodeGenerator): Generator class or instance.
        """
        norm_lang = self._normalize_lang(language)
        self._generators[norm_lang] = generator

    def unregister_generator(self, language: str) -> bool:
        """Unregister a target generator if present."""
        norm_lang = self._normalize_lang(language)
        if norm_lang in self._generators:
            del self._generators[norm_lang]
            return True
        return False

    def get_generator(self, language: str) -> BaseCodeGenerator:
        """
        Retrieves an instantiated generator for the given language.

        Raises:
            GeneratorNotFoundError: If no generator is registered for the language.
        """
        norm_lang = self._normalize_lang(language)
        if norm_lang not in self._generators:
            raise GeneratorNotFoundError(language=language)

        gen = self._generators[norm_lang]
        if isinstance(gen, type):
            return gen()
        return gen

    def supported_languages(self) -> List[str]:
        """Returns the list of currently registered target languages."""
        return sorted(list(self._generators.keys()))

    def translate(self, program: Union[IRProgram, str], target_language: str) -> str:
        """
        Translates an IRProgram or Python source string into target language source code using the registered generator.

        Args:
            program (Union[IRProgram, str]): The Intermediate Representation or source code string.
            target_language (str): The name of the target language.

        Returns:
            str: Generated source code in the target language.

        Raises:
            GeneratorNotFoundError: If the target language generator is not found.
            UnsupportedIRNodeError: If the IR contains a node unhandled by the generator.
        """
        if isinstance(program, str):
            from app.ir.builder import build_ir
            program = build_ir(program)

        generator = self.get_generator(target_language)
        return generator.generate(program)
