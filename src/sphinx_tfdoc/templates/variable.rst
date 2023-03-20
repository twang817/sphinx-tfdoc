{% extends "base.rst" %}

{% block field_list %}
:Type:
    .. code-block::

{{ item.type | indent(8) }}
{% if item.default != "null" %}

:Default:
       .. code-block::

{{ item.default | indent(8) }}
{% endif %}


{% endblock field_list %}
