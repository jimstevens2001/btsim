import random

from work_queue import WorkQueue, WorkQueueException

#Node States - not sure if this should be in the node class

#Node class to contain explicit copies of the bit field and peer lists
class Node:
	def __init__(self, node_id):
		self.id = node_id
		self.peers = [] # Current set of peers that are not unchoked.
		self.unchoked = [] # set of unchoked peers this list should never have more than 5 things in it
		self.min_peers = 5
		self.max_peers = 15
		self.desired_peers = random.randint(self.min_peers, self.max_peers)
		self.op_unchoke = 0 # will be id of current optomistically unchoked peer
		self.unchoke_count = 0 # number of times we've tried to unchoke this peer, try 3 times then switch
		self.curr_up = [] # Values to keep track of current upload resources being spent, indexed by node id
		self.curr_down = [] # Values to keep track of current download resources being spent, indexed by node id

		# don't care about any of thie for now
		#=================================================
		# self.cur_blocks = [] # Current blocks held by the node.
		# self.want_blocks = [] # Blocks node is interested in.
		# self.gossip = [] # Recent gossip messages recieved (to be passed on when possible) - not sure about this
		# self.max_up = 100 # Default maximum upload speed
		# self.max_down = 100 # Default maximum download speed
		# self.altruism = leave # Current altruism setting
		#=================================================

	def add_peer(self, node_id):
		self.desired_peers = self.desired_peers-1 # right now we don't need this
		self.peers.append(node_id)

	def remove_peer(self, node_id):
		self.peers.remove(node_id)
		self.desired_peers = self.desired_peers+1

	def get_peers(self):
		# Get a list of all the nodes that we are not peers with.
		all_nodes = nodes.keys()
		all_nodes.remove(self.id)
		[all_nodes.remove(i) for i in self.peers]

		# Randomly decide how many peers we desire right now.
		self.desired_peers = random.randint(self.min_peers, self.max_peers)
		print 'node',self.id,'(',len(self.peers),'peers ) is querying the tracker and now wants at least',self.desired_peers

		# If we already have at least desired_peers, then there is nothing to do.
		if len(self.peers) >= self.desired_peers:
			#print 'but we are already at max'
			return

		# Otherwise, get more peers until we have desired_peers (or there are none left to get).
		num_peers = min([self.desired_peers-len(self.peers), len(all_nodes)])

		for i in range(num_peers):
			done = False
			while not done:
			#print 'all_nodes',all_nodes
				if all_nodes != []:
					new_peer = random.choice(all_nodes);
				else:
					break

				all_nodes.remove(new_peer)

				if len(nodes[new_peer].peers) < nodes[new_peer].max_peers:
				        #print nodes
				        #print node_id,'and',new_peer,'are now peers'
					nodes[new_peer].add_peer(self.id)
					self.add_peer(new_peer)
					done = True

	
	# unchoking process
	# there might be a much simpler way to do this, I was really tired when I wrote it
	def update_unchoke(self):
		#first clear the set of unchoked peers
		for i in unchoked:
			self.peers.append(i)
			self.unchoked:remove(i)

		#first take care of the optimistic unchoke
		self.update_op_unchoke()

		#find the top four uploaders among your peers
		first = second = third = fourth = 0
		for i in curr_down:
			if(i > first):
				fourth = third
				third = second
				second = first
				first = i
			elif(i > second):
				fourth = third
				third = second
				second = i
			elif(i > third):
				fourth = third
				third = i
			elif(i > fourth):
				fourth = i

		#update unchoked set with the new top four peers
		self.unchoked.append(self.curr_down.index(first))
		self.unchoked.append(self.curr_down.index(second))
		self.unchoked.append(self.curr_down.index(third))
		self.unchoked.append(self.curr_down.index(fourth))


	# I guess this could've just been included in the unchoking process
	# this should get called every 10 seconds
	def update_op_unchoke(self):	
		if self.op_unchoke == 0: # first time we're here
			self.op_unchoke = random.choice(self.peers)
			self.unchoked.append(self.op_unchoke)
			self.peers.remove(self.op_unchoke)
			self.unchoke_count = 1
		elif self.unchoke_count < 4:
			self.unchoke_count = self.unchoke_count + 1
		else:
			self.unchoked.remove(self.op_unchoke) # if he uploaded enough, he should get selected as
			                                      # one of the four unchoked peers this round
			self.peers.append(self.op_unchoke)
			self.op_unchoke = random.choice(self.peers)
			self.unchoked.append(self.op_unchoke)
			self.peers.remove(self.op_unchoke)
			self.unchoke_count = 1	
			


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
	nodes[node_id] = Node(node_id)

	# Get peers for it.
	nodes[node_id].get_peers()

	# Schedule the first update_peers event.
	wq.enqueue([wq.cur_time + QUERY_TIME, UPDATE_PEERS, node_id])

def update_peers(event):
	node_id = event[2]
	nodes[node_id].get_peers()

	# Schedule the next update_peers event.
	wq.enqueue([wq.cur_time + QUERY_TIME, UPDATE_PEERS, node_id])	


for i in range(100,0, -1):
	x = random.randint(0, 100) + i
	wq.enqueue([x, ADD_NODE, i])
wq.enqueue([200, KILL_SIM])

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
