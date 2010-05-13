from work_queue import WorkQueue

# Simulation parameters

# Gossip
#GOSSIP = True
GOSSIP = False

#How gossip messages are generated and handled
#Options: priority, peering, all
GOSSIP_STYLE = 'all'


# Specify whether to use global knowledge or not
GLOBAL_KNOWLEDGE = False
#GLOBAL_KNOWLEDGE = True


# Distance Calculation
#Options: normal, top_ten, weighted
DISTANCE_MODE = 'normal'

# Set altruism for leechers
#LEECHER_ALTRUISM = 'eternal_seed'
LEECHER_ALTRUISM = 'leave_on_complete'

# Set number of nodes
NUM_NODES = 100

# If NO_SEED_TEST is true, there will be no seed
# and instead the file will be distributed among the leecers.
NO_SEED_TEST = True
#NO_SEED_TEST = False

# Set number of peers
MAX_PEERS = 20
DESIRED_PEERS = 10

########################################################################################3

# Constants

MIN_PEERS = 5
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
#file_progress_file = 'Records/file_progress_full_gossip_100u'
local_file = 'Records/local_view_full_gossip_100u'
global_file = 'Records/global_view_full_gossip_100u'
distance_file = 'Records/distance_full_gossip_100u'
piece_count_file = 'Records/piece_count_full_gossip_100u'
#curr_down_file = 'Records/curr_down_full_gossip_100u'
#priority_list_file = 'Records/priority_list_full_gossip_100u'
