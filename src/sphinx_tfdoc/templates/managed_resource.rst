.. tf:managed_resource:: {{ module.name }}.{{ name }}

{% filter indent(4, first=True) %}
{% if item.docstring %}
{{ item.docstring }}

{% endif %}
{% endfilter %}
