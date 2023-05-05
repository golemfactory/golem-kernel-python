#! /bin/bash

until [ -f workdir/server_status.txt ]
do
  sleep 1
  echo "Waiting for server" >> workdir/kernel_server_log.txt
done
echo "Server ready" >> workdir/kernel_server_log.txt
exit
