from work_queue import WorkQueue

# Simulation parameters

# Gossip
GOSSIP = True
#GOSSIP = False

#How gossip messages are generated and handled
#Options: priority, peering, all
GOSSIP_STYLE = 'priority'


# Specify whether to use global knowledge or not
#GLOBAL_KNOWLEDGE = False
GLOBAL_KNOWLEDGE = True


# Distance Calculation
#Options: normal, top_ten, weighted
DISTANCE_MODE = 'normal'

# Set altruism for leechers
#LEECHER_ALTRUISM = 'eternal_seed'
LEECHER_ALTRUISM = 'leave_on_complete'

# Set number of nodes
NUM_NODES = 100

########################################################################################3

# Constants
MIN_PEERS = 5
MAX_PEERS = 60
DESIRED_PEERS = 30
ROUND_TIME = 10
NUM_SEEDS = 1

# File Parameters
NUM_PIECES = 1000
PIECE_SIZE = 40 # in KB

# Create the main event queue.
wq = WorkQueue()

# Create the main node dictionary.
nodes = {}

# Create the run times dictionary.
run_time = {}

# LOG FILES
# would like to be set this from the command line
# but its not necessary right now
file_progress_file = 'Records/file_progress_20globalh'
local_file = 'Records/local_view_20globalh'
global_file = 'Records/global_view_20globalh'
distance_file = 'Records/distance_20globalh'
piece_count_file = 'Records/piece_count__20globalh'
curr_down_file = 'Records/curr_down_test'


