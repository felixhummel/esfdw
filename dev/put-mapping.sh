#!/bin/bash
set -euo pipefail

curl -s -XPUT "http://localhost:9200/my_index" -d @- <<'EOF'
{
  "mappings": {
    "my_type": {
      "properties": {
        "some_id": { "type": "integer" },
        "my_string": { "type": "text" },
        "foo": { "type": "text" },
        "my_nested": { "type": "nested" },
        "my_list": { "type": "text" }
      }
    }
  }
}
EOF
echo
