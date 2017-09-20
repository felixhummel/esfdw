DROP FOREIGN TABLE IF EXISTS hello;

CREATE FOREIGN TABLE hello (
  _id TEXT,
  some_id INTEGER,
  my_string TEXT OPTIONS (es_property 'my_string'),
  foo TEXT,
  my_nested TEXT,
  my_list TEXT OPTIONS (list_separator '|'),
  my_array TEXT[] OPTIONS (es_property 'my_list'),
  different_sep TEXT OPTIONS (es_property 'my_list'),
  my_nested_string TEXT OPTIONS (es_property 'my_nested.string'),
  my_nested_integer TEXT OPTIONS (es_property 'my_nested.integer'),
  my_nested_as_json JSON OPTIONS (es_property 'my_nested'),
  list_with_objects TEXT
) SERVER es_srv OPTIONS (
  index 'my_index',
  doc_type 'my_type',
  debug 'true',
  loglevel 'DEBUG'
);
