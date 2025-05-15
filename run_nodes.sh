#!/bin/bash

# Start three nodes in the background
NODE_ID=node_1 /usr/local/bin/python3 main.py &
NODE_ID=node_2 /usr/local/bin/python3 main.py &
NODE_ID=node_3 /usr/local/bin/python3 main.py &

# Wait for all background processes
wait 