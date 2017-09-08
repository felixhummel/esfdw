#!/bin/bash
set -euo pipefail

curl -s -XDELETE "http://localhost:9200/my_index"
echo
