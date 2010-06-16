from work_queue import WorkQueue
import sys #not sure if this is going to do what I want it to do...

# Simulation parameters

# Gossip
#GOSSIP = True
GOSSIP = False

#How gossip messages are generated and handled
#Options: priority, peering, all
GOSSIP_STYLE = 'priority'

# Specify the knowledge mode to use
# Options: local, global, omni
KNOWLEDGE_MODE = 'local'

# Distance Calculation
# Options: normal, top_ten, weighted
DISTANCE_MODE = 'normal'

# Set altruism for leechers
# LEECHER_ALTRUISM = 'eternal_seed'
LEECHER_ALTRUISM = 'leave_on_complete'

# Set number of nodes
NUM_NODES = 100

# If NO_SEED_TEST is true, there will be no seed
# and instead the file will be distributed among the leecers.
#NO_SEED_TEST = True
NO_SEED_TEST = False

# If SEED_LEAVE_TEST is true, the seed will leave at some random time
SEED_LEAVE_TEST = True
#SEED_LEAVE_TEST = False

# Set number of peers
MAX_PEERS = 10
DESIRED_PEERS = 5

# Seed Speed
SEED_SPEED = [100,100]

########################################################################################

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
local_file = 'Records/local_view_unbalanced275gos3'
global_file = 'Records/global_view_unbalanced275gos3'
distance_file = 'Records/distance_unbalanced275gos3'
piece_count_file = 'Records/piece_count_unbalanced275gos3'
#curr_down_file = 'Records/curr_down_full_gossip_100u'
#priority_list_file = 'Records/priority_list_full_gossip_100u'

LOAD_RATES = False
SEED_LEAVE = 1250

if len(sys.argv) > 4:
	outfile = str(sys.argv[1])
	statefile = str(sys.argv[2])
	# check to see if the state file is what we're reading from or writing to
	if str(sys.argv[3]) == 'True':
		LOAD_RATES = True
	SEED_LEAVE = int(sys.argv[4])
if len(sys.argv) > 3:
	outfile = str(sys.argv[1])
	statefile = str(sys.argv[2])
	# check to see if the state file is what we're reading from or writing to
	if str(sys.argv[3]) == 'True':
		LOAD_RATES = True		
if len(sys.argv) > 2:
	outfile = str(sys.argv[1])
	statefile = str(sys.argv[2])
elif len(sys.argv) > 1:
	outfile = str(sys.argv[1])
	statefile = 'temp'
else:
    outfile = 'Records/out'
    statefile = 'temp'
