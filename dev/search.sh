#!/bin/bash
set -euo pipefail

curl 'http://localhost:9200/hello/example/_search' | jq .
