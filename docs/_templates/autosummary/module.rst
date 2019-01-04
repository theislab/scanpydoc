:github_url: {{ fullname | github_url }}

{{ fullname | escape | underline }}

.. automodule:: {{ fullname }}
.. currentmodule:: {{ fullname }}

Functions
---------

{% for function in functions %}
{%- if not function.startswith('_') %}
.. autofunction:: {{ function }}
{%- endif -%}
{%- endfor %}
