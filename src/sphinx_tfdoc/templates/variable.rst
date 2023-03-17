.. tf:variable:: {{ module.name }}.{{ name }}

{% filter indent(4, first=True) %}
:Type:
    .. code-block::

{{ item.type | indent(8, first=True) }}
{% if item.default != "null" %}

:Default:
       .. code-block::

{{ item.default | indent(8, first=True) }}
{% endif %}

{% if item.docstring %}
{{ item.docstring }}

{% endif %}
{% endfilter %}
