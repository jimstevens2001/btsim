import random
import sys
import pickle

from node import Node
from globals import *

# Event format is: [time, type, X, ...] (X and ... can be anything and is determined by the type)
# Time must be non-negative integer.
# Type must be a string and is used to call event handler function.

class EventException(Exception): pass


# Define event Handlers

def add_node(event):
	node_id = event[2]
	selection = event[3]

	# Add the new node to the nodes dictionary.
	if len(event) >= 5:
		have = event[4]
	else:
		have = {}
	nodes[node_id] = Node(node_id, selection, have)

	print 'Added node',node_id,'at',event[0]
	print

	# Run the initial exchange_round for this node
	exchange_round(event)



# when a node leaves the swarm
def remove_node(event):
	node_id = event[2]

	# find all events for this node and remove them from the work queue
	# Search the queue for events for this node_id
	del_list = [] 
	for e in wq.wq:
		# Remove all events that use e[2] as a node_id
		if e[1] in ['ADD_NODE', 'REMOVE_NODE', 'EXCHANGE_ROUND']:
			if e[2] == node_id:
				del_list.append(e)
				#wq.remove_event(e)

		# Special case for the finish_piece event to account for partial download
		if e[1] == 'FINISH_PIECE':
			if e[2] == node_id:
				partial_download(wq.cur_time, e[0], e[2], e[3], e[4])
				del_list.append(e)
				#wq.remove_event(e)

		# Remove all events that use e[3] as a node_id
		if e[1] in ['FINISH_PIECE']:
			if e[3] == node_id:
				partial_download(wq.cur_time, e[0], e[2], e[3], e[4])
				del_list.append(e)
				#wq.remove_event(e)

		# Remove logs that use node_id
		if e[1] == 'LOG' and e[2] in ['file_progress', 'priority_queue']:
			if e[3] == node_id:
				del_list.append(e)
				#wq.remove_event(e)
	for e in del_list:
		wq.remove_event(e)
			

	# remove the node from all the peer and unchoked lists of the other nodes
	for i in nodes:
		nodes[i].remove_peer(node_id) 

	
	# remove the node from the node list
	del nodes[node_id]
	print 'Removed node',node_id,'at',event[0]
	print wq.wq
	print


# This is the function to identify pieces to be exchanged between nodes and to schedule that piece exchange in the work_queue
def piece_exchange(sending_node_id, recieving_node_id, time_remaining, transfer_rate):
	# choose a random piece to upload
	# first make of list of everything that we have that they want	
	print 'PIECE EXCHANGE IS CALLED'
		
	print 'Piece selection routine is: ',nodes[sending_node_id].piece_selection
	if nodes[sending_node_id].piece_selection == 'random':
		can_fill = []
		for j in nodes[recieving_node_id].want_pieces.keys():
			if nodes[recieving_node_id].want_pieces[j] != 0:
				if j in nodes[sending_node_id].have_pieces.keys():
					can_fill.append(j)
		if can_fill != []:
			piece_index = random.choice(can_fill)
		else:
			# setting rates to 0 cause nothing is moving cause we have nothing they want
			nodes[recieving_node_id].curr_down[sending_node_id] = 0
			nodes[sending_node_id].curr_up[recieving_node_id] = 0
			piece_index = NUM_PIECES+1
	else:
		piece_index = nodes[sending_node_id].interest[recieving_node_id]
		print 'The piece index for node ',sending_node_id,' to node ',recieving_node_id,' is ', piece_index

	if(piece_index != NUM_PIECES+1):
		piece_remaining = nodes[recieving_node_id].want_pieces[piece_index]

		# if its small enough to get in one round then add a finish piece event to the work queue
		if piece_remaining < (transfer_rate*time_remaining):
			# maybe we should store the time the piece is finished in the have list instead of the size of the piece
			finish_time = piece_remaining/transfer_rate # this should come out in seconds
			event_time = time_remaining - finish_time
			wq.enqueue([wq.cur_time + finish_time, 'FINISH_PIECE', sending_node_id, recieving_node_id, piece_index, event_time])
			nodes[recieving_node_id].want_pieces[piece_index] = 0 # set this to 0 to indicate that we are currently finishing it
			# otherwise subtract the amount that we can get from the piece size and leave
			# it in the want list
		else:
			nodes[recieving_node_id].want_pieces[piece_index] = nodes[recieving_node_id].want_pieces[piece_index] - (transfer_rate*time_remaining)
			nodes[recieving_node_id].remain_down = max(0, (nodes[recieving_node_id].remain_down - transfer_rate))
			time_remaining = 0

