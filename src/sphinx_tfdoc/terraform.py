from typing import Any, cast, NamedTuple

from docutils import nodes
from docutils.nodes import Element
from docutils.parsers.rst import directives
from sphinx import addnodes
from sphinx.addnodes import desc_signature, pending_xref
from sphinx.builders import Builder
from sphinx.directives import ObjectDescription
from sphinx.domains import Domain, ObjType
from sphinx.environment import BuildEnvironment
from sphinx.locale import _
from sphinx.roles import XRefRole
from sphinx.util.logging import getLogger
from sphinx.util.nodes import make_id, make_refnode
from sphinx.util.typing import OptionSpec

from .store import TerraformModule, TerraformObjectBase


logger = getLogger(__name__)


class TerraformObjectDirective(ObjectDescription[tuple[str, str, str]]):
    option_spec: OptionSpec = {
        "noindex": directives.flag,
        "noindexentry": directives.flag,
        "nocontentsentry": directives.flag,
    }

    tfobj: TerraformModule | TerraformObjectBase | None = None

    @property
    def display_name(self):
        return self.objtype

    @property
    def module_name(self):
        if isinstance(self.tfobj, TerraformModule):
            return self.tfobj.name
        return self.tfobj.module.name

    def get_tf_object(self, sig: str) -> None:
        module_name, name = sig.rsplit(".", 1)
        module = self.env.tfdoc_store.modules[module_name]
        self.tfobj = getattr(module, f"{self.objtype}s")[name]

    def get_signature_name_prefix(self, sig: str) -> list[nodes.Node]:
        return []

    def get_signature_suffix(self, sig: str) -> list[nodes.Node]:
        return []

    def handle_signature(
        self, sig: str, signode: desc_signature
    ) -> tuple[str, str, str]:
        self.get_tf_object(sig)

        signode += addnodes.desc_annotation(self.display_name, self.display_name)
        signode += addnodes.desc_sig_space()

        signode += self.get_signature_name_prefix(sig)
        signode += addnodes.desc_name(self.tfobj.name, self.tfobj.name)

        signode += self.get_signature_suffix(sig)

        return self.module_name, self.display_name, self.tfobj.name

    def add_target_and_index(
        self, name: tuple[str, str, str], sig: str, signode: desc_signature
    ) -> None:
        module_name, objtype, objname = name
        fullname = ".".join([module_name, objtype.replace(" ", "_"), objname])

        node_id = make_id(self.env, self.state.document, objtype, objname)
        signode["ids"].append(node_id)
        self.state.document.note_explicit_target(signode)

        domain = cast(TerraformDomain, self.env.get_domain("tf"))
        domain.note_object(fullname, objtype, node_id, signode)

        if "noindexentry" not in self.options:
            indextext = self.get_index_text(module_name, objname)
            if indextext:
                self.indexnode["entries"].append(
                    ("single", indextext, node_id, "", None)
                )

    def get_index_text(self, module_name: str, objname: str):
        return f"{objname} ({self.objtype} in module {module_name})"


class TerraformModuleDirective(TerraformObjectDirective):
    @property
    def module_name(self):
        return self.tfobj.name

    def get_tf_object(self, sig: str) -> None:
        self.tfobj = self.env.tfdoc_store.modules[sig]

    def get_index_text(self, module_name: str, objname: str):
        return f"{objname} ({self.objtype})"


class TerraformManagedResourceDirective(TerraformObjectDirective):
    display_name = "resource"

    def get_signature_name_prefix(self, sig: str) -> list[nodes.Node]:
        return [
            addnodes.desc_sig_keyword(
                self.tfobj.resource_type, self.tfobj.resource_type
            ),
            addnodes.desc_sig_literal_char(".", "."),
        ]


class TerraformDataResourceDirective(TerraformManagedResourceDirective):
    display_name = "data"


class TerraformRequiredProviderDirective(TerraformObjectDirective):
    display_name = "required provider"


class TerraformModuleCallDirective(TerraformObjectDirective):
    display_name = "called module"


class TerraformVariableDirective(TerraformObjectDirective):
    def get_signature_suffix(self, sig: str) -> list[nodes.Node]:
        if not self.tfobj.required:
            return addnodes.desc_optional("optional", "optional")
        else:
            return addnodes.desc_optional("required", "required")


class TerraformOutputDirective(TerraformObjectDirective):
    pass


class TerraformXRefRole(XRefRole):
    pass


class ObjectEntry(NamedTuple):
    docname: str
    node_id: str
    objtype: str


class TerraformDomain(Domain):
    name: str = "tf"
    label: str = "Terraform"
    object_types: dict[str, ObjType] = {
        "data_resource": ObjType(_("data_resource"), "data_resource"),
        "managed_resource": ObjType(_("managed_resource"), "managed_resource"),
        "module_call": ObjType(_("module_call"), "module_call"),
        "output": ObjType(_("output"), "output"),
        "required_provider": ObjType(_("required_provider"), "required_provider"),
        "variable": ObjType(_("variable"), "variable"),
    }
    directives: dict[str, type[TerraformObjectDirective]] = {
        "module": TerraformModuleDirective,
        "data_resource": TerraformDataResourceDirective,
        "managed_resource": TerraformManagedResourceDirective,
        "module_call": TerraformModuleCallDirective,
        "output": TerraformOutputDirective,
        "required_provider": TerraformRequiredProviderDirective,
        "variable": TerraformVariableDirective,
    }
    roles: dict[str, Any] = {
        "variable": TerraformXRefRole(),
        "resource": TerraformXRefRole(),
        "output": TerraformXRefRole(),
        "data": TerraformXRefRole(),
        "required_provider": TerraformXRefRole(),
        "called_module": TerraformXRefRole(),
        "module": TerraformXRefRole(),
    }
    indicies: dict[str, Any] = {}
    initial_data: dict[str, dict[str, tuple[Any]]] = {
        "objects": {},
        "modules": {},
    }

    @property
    def objects(self) -> dict[str, ObjectEntry]:
        return self.data.setdefault("object", {})

    def note_object(self, name: str, objtype: str, node_id: str, location: Any = None):
        if name in self.objects:
            logger.warning(f"duplicate object description of {name}")
        self.objects[name] = ObjectEntry(self.env.docname, node_id, objtype)

    def resolve_xref(
        self,
        env: BuildEnvironment,
        fromdocname: str,
        builder: Builder,
        type: str,
        target: str,
        node: pending_xref,
        contnode: Element,
    ) -> Element | None:
        if type == "module":
            fullname = ".".join([target, type, target])
            title = ".".join([type, target])
        else:
            module, name = target.split(".")
            fullname = ".".join([module, type, name])
            title = fullname
        if fullname in self.objects:
            obj = self.objects[fullname]
            return make_refnode(
                builder, fromdocname, obj.docname, obj.node_id, contnode, title
            )
        else:
            names = "\n".join(list(self.objects.keys()))
            logger.warning(f"could not resolve {fullname} among {names}")
