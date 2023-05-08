#! /bin/bash

until [ -f workdir/kernel_status.txt ]
do
  sleep 1
  echo "Waiting for kernel" >> workdir/kernel_server_log.txt
done
echo "Kernel ready" >> workdir/kernel_server_log.txt
exit
