#!/bin/bash
set -euo pipefail

put() {
  curl -s -XPUT "http://localhost:9200/my_index/my_type/$1" -d @- | jq .
}

id=1
put $id <<'EOF'
{
  "some_id": 1,
  "my_string": "Hello World 1!",
  "foo": "bar",
  "my_nested": {
    "string": "bar 1",
    "integer": 10
  },
  "my_list": [
    "one",
    "another"
  ],
  "list_with_objects": [
    {"a": 1, "b": "doc1-b1"},
    {"a": 2, "b": "doc1-b2"}
  ]
}
EOF

id=2
put $id <<'EOF'
{
  "some_id": 2,
  "my_string": "Hello World 2!",
  "foo": "bar",
  "my_nested": {
    "string": "bar 2",
    "integer": 20
  },
  "my_list": [
    "two",
    "another"
  ],
  "list_with_objects": [
    {"a": 1, "b": "doc1-b1"},
    {"a": 2, "b": "doc1-b2"},
    {"something": {"completely": "different"}}
  ]
}
EOF

echo
