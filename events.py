import random
import sys

from node import Node
from globals import *

# Event format is: [time, type, X, ...] (X and ... can be anything and is determined by the type)
# Time must be non-negative integer.
# Type must be a string and is used to call event handler function.

class EventException(Exception): pass


# Define event Handlers

def add_node(event):
	node_id = event[2]

	# Add the new node to the nodes dictionary.
	nodes[node_id] = Node(node_id)

	print 'Added node',node_id,'at',event[0]
	print

	# Run the initial exchange_round for this node
	exchange_round(event)

	# Get peers for it.
	#nodes[node_id].get_peers(event[0])

	# generate the priority_list for our set of peers
	#nodes[node_id].sort_priority() # since we get new peers each round, this will also update the list each round

	# Schedule the first update_peers event.
	#wq.enqueue([wq.cur_time + ROUND_TIME, 'EXCHANGE_ROUND', node_id])

def update_peers(event):
	node_id = event[2]
	nodes[node_id].get_peers(event[0])

	# Schedule the next update_peers event.
	wq.enqueue([wq.cur_time + QUERY_TIME, 'UPDATE_PEERS', node_id])

# when a node leaves the swarm
def remove_node(event):
	node_id = event[2]

	# remove the node from all the peer and unchoked lists of the other nodes
	for i in nodes:
		nodes[i].remove_peer(node_id)

	# find all events for this node and remove them from the work queue
	wq.remove(node_id)
	
	# will need to cancel any pieces that we had expect to be downloaded from this node 
	
	# remove the node from the node list
	del nodes[node_id]
	print 'Removed node',node_id,'at',event[0]
	print

# Use this to update each peers download and upload rates per round and to decide 
# also includes the unchoke algorithm at the beginning
def exchange_round(event):
	node_id = event[2]

	# if we need more peers, get them
	if (len(nodes[node_id].peers)+len(nodes[node_id].unchoked)) < nodes[node_id].desired_peers:
		nodes[node_id].get_peers(event[0])

	# generate the priority_list for our set of peers
	nodes[node_id].sort_priority() # since we get new peers each round, this will also update the list each round

	# run the unchoke algorithm
	nodes[node_id].update_unchoke(event[0]);

	# let peers know that they're being uploaded to and how much
	up_rate = nodes[node_id].max_up / 5
	for i in nodes[node_id].unchoked:
		nodes[i].curr_down[node_id] = up_rate
		nodes[node_id].curr_up[i] = up_rate		
	
	# compute completed pieces
	for i in nodes[node_id].unchoked:
		exchange_time = ROUND_TIME
		while exchange_time != 0:
			# zero the recent piece field, it shouldn't matter between rounds
			nodes[i].recent_piece = 0

			# choose a random piece to upload
			# first make of list of everything that we have that they want
			can_fill = []
			for j in nodes[i].want_pieces:
				if j in nodes[node_id].have_pieces:
					can_fill.append(j)
			if can_fill != []:	
				piece_index = random.randint(0, len(can_fill))
				piece = nodes[i].want_pieces[piece_index]

				# if its small enough to get in one round then remove it from the want list
				# and add it to the have list
				transfer_rate =  min(nodes[i].remain_down, up_rate)
				if piece < (transfer_rate*exchange_time):
					# *BIG QUESTION* does download bandwidth get split between downloads?
					nodes[i].remain_down =  nodes[i].remain_down - (piece/exchange_time)
					del nodes[i].want_pieces[piece_index]
					# maybe we should store the time the piece is finished in the have list instead of the size of the piece
					finish_time = piece/transfer_rate # this should come out in seconds
					nodes[i].have_pieces[piece_index] = finish_time + event[0]
					exchange_time = exchange_time - finish_time
				# otherwise subtract the amount that we can get from the piece size and leave
				# it in the want list
				else:
					nodes[i].want_pieces[piece_index] = nodes[i].want_pieces[piece_index] - (transfer_rate*exchange_time)
					nodes[i].remain_down = max(0, (nodes[i].remain_down - transfer_rate))
					exchange_time = 0
			else:
				break
		
	# Schedule the next update_peers event.
	wq.enqueue([wq.cur_time + ROUND_TIME, 'EXCHANGE_ROUND', node_id])


def kill_sim(event):
	print 'KILL_SIM event at time',event[0]
	print wq.get_queue()
	sys.exit(0)


def log(event):
	time = event[0]
	log_type = event[2]
	if log_type == 'time':
		print 'LOG Time=',time
	elif log_type == 'wq':
		print 'LOG Time=',time
		print 'Work Queue ='
		print wq.get_queue()
	elif log_type == 'nodes':
		print 'LOG Time=',time
		print 'Nodes ='
		print nodes.keys()
	elif log_type == 'peers':
		print 'LOG Time=',time
		print 'Peers ='
		peers = {}
		for i in nodes:
			peers[i] = nodes[i].peers
		print peers
	elif log_type == 'file_progress':
		node_id = event[3]
		print 'LOG Time=',time
		print 'Node ',node_id,'s File Progress:'
		for i in nodes[node_id].have_pieces:
			print 'Piece ',i,'was finished at ',nodes[node_id].have_pieces[i]
	elif log_type == 'priority_queue':
		node_id = event[3]
		print 'LOG Time=',time
		print 'Priority list for node',node_id,'is'
		print nodes[node_id].priority_list
	elif log_type == 'node_state':
		print 'LOG Time=',time
		for i in nodes:
			print i,':',nodes[i].__dict__
	else:
		raise EventException('Invalid log_type')
	print
	


# Register event handlers

handlers = {}
handlers['ADD_NODE'] = add_node 		# Param: node_id
handlers['UPDATE_PEERS'] = update_peers 	# Param: node_id
handlers['REMOVE_NODE'] = remove_node		# Param: node_id
handlers['EXCHANGE_ROUND'] = exchange_round 	# Param: node_id
#handlers['NEXT_DL'] = next_dl 			# used to schedule additional piece downloads on fast peers
handlers['KILL_SIM'] = kill_sim			# No param
handlers['LOG'] = log				# Param: log type

