{% macro ref(model_name=None, name=None, version=None) %}
  {% set the_name = model_name or name %}
  {% set rel = builtins.ref(the_name) %}
  {% do return(rel.include(database=False)) %}
{% endmacro %}

{% macro source(source_name, table_name) %}
  {% set rel = builtins.source(source_name, table_name) %}
  {% do return(rel.include(database=False)) %}
{% endmacro %}
