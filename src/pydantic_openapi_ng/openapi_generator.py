import importlib.machinery
import json
import sys
from contextlib import contextmanager
from importlib import import_module
from importlib.util import module_from_spec, spec_from_file_location
from typing import Optional

from pydantic import BaseModel
from pydantic.schema import schema

from .camel_case import camelize


@contextmanager
def add_to_modules(spec, module):
    old_modules = sys.modules
    sys.modules[spec.name] = module
    try:
        yield
    finally:
        sys.modules = old_modules


class OpenAPIGenerator:
    def __init__(
        self,
        *,
        indent: int = 2,
        ref_prefix: str = "#/components/schemas/",
        title: Optional[str] = None,
        by_alias: bool = True,
        description: Optional[str] = None,
    ):
        self.description = description
        self.by_alias = by_alias
        self.indent = indent
        self.ref_prefix = ref_prefix
        self.title = title
        self.models = []

    @property
    @camelize
    def schema(self) -> dict:
        return schema(
            self.models,
            by_alias=self.by_alias,
            title=self.title,
            description=self.description,
            ref_prefix=self.ref_prefix,
        )

    def render(self) -> str:
        return json.dumps(self.schema, indent=self.indent)

    def load_module(self, module_path: str):
        module_name = module_path.rstrip(".py").replace("/", ".")
        spec = spec_from_file_location(module_name, module_path)
        module = module_from_spec(spec)
        # https://docs.python.org/3/library/importlib.html#checking-if-a-module-can-be-imported
        with add_to_modules(spec, module):
            spec.loader.exec_module(module)
        for model_name in module.__all__:
            self.models.append(getattr(module, model_name))

    @staticmethod
    def model_to_swagger(model: BaseModel, indent: int = 2):
        return json.dumps(model.schema(), indent=indent)
