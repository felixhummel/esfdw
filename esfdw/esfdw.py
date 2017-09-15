from datetime import datetime
import json
import logging
import re

from multicorn import ForeignDataWrapper, ANY, ALL
from multicorn.utils import log_to_postgres

import elasticsearch
from elasticsearch.helpers import scan

from .es_helper import MatchList, get_bool_query


class ESForeignDataWrapper(ForeignDataWrapper):

    # https://github.com/Kozea/Multicorn/blob/master/python/multicorn/__init__.py#L147
    # These operators and negated variants (prefixed with a '!') can be
    # offloaded to ElasticSearch.
    _PUSHED_DOWN_OPERATORS = ['=', '<>', '~~', '<@', '<', '>', '<=', '>=']

    # How many results should be returned in response to a single scroll request.
    # A lower value increases the number of round trips to the ElasticSearch
    # server to fetch the data.
    # A higher value increases the memory pressure on the ElasticSearch client
    # node issuing the search.
    _SCROLL_SIZE = 5000

    # How long a consistent view of the index should be maintained for scrolled
    # search. The default is 5 minutes.
    # This should be greater than the time it takes for an ES query to complete.
    # On the other hand, unnecessarily high values needlessly increase the load
    # on the cluster.
    _SCROLL_LENGTH = '5m'

    def __init__(self, options, columns):
        super(ESForeignDataWrapper, self).__init__(options, columns)
        self._esclient = None
        self._options = options
        # dict mapping column_name to column_definition
        self._columns = columns
        self._doc_type = options['doc_type']
        # debug and logging
        self._loglevel = getattr(logging, options.get('loglevel', 'INFO'))
        self._logs = []
        self._debug = options.get('debug', None) == 'true'
        if self._debug:
            self.log('debug enabled! This generates very much output on the server.', level=logging.WARNING)

    def _column_to_es_field(self, column):
        options = self._columns[column].options
        if 'es_property' in options:
            self.debug('got es_property for "%s": "%s"' %(column, str(options['es_property'])))
            return options['es_property']
        return column

    def log(self, msg, level=None):
        self._logs.append(str(msg))

    def debug(self, *msgs):
        if self._debug:
            msg = ' '.join(map(str, msgs))
            print('DEBUG-esfdw: %s' % msg)

    def _flush_logs(self):
        result = '\n    >>> '.join(self._logs)
        log_to_postgres('\n    >>> ' + result, self._loglevel)

    @property
    def esclient(self):
        if self._esclient is None:
            params = {}
            if 'hostname' in self._options:
                params['host'] = self._options['hostname']
            if 'port' in self._options:
                params['port'] = self._options['port']
            self._esclient = elasticsearch.Elasticsearch([params])
        return self._esclient

    def get_index(self, _quals):
        """Get the ElasticSearch index or indices to query.

        By default, we obtain the index from the foreign table options.
        However, this method can be overridden to derive the index from the query
        quals. For example, the `timestamp` qual could be used to select one or
        more time-based indices.
        """
        return self._options['index']

    def _endpoint_to_datetime(self, endpoint):
        # When dealing with date and time ranges, we get a string formatted as
        # %Y-%m-%d %H:%M:%S(.%f)?
        valid_time_formats = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f']
        for fmt in valid_time_formats:
            try:
                return datetime.strptime(endpoint, fmt)
            except ValueError:
                pass
        # No expected time formats matched, so no conversion
        return endpoint

    def _append_filter(self, filter_list, field, operator, value):
        if operator == '=':
            if value is None:
                filter_list.append_missing(field)
            else:
                filter_list.append_term(field, value)
        elif operator == '<>':
            if value is None:
                filter_list.append_exists(field)
            else:
                filter_list.append_term(field, value, not_value=True)
        elif operator == '~~':
            # LIKE operator
            if value.find('%') == len(value) - 1 and '_' not in value:
                filter_list.append_prefix(field, value[:-1])
            else:
                value = re.escape(value).replace(
                    r'\%', '.*').replace(r'\_', '.')
                filter_list.append_filter({'regexp': {field: value}})
        elif operator == '<@':
            # range operator
            # value looks something like ["start","end")
            # (including quotation marks when dealing with date strings)
            def _format_endpoint(endpoint):
                endpoint = self._endpoint_to_datetime(endpoint)
                if isinstance(endpoint, datetime):
                    return endpoint.strftime('%Y-%m-%dT%H:%M:%S.%f')
                return endpoint

            start, end = value.split(',')
            if start[0] == '[':
                start_op = 'gte'
            else:
                start_op = 'gt'
            start = start[1:].replace('"', '')

            if end[-1] == ']':
                end_op = 'lte'
            else:
                end_op = 'lt'
            end = end[:-1].replace('"', '')

            params = {
                start_op: _format_endpoint(start),
                end_op: _format_endpoint(end)
            }
            filter_list.append_range(field, **params)
        elif operator in ('<', '<=', '>', '>='):
            operator_map = {
                '<': 'lt',
                '<=': 'lte',
                '>': 'gt',
                '>=': 'gte'
            }
            params = {
                operator_map[operator]: value
            }
            filter_list.append_range(field, **params)

    def _normalize_operator(self, operator, value):
        negation = False
        if operator[0] == '!':
            # Negative operators are handled as their positive counterparts
            # but are added to the must_not list.
            operator = operator[1:]
            negation = True
        if operator == '<>' and value is not None:
            # Generally handle a not-equals in the must_not list.
            # IS NOT NULL, which is passed down to us as '<> None', is handled
            # as a `missing` filter in the must_list.
            operator = '='
            negation = True
        return operator, negation

    def _process_qual(self, must_list, must_not_list, field, operator, value):
        operator, negation = self._normalize_operator(operator, value)
        if operator in self._PUSHED_DOWN_OPERATORS:
            filter_list = must_not_list if negation else must_list
            self._append_filter(filter_list, field, operator, value)

    def _make_match_lists(self, quals):
        must_list = MatchList()
        must_not_list = MatchList()
        for qual in quals:
            field = self._column_to_es_field(qual.field_name)
            if qual.list_any_or_all == ANY:
                if qual.operator[0] == '=':
                    must_list.append_terms(field, qual.value)
                else:
                    match_list = MatchList()
                    operator, negation = self._normalize_operator(
                        qual.operator[0], True)
                    for elem in qual.value:
                        self._append_filter(match_list, field, operator, elem)
                    if negation:
                        # a <> any(x, y, z) => a <> x or a <> y or a <> z =>
                        # not (a = x and a = y and a = z)
                        must_not_list.append_filter({'and': match_list})
                    else:
                        must_list.append_filter({'or': match_list})
            elif qual.list_any_or_all == ALL:
                if qual.operator[0] == '<>':
                    # a <> all(x, y, z) => a <> x and a <> y and a <> z => not
                    # (a = x or a = y or a = z)
                    must_not_list.append_terms(field, qual.value)
                else:
                    for elem in qual.value:
                        self._process_qual(
                            must_list, must_not_list, field, qual.operator[0], elem)
            else:
                self._process_qual(
                    must_list,
                    must_not_list,
                    field,
                    qual.operator,
                    qual.value)
        return must_list, must_not_list

    def execute(self, quals, columns, _sortkeys=None):
        must_list, must_not_list = self._make_match_lists(quals)
        if must_list or must_not_list:
            query = get_bool_query(
                must_list=must_list,
                must_not_list=must_not_list)
        else:
            query = {}
        query['_source'] = [self._column_to_es_field(
            column) for column in columns]
        self.debug('query: %s' % json.dumps(query))
        self._flush_logs()
        for result in scan(
                self.esclient,
                query=query,
                index=self.get_index(quals),
                doc_type=self._doc_type,
                size=self._SCROLL_SIZE,
                scroll=self._SCROLL_LENGTH):
            self.debug('result: %s' % result)
            obs = result.get('_source', {})
            self.debug('obs: %s' % obs)

            row = {}
            for column_name in columns:
                field = self._column_to_es_field(column_name)
                column_type_name = self._columns[column_name].type_name
                self.debug('coldata: %s' % str({
                    'column_type_name': column_type_name,
                    'field': field,
                    'options': self._columns[column_name].options
                }))
                if column_name == '_id':
                    # `_id` is special in that it's always present in the top-level
                    # result, not under `fields`.
                    val = result['_id']
                    continue
                # handle nested fields
                if '.' in field:
                    val = self._get_nested(obs, field)
                else:
                    val = obs.get(field, None)
                if isinstance(val, list):
                    separator = self._get_column_option(column_name, 'list_separator', ',')
                    val = separator.join([str(x) for x in val])
                # val here can be scalar or still nested
                # if it is defined as JSON, dump it
                if column_type_name == 'json':
                    val = json.dumps(obs)
                row[column_name] = val
            yield row

    def _get_column_option(self, column_name, option, default=None):
        return self._columns[column_name].options.get(option, default)

    @staticmethod
    def _get_nested(nested_dict, field):
        """
        Given a nested dict and a dot-separated field path, returns the value
        at this path or None if the path does not exist, e.g.:

        >>> _get_nested({"foo": {"bar": "baz"}}, 'foo.bar')
        "baz"
        """
        print(nested_dict, field)
        keys = field.split('.')
        current = nested_dict
        for k in keys:
            print('key', k, 'current', current)
            # return None for nested fields without a value in this doc
            if not k in current:
                current = None
                break
            current = current[k]
        print('wtf', current)
        return current

    def get_rel_size(self, quals, columns):
        must_list, must_not_list = self._make_match_lists(quals)
        if must_list or must_not_list:
            query = get_bool_query(
                must_list=must_list,
                must_not_list=must_not_list)
        else:
            query = {}
        query['size'] = 0
        results = self.esclient.search(
            index=self.get_index(quals),
            body=query,
            doc_type=self._doc_type)
        return (results['hits']['total'], len(columns) * 100)
