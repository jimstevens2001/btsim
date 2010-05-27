import random
import sys
import pickle
import math

from node import Node
from globals import *

# Event format is: [time, type, X, ...] (X and ... can be anything and is determined by the type)
# Time must be non-negative integer.
# Type must be a string and is used to call event handler function.

class EventException(Exception): pass


# Define event Handlers

def add_node(event):
	# Add the new node to the nodes dictionary.
	node_id = event[2]
	selection = event[3]
	leave_time = event[5]
	altruism = event[4]
	have = event[6]
	rate = event[7]

	nodes[node_id] = Node(node_id, selection, altruism, leave_time, have, rate)

	print 'Added node',node_id,'at',event[0]
	print

	# Run the initial exchange_round for this node
	exchange_round(event)



# when a node leaves the swarm
def remove_node(event):
	node_id = event[2]

	# Compute the total time this node executed.
	run_time[node_id] = [wq.cur_time - nodes[node_id].start_time, nodes[node_id].max_down]

	# find all events for this node and remove them from the work queue
	# Search the queue for events for this node_id
	del_list = [] 
	for e in wq.wq:
		# Remove all events that use e[2] as a node_id
		if e[1] in ['REMOVE_NODE', 'EXCHANGE_ROUND']:
			if e[2] == node_id:
				del_list.append(e)

		# Special case for the finish_piece event to account for partial download
		if e[1] == 'FINISH_PIECE':
			if e[2] == node_id:
				partial_download(wq.cur_time, e[0], e[2], e[3], e[4])
				del_list.append(e)

		# Remove all events that use e[3] as a node_id
		if e[1] in ['FINISH_PIECE']:
			if e[3] == node_id:
				partial_download(wq.cur_time, e[0], e[2], e[3], e[4])
				del_list.append(e)

		# Remove logs that use node_id
		if e[1] == 'LOG' and e[2] in ['file_progress', 'priority_queue', 'node_peers', 'curr_down', 'curr_up', 'interest', 'want', 'compare']:
			if e[3] == node_id:
				del_list.append(e)
	for e in del_list:
		wq.remove_event(e)
			

	# remove the node from all the peer and unchoked lists of the other nodes
	for i in nodes:
		nodes[i].remove_peer(node_id) 

	
	# remove the node from the node list
	del nodes[node_id]


	# Check to see if we're the last node in the swarm besides the starting seeds
	if len(nodes.keys()) <= NUM_SEEDS: 
		wq.enqueue([wq.cur_time, 'KILL_SIM'])


	print 'Removed node',node_id,'at',event[0]
	print 'The number of remaining nodes is now ',len(nodes.keys())


# This is the function to identify pieces to be exchanged between nodes and to schedule that piece exchange in the work_queue
def piece_exchange(sending_node_id, receiving_node_id, time_remaining, transfer_rate):
	# choose a random piece to upload
	# first make of list of everything that we have that they want	
		
	if nodes[sending_node_id].piece_selection == 'random':
		can_fill = []
		for j in nodes[receiving_node_id].want_pieces.keys():
			if nodes[receiving_node_id].want_pieces[j] != 0:
				if j in nodes[sending_node_id].have_pieces.keys():
					can_fill.append(j)
		if can_fill != []:
			piece_index = random.choice(can_fill)
		else:
			# setting rates to 0 cause nothing is moving cause we have nothing they want
			nodes[receiving_node_id].curr_down[sending_node_id] = 0
			nodes[sending_node_id].curr_up[receiving_node_id] = 0
			piece_index = NUM_PIECES+1
	else:
		# We are checking the interest dictionary for node sending_node_id
		piece_index = nodes[sending_node_id].interest[receiving_node_id]

	if(piece_index != NUM_PIECES+1):
		piece_remaining = nodes[receiving_node_id].want_pieces[piece_index]

		# if its small enough to get in one round then add a finish piece event to the work queue
		if piece_remaining <= (transfer_rate*time_remaining):
			# maybe we should store the time the piece is finished in the have list instead of the size of the piece
			finish_time = piece_remaining/transfer_rate # this should come out in seconds
			event_time = time_remaining - finish_time
			wq.enqueue([wq.cur_time + finish_time, 'FINISH_PIECE', sending_node_id, receiving_node_id, piece_index, event_time])
			#print 'We are scheduling a finish piece event for piece ',piece_index,' at time',wq.cur_time + finish_time
			nodes[receiving_node_id].want_pieces[piece_index] = 0 # set this to 0 to indicate that we are currently finishing it
			nodes[sending_node_id].interest[receiving_node_id] = NUM_PIECES+1
			# otherwise subtract the amount that we can get from the piece size and leave
			# it in the want list
		else:
			nodes[receiving_node_id].want_pieces[piece_index] = nodes[receiving_node_id].want_pieces[piece_index] - (transfer_rate*time_remaining)
			nodes[receiving_node_id].remain_down = max(0, (nodes[receiving_node_id].remain_down - transfer_rate))
			time_remaining = 0

