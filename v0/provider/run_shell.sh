#!/usr/bin/env bash

# Trap exit and kill the server (not to leave orphaned Python processes)
trap 'kill $SERVER_PID' EXIT

# Start the server in the background
python shell.py run >/dev/null & SERVER_PID=($!)

# Create a file descriptor to capture output from 'read' command
exec 5>&1

while true
do
    OUTPUT=$(python shell.py read | tee /dev/fd/5)
    if [[ $OUTPUT ]]
    then
      python shell.py write
    else
      # No output from 'read' means the Python process has exited
      break
    fi
done
