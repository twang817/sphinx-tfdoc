{% block directive %}
.. tf:{{ directive }}:: {{ module.name }}.{{ name }}

{% endblock directive %}
{% filter indent(4) %}
    {% block contents %}
        {% block field_list %}
        {% endblock field_list %}
        {% block docstring %}
            {% if item.docstring %}
{{ item.docstring }}

            {% endif %}
        {% endblock docstring %}
    {% endblock contents %}
{% endfilter %}
