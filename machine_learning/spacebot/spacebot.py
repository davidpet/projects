import sys
import grpc
import time
from concurrent import futures
from threading import Thread, Event

from machine_learning.spacebot.server import InMemorySpaceBotServer
from machine_learning.spacebot.client import TerminalSpaceBotClient

from machine_learning.spacebot import spacebot_pb2_grpc

# TODO: put common stuff for future chatbots into common library

# TODO: docstrings
# TODO: type hint cleanup
# TODO: tests (cheese historian failure case)(Really? failure case)
# TODO: lint errors
# TODO: README (multiple levels) & update/clarify dependencies for different sub-projects

# TODO: contribute some evals to get GPT 4 access and see if that fixes the prompt injection issues
# (https://github.com/openai/evals)

# TODO: consider getting multiple choices for prompt and using those (instead of re-fetch)
# TODO: consider making an enum for role in messages
# TODO: consider making message a proto for py and ts to share

# TODO: start a real bug/task list in GitHub for anything not done on check-in
# TODO: future: make angular client & put client+server on google cloud


DEFAULT_PORT = '50051'

CLIENT_SIDE_SERVER = 'localhost'
SERVER_SIDE_SERVER = 'localhost'


def main(port: str) -> int:
    # Create a shared event for controlling the server thread.
    server_should_exit = Event()

    # Start server in a separate thread.
    server_thread = Thread(target=run_server, args=(server_should_exit,port))
    server_thread.start()
    time.sleep(1)

    # Create and run client
    client = TerminalSpaceBotClient(f'{CLIENT_SIDE_SERVER}:{port}')
    client.initialize()
    if client.valid:
        retcode = client.run()
    else:
        retcode = 1

    # Signal the server thread to exit and wait for it to do so.
    server_should_exit.set()
    server_thread.join()

    return retcode

def run_server(should_exit, port):
    # Create a gRPC server
    grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    server = InMemorySpaceBotServer(grpc_server)
    
    # Add the servicer to the server
    spacebot_pb2_grpc.add_SpaceBotServiceServicer_to_server(server, grpc_server)

    # Listen on a port
    grpc_server.add_insecure_port(f'{SERVER_SIDE_SERVER}:{port}')

    # Start the server
    grpc_server.start()
    try:
        while not should_exit.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        grpc_server.stop(0)

if __name__ == "__main__":
    port = DEFAULT_PORT
    if len(sys.argv) > 1:
        port = sys.argv[1]
    
    sys.exit(main(port))