# Use this to update each peers download and upload rates per round and to decide 
# also includes the unchoke algorithm at the beginning
def exchange_round(event):
	node_id = event[2]
	
	print 'Exchange round for node',node_id,'at time',wq.cur_time

	# if our altruism setting is to leave at the end of the round after we've got the whole file
	# then schedule the leave event and don't start any new uploads
	if nodes[node_id].want_pieces.keys() == []:
		if nodes[node_id].altruism == 'leave_after_round':
			wq.enqueue([wq.cur_time, 'REMOVE_NODE', node_id])
			return # we're done here
		elif nodes[node_id].altruism == 'leave_on_complete':
			wq.enqueue([wq.cur_time, 'REMOVE_NODE', node_id]) #not really necessary but here for completeness
			return
		elif nodes[node_id].altruism == 'leave_time_after_complete':
			wq.enqueue([wq.cur_time + nodes[node_id].leave_time, 'REMOVE_NODE', node_id])

	# Run the gossip protocol for peering
	if GOSSIP and GOSSIP_STYLE == 'peering':
		nodes[node_id].gossip()

	# if we need more peers, get them
	nodes[node_id].get_peers(event[0])

	# generate the priority_list for our set of peers
	nodes[node_id].sort_priority() # since we get new peers each round, this will also update the list each round

	# update the interest dictionary to reflect the new priority
	nodes[node_id].update_full_interest()

	# Run the gossip protocol for peering
	if GOSSIP and GOSSIP_STYLE == 'priority':
		nodes[node_id].gossip()
	
	print 'interest',nodes[node_id].interest
	print 'peers',nodes[node_id].peers

	# run the unchoke algorithm
	nodes[node_id].update_unchoke(event[0]);

	# clear the old upload rates cause we're going to recalculate all that stuff
	nodes[node_id].curr_up.clear()

	# determine which piece to send to each unchoked peer
	for i in nodes[node_id].unchoked:
		#print 'we are preparing to send something to node ',i
		#print 'our unchoked dictionary was ',nodes[node_id].unchoked
		exchange_time = ROUND_TIME-1

		del_list = []
		# only unchoked peers should have a curr_down entry
		# I really wish there was a better place to do this
		for k in nodes[i].curr_down:
			if k not in nodes[i].unchoked:
				del_list.append(k)
		
		for k in range(len(del_list)):
			del nodes[i].curr_down[del_list[k]]

		# Splitting download bandwidth
		remain_down = nodes[i].max_down
		for k in nodes[i].curr_down:
			if k != node_id:
				remain_down = remain_down - nodes[i].curr_down[k]


		# let peers know that they're being uploaded to and how much
		up_rate = nodes[node_id].max_up / len(nodes[node_id].unchoked)
		transfer_rate =  min(remain_down, up_rate)

		print 'remain_down',remain_down
		print 'transfer_rate',transfer_rate

		nodes[i].curr_down[node_id] = transfer_rate
		nodes[node_id].curr_up[i] = transfer_rate

		piece_exchange(node_id, i, exchange_time, transfer_rate)
		
	# Schedule the next exchange_round event.
	wq.enqueue([wq.cur_time + ROUND_TIME, 'EXCHANGE_ROUND', node_id])

	# Schedule the next log events
	#wq.enqueue([wq.cur_time, 'LOG', 'file_progress', node_id, file_progress_file])
	wq.enqueue([wq.cur_time, 'LOG', 'compare', node_id, local_file, global_file, distance_file, piece_count_file])
	#wq.enqueue([wq.cur_time, 'LOG', 'curr_down', node_id, curr_down_file])
	#wq.enqueue([wq.cur_time, 'LOG', 'priority_queue', node_id, priority_list_file])
	#wq.enqueue([wq.cur_time, 'LOG', 'interest', node_id, interest_file])



	print
	print 'node_id',nodes[node_id].id
	print 'up/down:',nodes[node_id].max_down,'/',nodes[node_id].max_up
	print 'never',nodes[node_id].never_unchoked
	print 'unchoked',nodes[node_id].unchoked.keys()
	print 'completed',len(nodes[node_id].have_pieces),'/',len(nodes[node_id].have_pieces)+len(nodes[node_id].want_pieces)
