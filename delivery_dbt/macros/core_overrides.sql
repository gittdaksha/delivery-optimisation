{% macro ref(model_name, version=None) %}
  {{ return(builtins.ref(model_name, version=version)) }}
{% endmacro %}
