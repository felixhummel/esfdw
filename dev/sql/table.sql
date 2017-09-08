DROP FOREIGN TABLE IF EXISTS hello;

CREATE FOREIGN TABLE hello (
  some_id INTEGER,
  my_string TEXT,
  my_nested TEXT,
  my_list TEXT

) SERVER es_srv OPTIONS (
  index 'hello',
  doc_type 'example',
  debug 'true',
  loglevel 'DEBUG'
);
