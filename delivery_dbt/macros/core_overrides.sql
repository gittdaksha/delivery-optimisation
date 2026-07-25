{% macro ref() %}
  {{ return(builtins.ref(*varargs, **kwargs)) }}
{% endmacro %}
