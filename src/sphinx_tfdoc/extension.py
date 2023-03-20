import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from sphinx.addnodes import toctree
from sphinx.application import Sphinx
from sphinx.errors import ExtensionError
from sphinx.util.console import darkgreen, bold
from sphinx.util.logging import getLogger
from sphinx.util import status_iterator
from tabulate import tabulate

from .store import TerraformStore
from .terraform import TerraformDomain


logger = getLogger(__name__)


def rst_tabulate(rows):
    table = [rows]
    return tabulate([rows], tablefmt="grid")


def custom_indent(s: str, width: int) -> str:
    lines = s.splitlines()
    lines = [" " * width + line if len(line) else line for line in lines]
    return "\n".join(lines)


def tfdoc_init(app: Sphinx) -> None:
    if not app.config.tfdoc_dirs:
        raise ExtensionError("You must configure the `tfdoc_dirs` setting")
    dirs = app.config.tfdoc_dirs
    if isinstance(dirs, str):
        dirs = [dirs]
    dirs = [
        d if os.path.abspath(d) else os.path.normpath(os.path.join(app.srcdir, d))
        for d in dirs
    ]
    for d in dirs:
        if not os.path.exists(d):
            raise ExtensionError(f"tfdoc dir `{d}` not found")

    target_dir = os.path.normpath(os.path.join(app.srcdir, app.config.tfdoc_target))
    os.makedirs(target_dir, exist_ok=True)

    template_paths = []
    template_dir = app.config.tfdoc_template_dir
    if template_dir:
        if not os.path.isdir(template_dir):
            template_dir = os.path.join(app.srcdir, template_dir)
        template_paths.append(template_dir)
    template_paths.append((Path(__file__).parent / "templates").absolute())

    store = TerraformStore(app.config)
    if store.load(dirs, recursive=app.config.tfdoc_recursive):
        env = Environment(
            loader=FileSystemLoader(template_paths),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )
        env.globals["tabulate"] = rst_tabulate
        env.globals["config"] = app.config
        env.globals["path_exists"] = os.path.exists
        env.filters["indent"] = custom_indent
        for key, module in status_iterator(
            store.modules.items(),
            bold("[tfdoc] Rendering Modules "),
            "darkgreen",
            len(store.modules),
            stringify_func=(lambda x: x[0]),
        ):
            template = env.get_template(f"{module.template}.rst")
            rendered = template.render(module=module)
            module_path = os.path.join(target_dir, module.name)
            os.makedirs(module_path, exist_ok=True)
            with open(f"{module_path}/index.rst", "w") as f:
                f.write(rendered)

        with open(f"{target_dir}/index.rst", "w") as f:
            template = env.get_template("index.rst")
            rendered = template.render(
                modules=sorted(store.modules.values(), key=lambda x: x.name)
            )
            f.write(rendered)

    app.env.tfdoc_store = store


def doctree_read(app: Sphinx, doctree) -> None:
    if app.env.docname == "index":
        nodes = list(doctree.traverse(toctree))
        if not nodes:
            return
        for node in nodes:
            for entry in node["entries"]:
                if entry[1].startswith(app.config.tfdoc_target):
                    return
        nodes[-1]["entries"].append((None, f"{app.config.tfdoc_target}/index"))
        nodes[-1]["includefiles"].append(f"{app.config.tfdoc_target}/index")


def setup(app: Sphinx) -> dict:
    app.setup_extension("sphinx.ext.napoleon")
    app.connect("builder-inited", tfdoc_init)
    app.connect("doctree-read", doctree_read)
    logger.info(bold("[tfoc] adding domain ") + darkgreen("TerraformDomain"))
    app.add_config_value("tfdoc_dirs", [], "env")
    app.add_config_value("tfdoc_recursive", True, "env")
    app.add_config_value("tfdoc_template_dir", None, "env")
    app.add_config_value("tfdoc_target", "tfdoc", "env")
    app.add_config_value("tfdoc_module_docstring_files", [], "env")
    app.add_config_value("tfdoc_docstring_ignores", [], "env")
    #app.add_config_value("tfdoc_auto_common_doc", True, "env")
    #app.add_config_value("tfdoc_common_doc_dir", [], "env")
    app.add_domain(TerraformDomain)

    return {
        "version": "0.1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
