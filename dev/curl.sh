#!/bin/bash
set -euo pipefail

curl -s 'http://localhost:9200/my_index/my_type/_search' -d@- | jq .
