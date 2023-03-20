{{ module.name }}
{{ "-" * module.name | length }}

.. tf:module:: {{ module.name }}

{% filter indent(4) %}
{% if module.docstring %}
{{ module.docstring }}
{% endif %}

{% if module.required_providers.items() | length > 0 %}
Required Providers
^^^^^^^^^^^^^^^^^^
{% with directive = "required_provider" %}
{% for name, item in module.required_providers.items() %}
{% include "required_provider.rst" %}
{% endfor %}
{% endwith %}
{% endif %}

{% if module.module_calls.items() | length > 0 %}
Called Modules
^^^^^^^^^^^^^^
{% with directive = "module_call" %}
{% for name, item in module.module_calls.items() %}
{% include "module_call.rst" %}
{% endfor %}
{% endwith %}
{% endif %}

{% if module.variables.items() | length > 0 %}
Variables
^^^^^^^^^
{% with directive = "variable" %}
{% for name, item in module.variables.items() %}
{% include "variable.rst" %}
{% endfor %}
{% endwith %}
{% endif %}

{% if module.managed_resources.items() | length > 0 %}
Resources
^^^^^^^^^
{% with directive = "managed_resource" %}
{% for name, item in module.managed_resources.items() %}
{% include "managed_resource.rst" %}
{% endfor %}
{% endwith %}
{% endif %}

{% if module.data_resources.items() | length > 0 %}
Data Resources
^^^^^^^^^^^^^^
{% with directive = "data_resource" %}
{% for name, item in module.data_resources.items() %}
{% include "data_resource.rst" %}
{% endfor %}
{% endwith %}
{% endif %}

{% if module.outputs.items() | length > 0 %}
Outputs
^^^^^^^
{% with directive = "output" %}
{% for name, item in module.outputs.items() %}
{% include "output.rst" %}
{% endfor %}
{% endwith %}
{% endif %}
{% endfilter %}
