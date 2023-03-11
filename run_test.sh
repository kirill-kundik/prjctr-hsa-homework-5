#!/bin/bash

concurrency=(10 25 50 100 150 250)
total_tests=${#concurrency[@]}
siege_location=./siege

echo "\nRunning all siege tests"
echo "Each test will run for 180 seconds with different concurrency levels"
echo "Siege folder with urls.txt and output logs: $siege_location"
echo "Total $total_tests tests: ${concurrency[*]} concurrency levels"
echo "It will require at least $((total_tests * 180)) seconds to run all tests"

for c in ${concurrency[@]}; do
  echo "Running $c concurrency test"
  siege -c$c -d1 -i -q -t180s --content-type "application/json" --file=$siege_location/urls.txt --log=$siege_location/${c}_test.log
done

echo "Successfully finished benchmarking"
