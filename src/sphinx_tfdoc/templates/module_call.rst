.. tf:module_call:: {{ module.name }}.{{ name }}

{% filter indent(4, first=True) %}
   :Source: ``{{ item.source }}``

{% if item.docstring %}
{{ item.docstring }}

{% endif %}
{% endfilter %}
