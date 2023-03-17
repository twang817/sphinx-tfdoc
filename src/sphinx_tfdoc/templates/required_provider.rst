.. tf:required_provider:: {{ module.name }}.{{ name }}

{% filter indent(4, first=True) %}
{% if item.source | length > 0 %}
:Source: ``{{ item.source }}``
{% endif %}
{% if item.version_constraints | length > 0 %}
:Version: ``{{ item.version_constraints }}``
{% endif %}
{% include module.name + "/required_provider_" + name + ".rst" ignore missing %}
{{ item.docstring }}
{% endfilter %}
