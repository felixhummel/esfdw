#!/bin/bash
set -euo pipefail

here="$(readlink -m $(dirname $0))"

# run this from the project root!
container=$(docker-compose ps -q postgres)


for sqlfile in $here/*.sql; do
  testcase=$(basename -s.sql $sqlfile)
  expected=$here/$testcase.expected
  echo $testcase
  echo ===============================
  # epic generation of expected files
  # cat $sqlfile | docker exec -i --user postgres $container psql --no-align --tuples-only > $expected
  diff $expected <(cat $sqlfile | docker exec -i --user postgres $container psql --no-align --tuples-only)
  echo OK
done