# Use this to update each peers download and upload rates per round and to decide 
# also includes the unchoke algorithm at the beginning
def exchange_round(event):
	node_id = event[2]

	# if we need more peers, get them
	nodes[node_id].get_peers(event[0])

	# generate the priority_list for our set of peers
	nodes[node_id].sort_priority() # since we get new peers each round, this will also update the list each round

	# run the unchoke algorithm
	nodes[node_id].update_unchoke(event[0]);			
	
	# determine which piece to send to each unchoked peer
	for i in nodes[node_id].unchoked:
		exchange_time = ROUND_TIME

		del_list = []
		# only unchoked peers should have a curr_down entry
		# I really wish there was a better place to do this
		for k in nodes[i].curr_down:
			if k not in nodes[i].unchoked:
				del_list.append(k)
		
		for k in range(len(del_list)):
			del nodes[i].curr_down[del_list[k]]

		# *BIG QUESTION* does download bandwidth get split between downloads?
		# need a way to reset this
		remain_down = nodes[i].max_down
		for k in nodes[i].curr_down:
			if k != node_id:
				remain_down = remain_down - nodes[i].curr_down[k]


		# let peers know that they're being uploaded to and how much
		up_rate = nodes[node_id].max_up / 5
		transfer_rate =  min(remain_down, up_rate)

		print transfer_rate

		nodes[i].curr_down[node_id] = transfer_rate
		nodes[node_id].curr_up[i] = transfer_rate

		piece_exchange(node_id, i, exchange_time, transfer_rate)
		
	# Schedule the next exchange_round event.
	wq.enqueue([wq.cur_time + ROUND_TIME, 'EXCHANGE_ROUND', node_id])

def finish_piece(event):
	print 'FINISH PIECE REACHED'
	time = event[0]
	sending_node_id = event[2] # include this just so remove node can find these in the work queue
	recieving_node_id = event[3]
	piece_id = event[4]
	exchange_time = event[5]
	
	print 'The finish piece recieving node is: ',recieving_node_id
	del nodes[recieving_node_id].want_pieces[piece_id]
	nodes[recieving_node_id].have_pieces[piece_id] = time

	# Update the interest dictionary
	nodes[recieving_node_id].update_interest(sending_node_id)

	up_rate = nodes[sending_node_id].curr_up[recieving_node_id]

	piece_exchange(sending_node_id, recieving_node_id, exchange_time, up_rate)

# sending or receiving node leaves mid round
def partial_download(time, event_time, sending_node_id, recieving_node_id, piece_id):
	
	# time =  the time now
	# event_time = when the download was supposed to finish
	# compute how much of the piece got downloaded
	print 'We are in partial download'
	print 'The receiving node id is: ',recieving_node_id
	print 'The sending node id is: ',sending_node_id
	transfer_rate = nodes[sending_node_id].curr_up[recieving_node_id]
	total_time = PIECE_SIZE/transfer_rate
	time_started = event_time - total_time
	time_elapsed = time_started - time
	amount_downloaded = transfer_rate*time_elapsed
	amount_left = nodes[recieving_node_id].want_pieces[piece_id] - amount_downloaded
	nodes[recieving_node_id].want_pieces[piece_id] = amount_left

def kill_sim(event):
	print 'KILL_SIM event at time',event[0]
	print wq.get_queue()
	sys.exit(0)


