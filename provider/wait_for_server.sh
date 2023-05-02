#! /bin/bash

until [ -f output/server_status.txt ]
do
  sleep 1
  echo "Waiting for server" >> output/log.txt
done
echo "Server ready" >> output/log.txt
exit
