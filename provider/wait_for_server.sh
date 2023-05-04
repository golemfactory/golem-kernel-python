#! /bin/bash

until [ -f output/server_status.txt ]
do
  sleep 1
  echo "Waiting for server" >> output/kernel_server_log.txt
done
echo "Server ready" >> output/kernel_server_log.txt
exit
