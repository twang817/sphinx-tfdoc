# sphinx-tfdoc

Terraform documentation support in Sphinx.

Inspired by [sphinx-terraform][1] and [sphinx-autoapi][2] sphinx-tfdoc documents
Terraform modules by using [terraform-config-inspect][3] to scan and parse
docstrings from Terraform files.

# Installation

```
pip install sphinx-tfdoc
```

# Quickstart

1. Use pip to install `sphinx-tfdoc`
2. Install [terraform-config-inspect][3]
3. Add `sphinx-tfdoc` to your conf.py
4. Set `tfdoc_dirs` to the root folder contain your Terraform modules
5. Run `make html`

# How it works

sphinx-tfdoc scans your Terraform module directories using
[terraform-conig-inspect][3] and uses Jinaj2 templates to generate RST
documentation for each of your modules.

The documentation can be customized by modifying the Jinja2 templates.  By
default, sphinx-tfdoc will pull docstrings for your variables, resources, and
outputs and include them into your rst documentation.

The rst documentation uses a custom Terraform Domain that allows you to
reference Terraform objects.  The custom roles follow the format:

```
:tf:<object_type>:`<module_name>.<object_name>`
```

For example, to refer to a variable "name" in the a module "vpc", you use the
role `` :tf:variable:`vpc.name` ``.

For resources, the object name is the Terraform identifier.  For example, given
the following resource:

```
resource aws_s3_bucket "data" {
    bucket = "my-data-bucket"
}
```

Assuming that this resource exists inside a module "etl", the role to reference
this resource would be `` :tf:resource:`etl.data` ``.

[1]: https://gitlab.com/cblegare/sphinx-terraform
[2]: https://github.com/readthedocs/sphinx-autoapi
[3]: https://github.com/hashicorp/terraform-config-inspect
