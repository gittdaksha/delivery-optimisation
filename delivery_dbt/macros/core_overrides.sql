{% macro ref(model_name, version=None) %}
  {% set rel = builtins.ref(model_name) %}
  {% do return(rel.include(database=False)) %}
{% endmacro %}

{% macro source(source_name, model_name) %}
  {% set rel = builtins.source(source_name, model_name) %}
  {% do return(rel.include(database=False)) %}
{% endmacro %}
