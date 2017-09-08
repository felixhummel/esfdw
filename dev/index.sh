#!/bin/bash
set -euo pipefail

put() {
  curl -s -XPUT "http://localhost:9200/hello/example/$1" -d @- | jq .
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
  ]
}
EOF

echo
