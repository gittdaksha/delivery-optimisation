{% macro ref(name, version=None) %}
  {% set rel = builtins.ref(name) %}
  {% do return(rel.include(database=False)) %}
{% endmacro %}

{% macro source(source_name, table_name) %}
  {% set rel = builtins.source(source_name, table_name) %}
  {% do return(rel.include(database=False)) %}
{% endmacro %}
