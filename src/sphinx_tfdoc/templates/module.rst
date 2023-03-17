{{ module.name }}
{{ "-" * module.name | length }}

.. tf:module:: {{ module.name }}

{% filter indent(4, first=True) %}
{{ module.docstring }}
{% endfilter %}

Required Providers
^^^^^^^^^^^^^^^^^^
{% for name, item in module.required_providers.items() %}
{% include "required_provider.rst" %}
{% endfor %}

Called Modules
^^^^^^^^^^^^^^
{% for name, item in module.module_calls.items() %}
{% include "module_call.rst" %}
{% endfor %}

Variables
^^^^^^^^^
{% for name, item in module.variables.items() %}
{% include "variable.rst" %}
{% endfor %}

Resources
^^^^^^^^^
{% for name, item in module.managed_resources.items() %}
{% include "managed_resource.rst" %}
{% endfor %}

Data Resources
^^^^^^^^^^^^^^
{% for name, item in module.data_resources.items() %}
{% include "data_resource.rst" %}
{% endfor %}

Outputs
^^^^^^^
{% for name, item in module.outputs.items() %}
{% include "output.rst" %}
{% endfor %}