#	print 'interest',nodes[node_id].interest
	print 'curr_up',nodes[node_id].curr_up
	print 'max_up',nodes[node_id].max_up
	print 'curr_down',nodes[node_id].curr_down
	print 'max_down',nodes[node_id].max_down
	print

#	cont = True
#	while (cont):
#		cmd = raw_input('>')
#		if cmd == '':
#			cont = False
#		else:
#			print eval(cmd)

def finish_piece(event):
	time = event[0]
	sending_node_id = event[2] # include this just so remove node can find these in the work queue
	receiving_node_id = event[3]
	piece_id = event[4]
	exchange_time = event[5]
	
	del nodes[receiving_node_id].want_pieces[piece_id]
	nodes[receiving_node_id].have_pieces[piece_id] = time

	# make sure this piece isn't still somehow in the global rare list
	for i in range(len(nodes[receiving_node_id].gossip_rare)):
		if nodes[receiving_node_id].gossip_rare[i][1] == piece_id:
			del nodes[receiving_node_id].gossip_rare[i]
			break # list should only have one entry per piece, if this isn't true we have bigger problems
 
	# Check the gossip to see what's changed
	if GOSSIP and GOSSIP_STYLE == 'priority':
		nodes[receiving_node_id].gossip()

	# Update the interest dictionary
	# but only do this if we're still peered
	if (sending_node_id in nodes[receiving_node_id].peers) or (sending_node_id in nodes[receiving_node_id].unchoked):
		nodes[receiving_node_id].update_interest(sending_node_id)

	#print 'the receiving_node_id is: ',receiving_node_id
	#print 'the sending_node_id is: ',sending_node_id
	#print nodes[sending_node_id].interest.keys()
	#print nodes[receiving_node_id].interest.keys()

	# Check to see if there is anything more we can get from this peer
	if receiving_node_id in nodes[sending_node_id].interest.keys():
		if receiving_node_id in nodes[sending_node_id].unchoked:
			up_rate = nodes[sending_node_id].curr_up[receiving_node_id]
		else:
			raise Exception('Attempting to upload to someone not unchoked')

		piece_exchange(sending_node_id, receiving_node_id, exchange_time, up_rate)
	# Check to see if there is anything more we can get from anyone
	# if not, check to see if we should just seed or check out
	elif nodes[receiving_node_id].want_pieces.keys() == []:
		if nodes[receiving_node_id].altruism == 'leave_on_complete':
			wq.enqueue([wq.cur_time, 'REMOVE_NODE', receiving_node_id])
		elif nodes[receiving_node_id].altruism == 'leave_time_after_complete':
			wq.enqueue([wq.cur_time + nodes[receiving_node_id].leave_time, 'REMOVE_NODE', receiving_node_id])
	# So we're not done but this peer isn't any good to us anymore
	# lets get rid of it then
	#else:
		#print 'We are removing a peer'
		#nodes[sending_node_id].remove_peer(receiving_node_id)
		#nodes[receiving_node_id].remove_peer(sending_node_id)
		#print nodes[sending_node_id].interest.keys()
		#print nodes[receiving_node_id].interest.keys()

