import random

from work_queue import WorkQueue, WorkQueueException

#Node States - not sure if this should be in the node class

#Node class to contain explicit copies of the bit field and peer lists
class Node:
	def __init__(self):
		self.cur_blocks = [] # Current blocks held by the node.
		self.want_blocks = [] # Blocks node is interested in.
		self.peers = [] # Current set of peers.
		self.min_peers = 5
		self.max_peers = 15
		self.desired_peers = random.randint(self.min_peers, self.max_peers)

		# don't care about any of thie for now
		#=================================================
		# self.gossip = [] # Recent gossip messages recieved (to be passed on when possible) - not sure about this
		# self.max_up = 100 # Default maximum upload speed
		# self.max_down = 100 # Default maximum download speed
		# self.altruism = leave # Current altruism setting
		# self.curr_up = 0 # Value to keep track of current upload resources being spent
		# self.curr_down = 0 # Value to keep track of current download resources being spent
		#=================================================

	def add_peer(self, node_id):
		
		self.peers.append(node_id)

	def remove_peer(self, 

	


# Event format is: [time, type, X, ...] (X and ... can be anything and is determined by the type)
# Time must be non-negative integer.
# Type must be a string.

# Create the main event queue.
wq = WorkQueue()

# Create the main node dictionary.
nodes = {}

# Events:
# add_node: Additional parameters (id)
ADD_NODE = 'add_node'
UPDATE_PEERS = 'update_peers'
KILL_SIM = 'kill_sim'

# Constants
MIN_PEERS = 5
MAX_PEERS = 15
QUERY_TIME = 100


def add_node(event):
	node_id = event[2]

	# Add the new node to the nodes dictionary.
	nodes[node_id] = {'peers': []}

	# Get peers for it.
	get_peers(node_id)

	# Schedule the first update_peers event.
	wq.enqueue([wq.cur_time + QUERY_TIME, UPDATE_PEERS, node_id])

def update_peers(event):
	node_id = event[2]
	get_peers(node_id)

	# Schedule the next update_peers event.
	wq.enqueue([wq.cur_time + QUERY_TIME, UPDATE_PEERS, node_id])


def get_peers(node_id):
	# Get out peers.
	peers = nodes[node_id]['peers']

	# Get a list of all the nodes that we are not peers with.
	all_nodes = nodes.keys()
	all_nodes.remove(node_id)
	[all_nodes.remove(i) for i in peers]

	# Randomly decide how many peers we desire right now.
	desired_peers = random.randint(MIN_PEERS, MAX_PEERS)
	print 'node',node_id,'(',len(peers),'peers ) is querying the tracker and now wants at least',desired_peers

	# If we already have at least desired_peers, then there is nothing to do.
	if len(peers) >= desired_peers:
		return

	# Otherwise, get more peers until we have desired_peers (or there are none left to get).
	num_peers = min([desired_peers-len(peers), len(all_nodes)])

	for i in range(num_peers):
		done = False
		while not done:
			#print 'all_nodes',all_nodes
			if all_nodes != []:
				new_peer = random.choice(all_nodes);
			else:
				break

			all_nodes.remove(new_peer)

			if len(nodes[new_peer]['peers']) < MAX_PEERS:
				#print nodes
				#print node_id,'and',new_peer,'are now peers'
				nodes[new_peer]['peers'].append(node_id)
				peers.append(new_peer)
				done = True
	nodes[node_id]['peers'] = peers

		
	
	


for i in range(100,0, -1):
	x = random.randint(0, 100) + i
	wq.enqueue([x, ADD_NODE, i])
wq.enqueue([10000, KILL_SIM])

# Main queue loop
while not wq.empty():
	cur_event = wq.dequeue()

	print 'Current event is',cur_event[1],'at time',wq.cur_time

	event_type = cur_event[1]

	if event_type == ADD_NODE:
		add_node(cur_event)
	elif event_type == UPDATE_PEERS:
		update_peers(cur_event)
	elif event_type == KILL_SIM:
		print 'KILL_SIM event at time',cur_event[0]
		break
	else:
		print 'Invalid event type'
		break

#print nodes

print wq.wq

print 'Done'
