{% extends "base.rst" %}

{% block field_list %}
{% if item.source %}
:Source: ``{{ item.source }}``
{% endif %}
{% if item.version_constraints %}
:Version: ``{{ item.version_constraints }}``
{% endif %}


{% endblock field_list %}
