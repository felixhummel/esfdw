DROP FOREIGN TABLE IF EXISTS hello;

CREATE FOREIGN TABLE hello (
  _id TEXT,
  some_id INTEGER,
  my_string TEXT OPTIONS (es_property 'my_string'),
  foo TEXT,
  my_nested TEXT,
  my_list TEXT,
  nested_string TEXT OPTIONS (es_property 'my_nested.string'),
  nested_integer TEXT OPTIONS (es_property 'my_nested.integer'),
  nested_as_json JSON OPTIONS (es_property 'my_nested')
) SERVER es_srv OPTIONS (
  index 'my_index',
  doc_type 'my_type',
  debug 'true',
  loglevel 'DEBUG'
);
