CREATE SERVER es_srv FOREIGN DATA WRAPPER multicorn OPTIONS (
  wrapper 'esfdw.ESForeignDataWrapper',
  hostname 'elasticsearch',
  port '9200'
);
