import random
import sys

from node import Node
from globals import *

# Event format is: [time, type, X, ...] (X and ... can be anything and is determined by the type)
# Time must be non-negative integer.
# Type must be a string and is used to call event handler function.


# Define event Handlers

def add_node(event):
	node_id = event[2]

	# Add the new node to the nodes dictionary.
	nodes[node_id] = Node(node_id)

	# Get peers for it.
	nodes[node_id].get_peers()

	# Schedule the first update_peers event.
	wq.enqueue([wq.cur_time + QUERY_TIME, 'UPDATE_PEERS', node_id])

def update_peers(event):
	node_id = event[2]
	nodes[node_id].get_peers()

	# Schedule the next update_peers event.
	wq.enqueue([wq.cur_time + QUERY_TIME, 'UPDATE_PEERS', node_id])

# when a node leaves the swarm
def remove_node(event):
	node_id = event[2]

	# remove the node from all the peer and unchoked lists of the other nodes
	for i in len(nodes):
		nodes[i].remove_peer(node_id)
	
	# will need to cancel any pieces that we had expect to be downloaded from this node 
	
	# remove the node from the node list
	nodes.remove(node_id)

# Use this to update each peers download and upload rates per round and to decide 
# also includes the unchoke algorithm at the beginning
def exchange_round(event):
	node_id = event[2]

	# if we need more peers, get them
	if (len(nodes[node_id].peers)+len(nodes[node_id].unchoked)) < nodes[node_id].desired_peers:
		nodes[node_id].get_peers()

	# run the unchoke algorithm
	nodes[node_id].update_unchoke();

	# let peers know that they're being uploaded to and how much
	
	# compute completed pieces

	# Schedule the next update_peers event.
	wq.enqueue([wq.cur_time + QUERY_TIME, 'EXCHANGE_ROUND', node_id])


def kill_sim(event):
	print 'KILL_SIM event at time',event[0]
	print wq.wq
	sys.exit(0)
	


# Register event handlers

handlers = {}
handlers['ADD_NODE'] = add_node 		# Param: node_id
handlers['UPDATE_PEERS'] = update_peers 	# Param: node_id
handlers['REMOVE_NODE'] = remove_node		# Param: node_id
handlers['EXCHANGE_ROUND'] = exchange_round 	# Param: node_id
#handlers['NEXT_DL'] = next_dl 			# used to schedule additional piece downloads on fast peers
handlers['KILL_SIM'] = kill_sim			# No param

