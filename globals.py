from work_queue import WorkQueue

# Constants
MIN_PEERS = 5
MAX_PEERS = 60
DESIRED_PEERS = 30
QUERY_TIME = 100
ROUND_TIME = 10
STOP_TIME = 250
NUM_SEEDS = 1 # number of seeds that we start with

# File Parameters
NUM_PIECES = 1000
PIECE_SIZE = 40 # in bits

# Create the main event queue.
wq = WorkQueue()

# Create the main node dictionary.
nodes = {}

# Have lists of removed nodes
haves = {}

# LOG FILES
# would like to be set this from the command line
# but its not necessary right now
file_progress_file = 'Records/file_progress_record_1000'
local_file = 'Records/local_record_1000'
global_file = 'Records/global_record_1000'
distance_file = 'Records/distance_record_1000'
piece_count_file = 'Records/rarity_record_1000'

#Disabled Logs
#======================================
#can_fill_file = 'can_fill_record'
#peers_file = 'peers_record'
#curr_down_file = 'curr_down_record'
#curr_up_file = 'curr_up_record'
#interest_file = 'interest_record'
#priority_file = 'priority_record'
#want_file = 'want_record'
#======================================
