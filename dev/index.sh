#!/bin/bash
set -euo pipefail

curl -XPUT 'http://localhost:9200/hello/example/1' -d @dev/example.json
echo
