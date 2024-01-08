{# https://raw.githubusercontent.com/sphinx-doc/sphinx/master/sphinx/ext/autosummary/templates/autosummary/module.rst #}
{% extends "!autosummary/module.rst" %}

{% block classes %}
{% if classes -%}
Classes
-------

{%- for class in classes -%}
{%- if not class.startswith('_') %}
.. autoclass:: {{ class }}
   :members:
{%- endif -%}
{%- endfor -%}
{%- endif %}
{% endblock %}

{% block functions %}
{% if functions -%}
Functions
---------

{%- for function in functions -%}
{%- if not function.startswith('_') and not function.startswith('example_') %}
.. autofunction:: {{ function }}
{%- endif -%}
{%- endfor -%}
{%- if functions | select('search', '^example_') | first %}

Examples
--------

{%- for function in functions -%}
{%- if function.startswith('example_') %}
.. autofunction:: {{ function }}
{%- endif -%}
{%- endfor -%}
{%- endif -%}
{%- endif %}
{% endblock %}
