from work_queue import WorkQueue

# Constants
MIN_PEERS = 5
MAX_PEERS = 15
QUERY_TIME = 100
ROUND_TIME = 10

# File Parameters
NUM_PIECES = 100
PIECE_SIZE = 100 # in bits

# Create the main event queue.
wq = WorkQueue()

# Create the main node dictionary.
nodes = {}
