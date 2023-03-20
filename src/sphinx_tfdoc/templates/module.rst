{{ module.name }}
{{ "-" * module.name | length }}

.. tf:module:: {{ module.name }}

{% filter indent(4) %}
{{ module.docstring }}

Required Providers
^^^^^^^^^^^^^^^^^^
{% with directive = "required_provider" %}
{% for name, item in module.required_providers.items() %}
{% include "required_provider.rst" %}
{% endfor %}
{% endwith %}

Called Modules
^^^^^^^^^^^^^^
{% with directive = "module_call" %}
{% for name, item in module.module_calls.items() %}
{% include "module_call.rst" %}
{% endfor %}
{% endwith %}

Variables
^^^^^^^^^
{% with directive = "variable" %}
{% for name, item in module.variables.items() %}
{% include "variable.rst" %}
{% endfor %}
{% endwith %}

Resources
^^^^^^^^^
{% with directive = "managed_resource" %}
{% for name, item in module.managed_resources.items() %}
{% include "managed_resource.rst" %}
{% endfor %}
{% endwith %}

Data Resources
^^^^^^^^^^^^^^
{% with directive = "data_resource" %}
{% for name, item in module.data_resources.items() %}
{% include "data_resource.rst" %}
{% endfor %}
{% endwith %}

Outputs
^^^^^^^
{% with directive = "output" %}
{% for name, item in module.outputs.items() %}
{% include "output.rst" %}
{% endfor %}
{% endwith %}
{% endfilter %}
