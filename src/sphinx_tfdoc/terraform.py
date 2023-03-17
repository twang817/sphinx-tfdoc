from typing import Any

from docutils import nodes, utils
from docutils.parsers.rst import directives
from docutils.statemachine import StringList
from sphinx import addnodes
from sphinx.addnodes import desc_signature
from sphinx.directives import ObjectDescription
from sphinx.domains import Domain, ObjType
from sphinx.locale import _
from sphinx.util.typing import OptionSpec


class TerraformObjectDirective(ObjectDescription[str]):
    option_spec: OptionSpec = {
        "noindex": directives.flag,
    }

    def handle_signature(self, sig: str, signode: desc_signature) -> str:
        self.sig_type = self.name.split(":")[-1]

        if self.sig_type == "module":
            module_name = sig
        else:
            module_name, sig = sig.rsplit(".", 1)

        self.module = self.env.tfdoc_store.modules[module_name]
        if self.sig_type != "module":
            self.obj = getattr(self.module, f"{self.sig_type}s")[sig]

        sig_type_name = self.sig_type
        if self.sig_type == "managed_resource":
            sig_type_name = "resource"
        elif self.sig_type == "data_resource":
            sig_type_name = "data"
        elif self.sig_type == "required_provider":
            sig_type_name = "required provider"
        elif self.sig_type == "module_call":
            sig_type_name = "called module"

        signode += addnodes.desc_annotation(sig_type_name, sig_type_name)

        if self.sig_type in ("data_resource", "managed_resource"):
            signode += addnodes.desc_addname(
                self.obj.resource_type, self.obj.resource_type
            )
            signode += addnodes.desc_sig_literal_char(".", ".")

        signode += addnodes.desc_name(sig, sig)

        if self.sig_type == "variable":
            if not self.obj.required:
                signode += addnodes.desc_optional("optional", "optional")
            else:
                signode += addnodes.desc_optional("required", "required")

        return sig

    # def transform_content(self, contentnode: addnodes.desc_content) -> None:
    #     if self.sig_type == "module":
    #         obj = self.module
    #     else:
    #         obj = self.obj

    #     if self.sig_type != "module" and self.sig_type != "required_provider":
    #         docstring = obj.docstring
    #         if self.env.app:
    #             self.env.app.emit(
    #                 "autodoc-process-docstring",
    #                 "object",
    #                 obj.name,
    #                 obj,
    #                 self.options,
    #                 docstring,
    #             )
    #         document = utils.new_document(
    #             f"{obj.filename}#L{obj.line - len(obj.docstring)}-L{obj.line}",
    #             self.state.document.settings,
    #         )

    #         self.state.nested_parse(
    #             StringList(
    #                 docstring,
    #                 source=obj.filename,
    #             ),
    #             self.content_offset,
    #             document,
    #         )
    #         contentnode.extend(document.children)


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
        "module": TerraformObjectDirective,
        "data_resource": TerraformObjectDirective,
        "managed_resource": TerraformObjectDirective,
        "module_call": TerraformObjectDirective,
        "output": TerraformObjectDirective,
        "required_provider": TerraformObjectDirective,
        "variable": TerraformObjectDirective,
    }
    roles: dict[str, Any] = {}
    indicies: dict[str, Any] = {}
    initial_data: dict[str, dict[str, tuple[Any]]] = {
        "objects": {},
        "modules": {},
    }
