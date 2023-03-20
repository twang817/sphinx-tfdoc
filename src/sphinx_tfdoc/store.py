import json
import os
import re
import subprocess

from sphinx.config import Config
from sphinx.errors import ExtensionError
from sphinx.util import status_iterator
from sphinx.util.console import darkgreen, bold
from sphinx.util.logging import getLogger


logger = getLogger(__name__)


def _strip_leading_spaces(lines: list[str]) -> list[str]:
    if lines:
        spaces = min([len(line) - len(line.lstrip()) for line in lines if len(line)])
        lines = [line[spaces:] for line in lines]
    return lines


def _should_ignore(config: Config, line: str) -> bool:
    for pat in config.tfdoc_docstring_ignores:
        if isinstance(pat, str):
            if pat in line:
                return True
        elif isinstance(pat, re.Pattern):
            if pat.match(line):
                return True
    return False


class TerraformModule:
    template = "module"

    def __init__(self, config: Config, name: str, root: str):
        self.config = config
        # a module is named from its path relative to the root that discovered the module
        # root is the path that was used to discover the module
        self.name = name
        self.root = root
        self.path = os.path.join(root, name)
        self.data_resources: dict[str, TerraformDataResource] = {}
        self.managed_resources: dict[str, TerraformManagedResource] = {}
        self.module_calls: dict[str, TerraformModuleCall] = {}
        self.outputs: dict[str, TerraformOutput] = {}
        self.required_providers: dict[str, TerraformRequiredProvider] = {}
        self.variables: dict[str, TerraformVariable] = {}

    def __str__(self) -> str:
        return f"tf:module {self.name}"

    def add_child(self, name: str, obj: "TerraformObjectBase") -> None:
        if isinstance(obj, TerraformDataResource):
            self.data_resources[name] = obj
        elif isinstance(obj, TerraformManagedResource):
            self.managed_resources[name] = obj
        elif isinstance(obj, TerraformModuleCall):
            self.module_calls[name] = obj
        elif isinstance(obj, TerraformOutput):
            self.outputs[name] = obj
        elif isinstance(obj, TerraformRequiredProvider):
            self.required_providers[name] = obj
        elif isinstance(obj, TerraformVariable):
            self.variables[name] = obj
        else:
            raise ExtensionError("could not add child")

    @property
    def empty(self) -> bool:
        return not bool(self.children)

    @property
    def children(self) -> list["TerraformObjectBase"]:
        return (
            list(self.data_resources.values())
            + list(self.managed_resources.values())
            + list(self.module_calls.values())
            + list(self.outputs.values())
            + list(self.required_providers.values())
            + list(self.variables.values())
        )

    @property
    def docstring(self) -> str | None:
        if hasattr(self, "_docstring"):
            return self._docstring

        result = []
        for filename in self.config.tfdoc_module_docstring_files:
            fullpath = os.path.join(self.root, self.path, filename)
            if os.path.exists(fullpath):
                with open(fullpath, "r") as f:
                    lines = f.readlines()
                in_comment = False
                for line in lines:
                    line = line.lstrip()
                    if not in_comment:
                        if _should_ignore(self.config, line):
                            continue
                        if line.startswith("#"):
                            in_comment = True
                            result.append(line[1:].rstrip("\n"))
                    else:
                        if _should_ignore(self.config, line):
                            continue
                        if line.startswith("#"):
                            result.append(line[1:].rstrip("\n"))
                        else:
                            break
                if result:
                    break

        if not result:
            return None

        result += [""]
        self._docstring = "\n".join(_strip_leading_spaces(result))
        return self._docstring


class TerraformObjectBase:
    kind: str = "base"

    def __init__(self, config: Config, module: TerraformModule, data: dict):
        self.config = config
        self.module = module
        self.data = data

    @property
    def filename(self) -> str:
        return self.data["pos"]["filename"]

    @property
    def line(self) -> int:
        return self.data["pos"]["line"] - 1

    @property
    def template(self) -> str:
        return self.kind

    @property
    def docstring(self) -> str | None:
        if hasattr(self, "_docstring"):
            return self._docstring

        with open(self.filename, "r") as f:
            lines = f.readlines()

        result = []
        if self.line != 0:
            for line in reversed(lines[: self.line]):
                line = line.lstrip()
                if _should_ignore(self.config, line):
                    continue
                if line.startswith("#"):
                    result.append(line[1:].rstrip("\n"))
                    continue
                break

        if not result:
            return None

        result = list(reversed(result))
        result += [""]
        self._docstring = "\n".join(_strip_leading_spaces(result))
        return self._docstring


