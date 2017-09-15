#!/bin/bash
set -euo pipefail

# run this from the project root!
container=$(docker-compose ps -q postgres)
diff tests/integration/expected <(cat sql/select.sql | docker exec -i --user postgres $container psql --no-align --tuples-only)