def log(event):
	time = event[0]
	log_type = event[2]
	print 'LOG Time=',time

	if log_type == 'time':
		pass
	elif log_type == 'wq':
		print 'Work Queue ='
		print wq.get_queue()
	elif log_type == 'nodes':
		print 'Nodes ='
		print nodes.keys()
	elif log_type == 'peers':
		print 'Peers ='
		peers = {}
		for i in nodes:
			peers[i] = nodes[i].peers
		print peers
	elif log_type == 'file_progress':
		node_id = event[3]
		if len(event) > 4:
			file = event[4]
			file.write('Node '+str(node_id)+'s File Progress at time '+str(time)+' is: \n')
			#file.write(temp_string)
			for i in nodes[node_id].have_pieces:
				file.write('    Piece '+str(i)+' was finished at '+str(nodes[node_id].have_pieces[i])+'\n')
			file.write('\n')
		else:
			print 'Node ',node_id,'s File Progress:'
			for i in nodes[node_id].have_pieces:
				print 'Piece ',i,'was finished at ',nodes[node_id].have_pieces[i]
	elif log_type == 'node_peers':
		node_id = event[3]
		if len(event) > 4:
			file = event[4]
			file.write('Node '+str(node_id)+'s Peers at time '+str(time)+' are: ')
			file.write('    ')
			for i in nodes[node_id].peers:
				file.write(str(nodes[i].id)+' ')
			file.write('\n')
			file.write('\n')
		else:
			print 'Node ',node_id,'s Peers at time ',time,'are: '
			print nodes[node_id].peers
	elif log_type == 'curr_down':
		node_id = event[3]
		if len(event) > 4:
			file = event[4]
			file.write('Node '+str(node_id)+'s Curr_down at time '+str(time)+' is: \n')
			for i in nodes[node_id].curr_down:
				file.write('Peer '+str(i)+' is pushing '+str(nodes[node_id].curr_down[i])+'\n')
			file.write('\n')
		else:
			print 'Node ',node_id,'s Curr_down at time ',time,' is:'
			for i in nodes[node_id].curr_down:
				print 'Peer ',i,' is pulling ',nodes[node_id].curr_down[i]
	elif log_type == 'curr_up':
		node_id = event[3]
		if len(event) > 4:
			file = event[4]
			file.write('Node '+str(node_id)+'s Curr_up at time '+str(time)+' is: \n')
			for i in nodes[node_id].curr_up:
				file.write('Peer '+str(i)+' is pulling '+str(nodes[node_id].curr_up[i])+'\n')
			file.write('\n')
		else:
			print 'Node ',node_id,'s Curr_up at time ',time,' is:'
			for i in nodes[node_id].curr_up:
				print 'Peer ',i,' is pulling ',nodes[node_id].curr_up[i]
	elif log_type == 'interest':
		node_id = event[3]
		if len(event) > 4:
			file = event[4]
			file.write('Node '+str(node_id)+'s Interest Dictionary at time '+str(time)+' is: \n')
			file.write('    Interested in Peers : For Piece \n')
			for i in nodes[node_id].interest:
				file.write('    '+str(i)+' : '+str(nodes[node_id].interest[i])+'\n')
			file.write('\n')
		else:
			print 'Node ',node_id,'s Interest Dictionary at time ',time,' is:'
			print '    Interested in Peers : For Piece'
			for i in nodes[node_id].interest:
				print '    ',i,' : ',nodes[node_id].interest[i]				
	elif log_type == 'priority_queue':
		node_id = event[3]
		if len(event) > 4:
			file = event[4]
			file.write('Priority list for node '+str(node_id)+' is: \n')
			for i in range(len(nodes[node_id].priority_list)):
				file.write(str(nodes[node_id].priority_list[i])+' ')
			file.write('\n')
			file.write('\n')
		else:
			print 'Priority list for node',node_id,'is'
			print nodes[node_id].priority_list
	elif log_type == 'interest_dict':
		node_id = event[3]
		print 'The interest dictionary for node ',node_id,' is '
		print nodes[node_id].interest
	elif log_type == 'node_state':
		for i in nodes:
			print i,':',nodes[i].__dict__
	else:
		raise EventException('Invalid log_type')

	print
	


# Register event handlers

handlers = {}
handlers['ADD_NODE'] = add_node 		# Param: node_id, have_pieces
handlers['REMOVE_NODE'] = remove_node		# Param: node_id
handlers['EXCHANGE_ROUND'] = exchange_round 	# Param: node_id
handlers['FINISH_PIECE'] = finish_piece         # Param: sending node_id, recieving node_id, piece_id, time_remaining
#handlers['NEXT_DL'] = next_dl 			# used to schedule additional piece downloads on fast peers
handlers['KILL_SIM'] = kill_sim			# No param
handlers['LOG'] = log				# Param: log type