class TerraformVariable(TerraformObjectBase):
    kind = "variable"

    def __init__(self, config: Config, module: TerraformModule, key: str, data: dict):
        super().__init__(config, module, data)
        self.name = key

    def __str__(self) -> str:
        return f"tf:variable {self.name}"

    @property
    def type(self) -> str:
        lines = self.data["type"].split("\n")
        lines = [line if idx == 0 else line[2:] for idx, line in enumerate(lines)]
        return "\n".join(lines)

    @property
    def default(self) -> str:
        default = self.data.get("default")
        if default is None:
            default = "null"
        else:
            default = json.dumps(default, indent=2)
        return default

    @property
    def required(self) -> bool:
        return self.data["required"]


class TerraformOutput(TerraformObjectBase):
    kind = "output"

    def __init__(self, config: Config, module: TerraformModule, key: str, data: dict):
        super().__init__(config, module, data)
        self.name = key

    def __str__(self) -> str:
        return f"tf:output {self.name}"


class TerraformManagedResource(TerraformObjectBase):
    kind = "managed_resource"

    def __init__(self, config: Config, module: TerraformModule, key: str, data: dict):
        super().__init__(config, module, data)
        self.kind = ".".join(key.split(".")[0:-1])
        self.name = data["name"]

    def __str__(self) -> str:
        return f"tf:resource {self.kind} {self.name}"

    @property
    def resource_type(self):
        return self.data["type"]


class TerraformDataResource(TerraformObjectBase):
    kind = "data_resource"

    def __init__(self, config: Config, module: TerraformModule, key: str, data: dict):
        super().__init__(config, module, data)
        self.kind = ".".join(key.split(".")[1:-1])
        self.name = data["name"]

    def __str__(self) -> str:
        return f"tf:data {self.kind} {self.name}"

    @property
    def resource_type(self):
        return self.data["type"]


class TerraformModuleCall(TerraformObjectBase):
    kind = "module_call"

    def __init__(self, config: Config, module: TerraformModule, key: str, data: dict):
        super().__init__(config, module, data)
        self.name = key
        self.source = os.path.relpath(
            os.path.normpath(
                os.path.join(os.path.dirname(data["pos"]["filename"]), data["source"])
            ),
            self.module.root,
        )

    def __str__(self) -> str:
        return f"tf:module_call {self.name} {self.source}"


class TerraformRequiredProvider(TerraformObjectBase):
    kind = "required_provider"

    def __init__(self, config: Config, module: TerraformModule, key: str, data: dict):
        super().__init__(config, module, data)
        self.name = key
        self.provider = key

    def __str__(self) -> str:
        return f"tf:provider {self.provider}"

    @property
    def docstring(self) -> str | None:
        return None

    @property
    def source(self) -> str | None:
        return self.data.get("source", None)

    @property
    def version_constraints(self) -> str | None:
        s = self.data.get("version_constraints", [])
        if not s:
            return None
        return ", ".join(s)


TF_OBJ_MAP = {cls.kind: cls for cls in TerraformObjectBase.__subclasses__()}


class TerraformStore:
    def __init__(self, config: Config):
        self.modules: dict[str, TerraformModule] = {}
        self.config = config

    def load(self, dirs: list[str], recursive: bool = True) -> bool:
        found_paths = set()
        if recursive:
            for scan_dir in dirs:
                for root, _, _ in os.walk(scan_dir):
                    found_paths.add((scan_dir, os.path.relpath(root, scan_dir)))
        else:
            for scan_dir in dirs:
                found_paths.add((os.path.dirname(scan_dir), os.path.basename(scan_dir)))

        for root, path in status_iterator(
            found_paths,
            bold("[tfdoc] Loading Data "),
            "darkgreen",
            len(found_paths),
            stringify_func=(lambda x: os.path.join(*x)),
        ):
            fullpath = os.path.join(root, path)
            data = json.loads(
                subprocess.check_output(
                    ["terraform-config-inspect", "--json", fullpath]
                )
            )
            if not data:
                continue
            module = TerraformModule(self.config, path, root)
            for obj in self.create_objects(module, data):
                module.add_child(obj.name, obj)
            if module.empty:
                continue
            self.modules[module.name] = module

        return True

    def create_objects(self, module: TerraformModule, data: dict):
        for kind, cls in TF_OBJ_MAP.items():
            for key, item in data[f"{kind}s"].items():
                obj = cls(self.config, module, key, item)
                yield obj

    def dump(self) -> None:
        for _, mod in self.modules.items():
            print(mod)
            for child in mod.children:
                print(f"  {child}")