# sending or receiving node leaves mid round
def partial_download(time, event_time, sending_node_id, receiving_node_id, piece_id):
	
	# time =  the time now
	# event_time = when the download was supposed to finish
	# compute how much of the piece got downloaded
	transfer_rate = nodes[sending_node_id].curr_up[receiving_node_id]
	total_time = PIECE_SIZE/transfer_rate
	time_started = event_time - total_time
	time_elapsed = time_started - time
	amount_downloaded = transfer_rate*time_elapsed
	amount_left = nodes[receiving_node_id].want_pieces[piece_id] - amount_downloaded
	if amount_left == 0:
		del nodes[receiving_node_id].want_pieces[piece_id]
		nodes[receiving_node_id].have_pieces[piece_id] = time
		
		if nodes[receiving_node_id].want_pieces.keys() == []:
			if nodes[receiving_node_id].altruism == 'leave_on_complete':
				wq.enqueue([wq.cur_time, 'REMOVE_NODE', receiving_node_id])
			elif nodes[receiving_node_id].altruism == 'leave_time_after_complete':
				wq.enqueue([wq.cur_time + nodes[receiving_node_id].leave_time, 'REMOVE_NODE', receiving_node_id])
		
	else:
		nodes[receiving_node_id].want_pieces[piece_id] = amount_left

def check_dead(event):
	# Make a list of all pieces.
	pieces = range(NUM_PIECES)

	# Remove the pieces held by current nodes.
	for i in nodes.keys():
		for j in nodes[i].have_pieces.keys():
			if j in pieces:
				pieces.remove(j)
			
			if len(pieces) == 0:
				# Return if all pieces are held.
				wq.enqueue([wq.cur_time + 10, 'CHECK_DEAD'])
				return
	if len(pieces) > 0:
		# Kill the simulation if any pieces are missing.
		print 'PIECES ARE LOST:',pieces
		wq.enqueue([wq.cur_time, 'KILL_SIM'])
	else:
		wq.enqueue([wq.cur_time + 10, 'CHECK_DEAD'])

def kill_sim(event):
	ofile = open(outfile, 'w')
	ofile.write('KILL_SIM event at time '+str(event[0])+'\n')
	ofile.write('nodes left: '+str(nodes.keys())+'\n')
	ofile.write('run_time: '+str(run_time)+'\n')
	print 'KILL_SIM event at time',event[0]
	print 'nodes left:'
	print nodes.keys()
	print 'run_time:'
	print run_time
	values = [run_time[i][0] for i in run_time.keys()]
	if len(values) > 0:
		print 'Average',float(sum(values))/len(values)
		ofile.write('Average '+str(float(sum(values))/len(values))+'\n')
	ofile.close()
	sys.exit(0)


