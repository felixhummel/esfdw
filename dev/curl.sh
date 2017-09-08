#!/bin/bash
set -euo pipefail

curl -s 'http://localhost:9200/hello/example/_search' -d@- | jq .
