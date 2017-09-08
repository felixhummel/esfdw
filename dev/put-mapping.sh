#!/bin/bash
set -euo pipefail

curl -s -XPUT "http://localhost:9200/hello" -d @- <<'EOF'
{
  "mappings": {
    "hello": {
      "properties": {
        "some_id": { "type": "integer" },
        "my_string": { "type": "text" },
        "foo": { "type": "text" },
        "my_nested": { "type": "object" },
        "my_list": { "type": "text" }
      }
    }
  }
}
EOF
