from work_queue import WorkQueue

# Gossip
GOSSIP = True
#GOSSIP = False

# Constants
MIN_PEERS = 5
MAX_PEERS = 15
QUERY_TIME = 100
ROUND_TIME = 10
STOP_TIME = 250
NUM_SEEDS = 1 # number of seeds that we start with

# File Parameters
NUM_PIECES = 100
PIECE_SIZE = 40 # in bits

# Create the main event queue.
wq = WorkQueue()

# Create the main node dictionary.
nodes = {}

# Have lists of removed nodes
haves = {}
