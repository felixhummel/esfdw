DROP FOREIGN TABLE IF EXISTS hello;

CREATE FOREIGN TABLE hello (
  my_string text
) SERVER es_srv OPTIONS (
  index 'hello',
  doc_type 'example',
  debug 'true'
);