def log(event):
	time = event[0]
	log_type = event[2]

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
		if nodes[node_id].count == 0:	
			if len(event) > 4:
				tfile = event[4]
				fpf = open(file_progress_file, 'a')
				fpf.write('Node '+str(node_id)+'s File Progress at time '+str(time)+' is: \n')
				fpf.write('Precentage complete: '+str(((len(nodes[node_id].have_pieces.keys())*100)/NUM_PIECES))+'%\n')
				for i in nodes[node_id].have_pieces:
					fpf.write('    Piece '+str(i)+' was finished at '+str(nodes[node_id].have_pieces[i])+'\n')
				fpf.write('\n')
			
				fpf.close()
			else:
				print 'Node ',node_id,'s File Progress:'
				for i in nodes[node_id].have_pieces:
					print 'Piece ',i,'was finished at ',nodes[node_id].have_pieces[i]
		elif nodes[node_id].count >= 19:
			nodes[node_id].count = 0
		else:
			nodes[node_id].count = nodes[node_id].count + 1
	elif log_type == 'node_peers':
		node_id = event[3]
		if len(event) > 4:
			file = event[4]
			file.write('Node '+str(node_id)+' has '+str(nodes[node_id].num_peers())+' peers and wants '+str(nodes[node_id].desired_peers)+' peers\n')
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
			cdf = open(file, 'a')
			cdf.write('Node '+str(node_id)+'s Curr_down at time '+str(time)+' is: \n')
			for i in nodes[node_id].curr_down:
				cdf.write('Peer '+str(i)+' is pushing '+str(nodes[node_id].curr_down[i])+'\n')
			cdf.write('\n')
			cdf.close()
		else:
			print 'Node ',node_id,'s Curr_down at time ',time,' is:'
			for i in nodes[node_id].curr_down:
				print 'Peer ',i,' is pulling ',nodes[node_id].curr_down[i]
	elif log_type == 'curr_up':
		node_id = event[3]
		if len(event) > 4:
			file = event[4]
			cuf = open(file, 'a')
			cuf.write('Node '+str(node_id)+'s Curr_up at time '+str(time)+' is: \n')
			for i in nodes[node_id].curr_up:
				cuf.write('Peer '+str(i)+' is pulling '+str(nodes[node_id].curr_up[i])+'\n')
			cuf.write('\n')
			cuf.close()
		else:
			print 'Node ',node_id,'s Curr_up at time ',time,' is:'
			for i in nodes[node_id].curr_up:
				print 'Peer ',i,' is pulling ',nodes[node_id].curr_up[i]
	elif log_type == 'interest':
		node_id = event[3]
		if len(event) > 4:
			file = event[4]
			nif = open(file, 'a')
			nif.write('Node '+str(node_id)+'s Interest Dictionary at time '+str(time)+' is: \n')
			nif.write('    Interested in Peers : For Piece \n')
			for i in nodes[node_id].interest:
				nif.write('    '+str(i)+' : '+str(nodes[node_id].interest[i])+'\n')
			nif.write('\n')
			nif.close()
		else:
			print 'Node ',node_id,'s Interest Dictionary at time ',time,' is:'
			print '    Interested in Peers : For Piece'
			for i in nodes[node_id].interest:
				print '    ',i,' : ',nodes[node_id].interest[i]				
	elif log_type == 'priority_queue':
		node_id = event[3]
		if len(event) > 4:
			file = event[4]
			pqf = open(file, 'a')
			pqf.write('Priority list for node '+str(node_id)+' at time '+str(time)+' is: \n')
			for i in range(len(nodes[node_id].priority_list)):
				pqf.write(str(nodes[node_id].priority_list[i])+' ')
			pqf.write('\n')
			pqf.write('\n')
			pqf.close()
		else:
			print 'Priority list for node ',node_id,' at time ',time,' is'
			print nodes[node_id].priority_list
	elif log_type == 'want':
		node_id = event[3]
		if len(event) > 4:
			file = event[4]
			file.write('Want list for node '+str(node_id)+' at time '+str(time)+' is: \n')
			for i in nodes[node_id].want_pieces:
				file.write('    '+str(i)+' : '+str(nodes[node_id].want_pieces[i])+' \n')
			file.write('\n')
		else:
			print 'Want list for node ',node_id,' at time ',time,' is: '
			for i in nodes[node_id].want_pieces:
				print '    ',i,' : ',nodes[node_id].want_pieces[i],' '
	elif log_type == 'compare':
		node_id = event[3]
		if nodes[node_id].count == 0:
			# Determin the actual global priority for comparison purposes
			global_priority_list = []
			count_dict = {}
			count_list = []

			for i in range(NUM_PIECES):
				# don't want to add pieces that are already in the interest dictionary
				count_dict[i] = 0
				for j in nodes.keys():
					if i in nodes[j].have_pieces:
						if i in count_dict:
							count_dict[i] += 1
						else:
							count_dict[i] = 1
				if i in count_dict:
					count_list.append([count_dict[i], i])

			count_list.sort() # Sort least to greatest so the head is now the most rare pieces
			global_priority_list = [i[1] for i in count_list] # Put the piece numbers in order of rarity, into the priority_list
			local_priority_list = []
			count_dict = {}
			count_list = []

			all_peers = nodes[node_id].peers.keys() + nodes[node_id].unchoked.keys()
			for i in range(NUM_PIECES):
				# don't want to add pieces that are already in the interest dictionary
				count_dict[i] = 0
				for j in all_peers:
					if i in nodes[j].have_pieces:
						if i in count_dict:
							count_dict[i] += 1
						else:
							count_dict[i] = 1
				if i in count_dict:
					count_list.append([count_dict[i], i])			

			count_list.sort() # Sort least to greatest so the head is now the most rare pieces
			local_priority_list = [i[1] for i in count_list] # Put the piece numbers in order of rarity, into the priority_list
			if len(event) > 7:
				lfile = event[4]
				gfile = event[5]
				dfile = event[6]
				pfile = event[7]

				locf = open(lfile, 'a')
				globf = open(gfile, 'a')
				distf = open(dfile, 'a')
				pcf = open(pfile, 'a')

			        #record the count dictionary so we know the rarity of pieces
				pcf.write('Piece counts at time '+str(time)+' for node '+str(node_id)+' are: \n')
				pcf.write('    Piece : Count \n') 
				for i in count_dict:
					pcf.write('    '+str(i)+' : '+str(count_dict[i])+'\n')

				globf.write('Global priority list at time '+str(time)+' is: \n')
				for i in range(len(global_priority_list)):
					globf.write(str(global_priority_list[i])+' ')
				globf.write('\n')
				globf.write('\n')
				locf.write('Local priority list at time '+str(time)+' for node '+str(node_id)+' is: \n')
				for i in range(len(local_priority_list)):
					locf.write(str(local_priority_list[i])+' ')
				locf.write('\n')
				locf.write('\n')
				distf.write('Average distance between all pieces at time '+str(time)+' for node '+str(node_id)+' is: \n')
				distance = 0
				if DISTANCE_MODE == 'top_ten':
				        #for i in range(NUM_PIECES):
					for i in range(10):
						if i in local_priority_list:
							distance = distance + math.fabs(local_priority_list.index(i) - global_priority_list.index(i))

					if len(local_priority_list) > 0:
						distance = distance/10
					else:
						distance = 0
			       
					distf.write('    '+str(distance)+' \n')
					distf.write('\n')
				elif DISTANCE_MODE == 'weighted':
					for i in range(NUM_PIECES):
						if i in local_priority_list:
							distance = distance + math.fabs(local_priority_list.index(i) - global_priority_list.index(i))
							distance = distance / count_dict[i]

					if len(local_priority_list) > 0:
						distance = distance/len(local_priority_list)
					else:
						distance = 0
			       
					distf.write('    '+str(distance)+' \n')
					distf.write('\n')
				else:
					for i in range(NUM_PIECES):
						if i in local_priority_list:
							distance = distance + math.fabs(local_priority_list.index(i) - global_priority_list.index(i))

					if len(local_priority_list) > 0:
						distance = distance/len(local_priority_list)
					else:
						distance = 0
			       
						distf.write('    '+str(distance)+' \n')
						distf.write('\n')
		
				locf.close()
				globf.close()
				distf.close()
				pcf.close()
	
		elif nodes[node_id].count >= 19:
			nodes[node_id].count = 0
		else:
			nodes[node_id].count = nodes[node_id].count + 1
	elif log_type == 'gossip_count':
		node_id = event[3]
		if len(event) > 4:
			file = event[4]
	elif log_type == 'interest_dict':
		node_id = event[3]
		print 'The interest dictionary for node ',node_id,' is '
		print nodes[node_id].interest
	elif log_type == 'node_state':
		for i in nodes:
			print i,':',nodes[i].__dict__
	else:
		raise EventException('Invalid log_type')

	


# Register event handlers

handlers = {}
handlers['ADD_NODE'] = add_node 		# Param: node_id, have_pieces
handlers['REMOVE_NODE'] = remove_node		# Param: node_id
handlers['EXCHANGE_ROUND'] = exchange_round 	# Param: node_id
handlers['FINISH_PIECE'] = finish_piece         # Param: sending node_id, receiving node_id, piece_id, time_remaining
handlers['CHECK_DEAD'] = check_dead			# No param
handlers['KILL_SIM'] = kill_sim			# No param
handlers['LOG'] = log				# Param: log type

