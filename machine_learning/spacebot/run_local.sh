#!/bin/bash

# Fail immediately on error (eg. build failure).
set -e

SERVER_TARGET=//machine_learning/spacebot:server
CLIENT_TARGET=//machine_learning/spacebot:client

SERVER_EXECUTABLE=bazel-bin/machine_learning/spacebot/server
CLIENT_EXECUTABLE=bazel-bin/machine_learning/spacebot/client

# Get port number if it's been provided
if [ $# -eq 1 ]; then
  SPACEBOT_PORT=$1
fi

# Build the targets
bazel build $SERVER_TARGET
bazel build $CLIENT_TARGET

# Start server and get its PID
$SERVER_EXECUTABLE $SPACEBOT_PORT &
SERVER_PID=$!
echo Server running with pid: $SERVER_PID

# Allow server time to start up. Adjust as necessary.
sleep 2

# Start client
$CLIENT_EXECUTABLE $SPACEBOT_PORT

# Once client has finished, kill the server
kill -SIGINT $SERVER_PID

# Wait for server to finish
wait $SERVER_PID
