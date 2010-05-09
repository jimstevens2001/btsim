import random

from globals import *

#Node States - not sure if this should be in the node class


#Node class to contain explicit copies of the bit field and peer lists
class Node:
	def __init__(self, node_id, selection, altruism, leave, have):
		self.id = node_id

		# Save the start time for the node.
		self.start_time = wq.cur_time

		self.starting = 1

		# Specify the bounds on the number of allowed peers.
		self.min_peers = MIN_PEERS
		self.max_peers = MAX_PEERS

		# Style of next piece selection
		# Options: Random, Priority
		self.piece_selection = selection

		# Style of altruism
		# Options: leave_on_complete, eternal_seed, leave_time_after_complete, leave_after_round
		self.altruism = altruism
		self.leave_time = leave

		# Pick a random number of desired peers.
		# Will always try to have at least this many peers (but may have more).
		self.desired_peers = DESIRED_PEERS

		# peers dictionary
		# key: peers that are choked
		# value: the time the peering was made
		self.peers = {}

		# unchoked dictionary
		# key: peers that are unchoked
		# value: the time the peering was made
		# Note: AT NO TIME SHOULD SOMETHING BE IN BOTH PEERS AND UNCHOKED
		self.unchoked = {} # Set of unchoked peers this list should never have more than 5 things in it

		# interest dictionary
		# key: peers that are interested in downloading from this node
		# value: the highest priority piece that this peer wants that we have
		self.interest = {} 
		
		# interest expressed
		# ** What's in here is functionally the head of our priority queue, its what we will get next round **
		# maintain this for measurement purposes
		# key: peers that we are interested in downloading from
		# value: the piece we asked for first from them
		self.requested = {}

		self.op_unchoke = -1 # ID of current optimistically unchoked peer
		self.op_unchoke_count = 0 # number of times we've tried to unchoke this peer, try 3 times then switch

		self.never_unchoked = []

		# Default download capacity
		self.max_down = random.betavariate(1.5, 5)*1000

		# Default upload capacity
		self.max_up = self.max_down * random.uniform(0.5, 1.0)

		self.remain_down = self.max_down # Download capacity not being used yet

		self.curr_up = {} # Values to keep track of current upload resources being spent, indexed by node id
		self.curr_down = {} # Values to keep track of current download resources being spent, indexed by node id


		# List of the piece IDs we want in order of their rarity
		self.priority_list = []

		# Sorted list of the piece IDs we have seen in gossip messages
		# ** Actually a list of objects, first entry is number of times we've seen it in different gossip messages
		#                                second entry is the piece id
		self.gossip_rare = []

		# have_pieces dictionary
		# key: the blocks that we have 
		# value: the time the block finished 
		self.have_pieces = {} 
		self.init_have(have)

		# want_pieces dictionary
		# key: the pieces we DO NOT have
		# value: the number of subblocks left to download
		self.want_pieces = {} 
		self.init_want(have)

		# Define the gossip queue
		self.gossip_queue = []

		# Define the gossip sequence number dictionary
		self.my_gossip_num = 0
		self.peer_gossip_numbers = {}




	# Initialize the have_pieces dictionary
	def init_have(self, have):
		#copy the have list into the have_pieces dictionary
		for i in range(len(have)):
			if have[i] == PIECE_SIZE:
				self.have_pieces[i] = 0 


	# Initialize the want_pieces dictionary
	def init_want(self, have):
		for i in range(NUM_PIECES):
			if i in self.have_pieces:
				# Already have the piece, so skip it.
				pass
			elif len(have) > 0:
				if have[i] > 0:
					self.want_pieces[i] = have[i]
				else:
					self.want_pieces[i] = PIECE_SIZE
			else:
				self.want_pieces[i] = PIECE_SIZE
		
		

	def add_peer(self, node_id, time):
		self.peers[node_id] = time
		self.never_unchoked.append(node_id)

	def remove_peer(self, node_id):
		if node_id in self.peers:
			del self.peers[node_id]
		
		if node_id in self.unchoked:
			del self.unchoked[node_id]
			if self.op_unchoke == node_id:
				self.op_unchoke_count = 0

		if node_id in self.never_unchoked:
			self.never_unchoked.remove(node_id)
				
		# also need to check the curr_up and curr_down dictionaries for this peer
		if node_id in self.curr_up:
			del self.curr_up[node_id]

		if node_id in self.curr_down:
			del self.curr_down[node_id]

		if node_id in self.interest:
			del self.interest[node_id]			

		self.sort_priority()

		self.update_full_interest()

		# Remove all gossip messages from node
		del_list = []
		for msg in self.gossip_queue:
			if node_id == msg[0]:
				del_list.append(msg)
		[self.gossip_queue.remove(msg) for msg in del_list]

		# Delete gossip sequence number
		if node_id in self.peer_gossip_numbers:
			del self.peer_gossip_numbers[node_id]
	

	def num_peers(self):
		return len(self.peers) + len(self.unchoked)


	def get_peers(self, time):
		# Check to see if more peers are needed.
		if self.num_peers() >= self.desired_peers:
			# If not, return because there is nothing to do.
			pass

		else:
			# Get a list of all the nodes that we are not peers with.
			available_nodes = nodes.keys()
			available_nodes.remove(self.id)
			[available_nodes.remove(i) for i in self.unchoked.keys()]
			[available_nodes.remove(i) for i in self.peers.keys()]
			del_list = []
			for i in available_nodes:
				if nodes[i].num_peers() >= nodes[i].max_peers:
					del_list.append(i)
			for i in range(len(del_list)):
				available_nodes.remove(del_list[i])

			# Otherwise, get more peers until we have desired_peers (or there are none left to get).
			peers_needed = min([self.desired_peers-self.num_peers(), len(available_nodes)])
			#outf = open('out_file', 'a')
			#outf.write('node '+str(self.id)+' ( '+str(self.num_peers())+' peers ) has the available nodes '+str(available_nodes)+'\n')
			#outf.write('node '+str(self.id)+' ( '+str(self.num_peers())+' peers ) thinks it needs '+str(peers_needed)+' peers \n')
			#outf.write('\n')
			#outf.close()

			for i in range(peers_needed):
				# Pick a random peer among those left
				new_peer = random.choice(available_nodes)
			
				# Remove it from the available nodes list and set the peer for both nodes.
				available_nodes.remove(new_peer)
				nodes[new_peer].add_peer(self.id, time)
				self.add_peer(new_peer, time)
			

	def choke(self, node_id):
		if node_id not in self.unchoked:
			raise Exception('Attempted to choke a node that is not in unchoked.')
		else:
			self.peers[node_id] = self.unchoked[node_id]
			del self.unchoked[node_id]
		

	def unchoke(self, node_id):
		if node_id not in self.peers:
			raise Exception('Attempted to unchoke a node that is not in peers.')
		else:
			self.unchoked[node_id] = self.peers[node_id]
			del self.peers[node_id]
			if node_id in self.never_unchoked:
				self.never_unchoked.remove(node_id)

	
	# unchoking process
	# there might be a much simpler way to do this, I was really tired when I wrote it
	def update_unchoke(self, time):
		
		# Move all unchoked nodes back into the peers list.
		for i in self.unchoked.keys():
			self.choke(i)

		# build the unchoke list for the peers we have
		unchoke_list = []
		if self.want_pieces.keys() == []:
			for i in self.curr_up:
				# only unchoke them if they want to download something from us
				if i in self.interest.keys():
					unchoke_list.append([self.curr_up[i], i])

		else:
			for i in self.curr_down:
				# only unchoke them if they want to download something from us
				if i in self.interest.keys():
					unchoke_list.append([self.curr_down[i], i])
			
		unchoke_list.sort();
		unchoke_list.reverse();

		# Pick the unchoked nodes
		if len(unchoke_list) >= 4:
		        # find the top four uploaders among the unchoked peers
			unchoke_list = unchoke_list[0:4]
			
		# update unchoked set with the new top four peers or however many we have
		for i in range(len(unchoke_list)):
			id = unchoke_list[i][1]
			self.unchoke(id)

		# see if the op_unchoke got picked
		for i in self.unchoked:
			if i == self.op_unchoke:
				# if it was picked, reset the op_unchoke
				self.op_unchoke_count = 0

		# if it wasn't picked, put it back into unchoked
		if self.op_unchoke_count != 0:
			self.unchoke(self.op_unchoke)

		# take care of the optimistic unchoke
		self.update_op_unchoke()



	# Pick the node to be optimistically unchoked.
	def update_op_unchoke(self):	
		# If there are any choked peers left
		if len(self.peers) > 0: 
			if self.op_unchoke_count > 3:
				# The current optimistic unchoke time has expired.
				# Set the unchoke count to 0 to make a new op_unchoke get
				# picked below.	
				self.op_unchoke_count = 0

				# Move the op_unchoke back to the choked list.
				# if he uploaded enough, he should get selected as
				# one of the four unchoked peers this round
				self.choke(self.op_unchoke)
				self.op_unchoke = -1

			# make sure the current optimistic unchoke is still interested
			elif self.op_unchoke != -1:
				if self.op_unchoke not in self.interest.keys():
					if self.op_unchoke_count != 0:
						self.op_unchoke_count = 0

						# Move the op_unchoke back to the choked list
						self.choke(self.op_unchoke)
						self.op_unchoke = -1


			if self.op_unchoke_count == 0: # first time we're here or old op_unchoke was removed
				# Create a new list of the keys of the peers list
				op_unchoke_list = []

				# For each peer that we are interested in.
				for i in self.peers:
					if i in self.interest.keys():
						# Add them to the op_unchoke list.
						op_unchoke_list.append(i)
						if i in self.never_unchoked:
							# Add two more times if they have never been unchoked.
							op_unchoke_list.append(i)
							op_unchoke_list.append(i)
						


				if len(op_unchoke_list) > 0:
					temp = random.choice(op_unchoke_list)
				
					self.op_unchoke = temp # should be a node_id

					self.unchoke(self.op_unchoke)

					self.op_unchoke_count = 1
				# if we have no peers to make the op_unchoke just set the unchoke_count to 0 and 
				# check again next time
				else:
					self.op_unchoke_count = 0
				
			else:
				# Run this op_unchoke peer for another round.
				self.op_unchoke_count = self.op_unchoke_count + 1

	# Update our entry in the interest dictionaries of our peers
	# This should be called whenever a peer is added or an exchange round begins
	def update_full_interest(self):
		# create a temporary list of all of the peers
		temp_peers = []
		num_all_peers = self.num_peers() 
		for i in self.peers.keys():
			temp_peers.append(i)
		
		for  i in self.unchoked.keys():
			temp_peers.append(i)

		# First time we're here so random choice of piece
		print 'WE ARE AT FULL INTEREST UPDATE'
		#print 'We have ',self.have_pieces.keys()
		#print 'starting is ',self.starting
		print 'gossip is ',GOSSIP,' and style is ',GOSSIP_STYLE

		if self.starting == 1:
			# keey track of which pieces we're getting so we don't get the same piece from two peers
			temp_del = []
			for j in range(len(temp_peers)):

				# Get all of the pieces that this peer has.
				temp_pieces = {}
				for k in nodes[temp_peers[j]].have_pieces.keys():
					temp_pieces[k] = nodes[temp_peers[j]].have_pieces[k]

				# Remove all fo the pieces that we have already scheduled to other peers.
				if temp_del != []:
					for k in range(len(temp_del)):
						if temp_del[k] in temp_pieces.keys():
							del temp_pieces[temp_del[k]]

				# Pick a random piece that this peer has to download
				if temp_pieces.keys() != []:
					rand_piece = random.choice(temp_pieces.keys())
					temp_del.append(rand_piece)
					nodes[temp_peers[j]].interest[self.id] = rand_piece
					self.priority_list.remove(rand_piece)
			
			self.starting = 0
				
		       		
		else:
			if GOSSIP == True and GOSSIP_STYLE == 'priority':
			        # clear our entry in all of our peers interest dictionaries because it might be out of date
			        # however, if the entry is a partially downloaded piece, instead remove that peer from
			        # temp_peers cause we don't want to touch that dictionary entry
			        #test_out.write(str(temp_peers)+'\n')
				print 'UPDATING INTEREST WITH GOSSIP'
			
				del_list = []
				for i in range(len(temp_peers)):
					if self.id in nodes[temp_peers[i]].interest.keys():
						piece_index = nodes[temp_peers[i]].interest[self.id]
						if piece_index in nodes[temp_peers[i]].want_pieces.keys():
							if nodes[temp_peers[i]].want_pieces[piece_index] == PIECE_SIZE:
								del nodes[temp_peers[i]].interest[self.id]
							else:
								del_list.append(temp_peers[i])
						elif piece_index in nodes[temp_peers[i]].have_pieces.keys():
							del nodes[temp_peers[i]].interest[self.id]
						else:
							del_list.append(temp_peers[i])
		
				for i in range(len(del_list)):
					temp_peers.remove(del_list[i])

	                        #print 'Node ',self.id,' temp_peer dictionary is ',temp_peers

				# go through the gossiped rare list and find out which peers (if any) have these pieces
				temp_del2 = []
				temp_del3 = []
				for i in range(5):
					temp_del = NUM_NODES+1
					for j in range(len(temp_peers)):
						if i < len(self.gossip_rare):
							print 'Searching the gossip list'
							if self.gossip_rare[i][1] in nodes[temp_peers[j]].have_pieces:
								nodes[temp_peers[j]].interest[self.id] = self.gossip_rare[i][1]
								temp_del = temp_peers[j]
								temp_del2.append(self.gossip_rare[i])
								temp_del3.append(self.gossip_rare[i][1])
								break
					if temp_del != NUM_NODES+1:
						temp_peers.remove(temp_del)

				# remove this piece from the list so we don't try to get it again
				if temp_del2 != []:
			                #print 'we are removing something from the rare list and the priority list'
					for i in range(len(temp_del2)):
						print 'ACTUALLY FOUND SOMETHING IN RARE_LIST'
						self.gossip_rare.remove(temp_del2[i])
						# also remove this from the priority list cause we're getting it
						print 'priority list is: ', self.priority_list
						print 'thing we are trying to delete is: ',temp_del3[i]
						self.priority_list.remove(temp_del3[i])
				
		                # go through the priority list and find out which peers have these pieces	
				temp_del2 = []
				for i in range(len(self.priority_list)):
					temp_del = NUM_NODES+1
					for j in range(len(temp_peers)):
						if self.priority_list[i] in nodes[temp_peers[j]].have_pieces:
							nodes[temp_peers[j]].interest[self.id] = self.priority_list[i]
							temp_del = temp_peers[j]
							temp_del2.append(self.priority_list[i])
						        # break out of the loop cause we've found a peer for that piece
							break
				        # remove the peer we found for this piece so we don't associate it with another piece
					if temp_del != NUM_NODES+1:
						temp_peers.remove(temp_del)
			        # remove this piece from the list so we don't try to get it again
				if temp_del2 != []:
			                # we are removing something from the priority list
					for i in range(len(temp_del2)):
						self.priority_list.remove(temp_del2[i])	
			else:
				print 'NORMAL INTEREST UPDATE'
				# clear our entry in all of our peers interest dictionaries because it might be out of date
			        # however, if the entry is a partially downloaded piece, instead remove that peer from
			        # temp_peers cause we don't want to touch that dictionary entry
			        #test_out.write(str(temp_peers)+'\n')
			
				# For each peer
				del_list = []
				for i in range(len(temp_peers)):
					# If we are already interested in one of their pieces.
					if self.id in nodes[temp_peers[i]].interest.keys():
						# Get the piece id.
						piece_index = nodes[temp_peers[i]].interest[self.id]

						# If we still want the piece.
						if piece_index in nodes[temp_peers[i]].want_pieces.keys():
							if nodes[temp_peers[i]].want_pieces[piece_index] == PIECE_SIZE:
								del nodes[temp_peers[i]].interest[self.id]
							else:
								del_list.append(temp_peers[i])
						elif piece_index in nodes[temp_peers[i]].have_pieces.keys():
							del nodes[temp_peers[i]].interest[self.id]
						else:
							del_list.append(temp_peers[i])
		
				for i in range(len(del_list)):
					temp_peers.remove(del_list[i])

				
		                # go through the priority list and find out which peers have these pieces
		
				temp_del2 = []
				for i in range(len(self.priority_list)):
					temp_del = NUM_NODES+1
					for j in range(len(temp_peers)):
						if self.priority_list[i] in nodes[temp_peers[j]].have_pieces:
							nodes[temp_peers[j]].interest[self.id] = self.priority_list[i]
							temp_del = temp_peers[j]
							temp_del2.append(self.priority_list[i])
						        # break out of the loop cause we've found a peer for that piece
							break
				        # remove the peer we found for this piece so we don't associate it with another piece
					if temp_del != NUM_NODES+1:
						temp_peers.remove(temp_del)
			        # remove this piece from the list so we don't try to get it again
				if temp_del2 != []:
					for i in range(len(temp_del2)):
						self.priority_list.remove(temp_del2[i])	

	# Update our entry in the interest dictionary of a specific peer
	def update_interest(self, peer):
		if GOSSIP == True and GOSSIP_STYLE == 'priority':
			done = 0
			# scan through the top five entries in our gossiped rare list and see if this peer has any of them
			temp_del = NUM_PIECES+1
			for i in range(5):
				if i < len(self.gossip_rare):
					if self.gossip_rare[i][1] in nodes[peer].have_pieces:
						nodes[peer].interest[self.id] = self.gossip_rare[i][1]
						temp_del = self.gossip_rare[i][1]
						done = 1
						break
			if temp_del != NUM_PIECES+1:
				self.gossip_rare.remove(temp_del)
				# also remove this from the priority list cause we're getting it
				self.priority_list.remove(temp_del)
						
			# if we didn't find anything
			if done == 0:
			        # scan through our priority list and find the next thing that this peer has that we want
				temp_del = NUM_PIECES+1
				for i in range(len(self.priority_list)):
					if self.priority_list[i] in nodes[peer].have_pieces:
						nodes[peer].interest[self.id] = self.priority_list[i]
						temp_del =  self.priority_list[i]
						break
				if temp_del != NUM_PIECES+1:
					self.priority_list.remove(temp_del)	
			        # check to see if we actually updated the interest entry, if not delete it since they no longer have anything we want
				if nodes[peer].interest[self.id] == NUM_PIECES+1:
					del nodes[peer].interest[self.id]
		else:
			# scan through our priority list and find the next thing that this peer has that we want
			temp_del = NUM_PIECES+1
			for i in range(len(self.priority_list)):
				if self.priority_list[i] in nodes[peer].have_pieces:
					nodes[peer].interest[self.id] = self.priority_list[i]
					temp_del =  self.priority_list[i]
					break
			if temp_del != NUM_PIECES+1:
				self.priority_list.remove(temp_del)	
			# check to see if we actually updated the interest entry, if not delete it since they no longer have anything we want
			if nodes[peer].interest[self.id] == NUM_PIECES+1:
				del nodes[peer].interest[self.id]

	# Sorts the priority list of the node based on rarity
	def sort_priority(self):
		self.priority_list = [] # clear the list cause the priority will change between rounds
		count_dict = {}
		count_list = []

		# If global 
		if GLOBAL_KNOWLEDGE == 1:
			all_peers = nodes.keys()
		else:
			all_peers = self.peers.keys() + self.unchoked.keys() + [self.id]

		for i in self.want_pieces:
			# don't want to add in flight pieces to the priority queue
			if self.want_pieces[i] != 0:
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
		self.priority_list = [i[1] for i in count_list] # Put the piece numbers in order of rarity, into the priority_list
				

	def add_gossip(self, msg):
		# Add to end of queue (if it is not a message from this node).
		if msg[0] == self.id:
			return

		# Delete old gossip messages from this node.
		del_list = []
		for i in self.gossip_queue:
			if i[0] == msg[0]:
				del_list.append(i)
		[self.gossip_queue.remove(i) for i in del_list]

		self.gossip_queue.append(msg)


	def gossip(self):
		# Step 1: Send my latest gossip message

		# Find the three rarest pieces within my peer set
		all_peers = self.peers.keys() + self.unchoked.keys()
		piece_list = []
		piece_dict = {}
		for j in range(NUM_PIECES):
			cnt = 0
			for i in all_peers:
				if j in nodes[i].have_pieces:
					cnt += 1
			piece_dict[j] = cnt
			piece_list.append([cnt, j])
		piece_list.sort()
		rare_list = [i[1] for i in piece_list if i[1] not in self.have_pieces][0:3]

		# If there is anything to send.
		if len(rare_list) > 0:
			# Form the gossip message
			gossip_msg = [self.id, self.my_gossip_num, rare_list]

			# Send it to all peers (call node[i].add_gossip()
			for i in all_peers:
				nodes[i].add_gossip(gossip_msg)

		# Update my gossip sequence number
		self.my_gossip_num += 1

		# Step 2: Process my gossip queue and form the list of peer candidates
		print wq.cur_time,': Processing gossip queue for node',self.id
		print 'gossip_queue:',self.gossip_queue
		print 'have list:',self.have_pieces.keys()
		print

		peer_candidates = []

		for msg in self.gossip_queue:
			make_peer = False

			if GOSSIP_STYLE == 'peering':
				# If the node is not already a peer
				if msg[0] not in all_peers:

				        # See if I have the piece
				 	ppiece = []
					for j in msg[2]:
						if j in self.have_pieces:
							if msg[0] not in peer_candidates:
								peer_candidates.append(msg[0])	
							# If so, then decide whether to peer with the source node
							# I have a 2/P chance to peer with this node
							upper_bound = 0.2
							if piece_dict[j] == 0:
								probability = upper_bound
							else:
								probability = upper_bound / piece_dict[j]
							if random.random() < probability:
								make_peer = True
								ppiece.append(j)

				        # Add the peer if necessary
					if make_peer and (self.num_peers() < self.max_peers) and (nodes[msg[0]].num_peers() < self.max_peers):
						print wq.cur_time,': gossip resulted in new peering between',self.id,'and',msg[0],'for one of these pieces:',ppiece
						self.add_peer(msg[0], wq.cur_time)
						nodes[msg[0]].add_peer(self.id, wq.cur_time)
				


				# Initialize the node's sequence number if necessary
				if msg[0] not in self.peer_gossip_numbers:
					self.peer_gossip_numbers[msg[0]] = 0

				# Decide whether to forward message to peers
				if msg[1] > self.peer_gossip_numbers[msg[0]]:
					# Update the gossip sequence number for this node.
					self.peer_gossip_numbers[msg[0]] = msg[1]

					# Forward the message to my peers if I didn't peer this node
					if not make_peer:
						for i in all_peers:
							nodes[i].add_gossip(msg)
							
			elif GOSSIP_STYLE == 'priority':
				#make sure this is a fresh message
				if msg[0] in self.peer_gossip_numbers:
					if msg[1] < self.peer_gossip_numbers[msg[0]]:
						break

				#temporary dictionary of gossiped pieces
				temp_dict = {}
				for i in self.gossip_rare:
					temp_dict[i[1]] = i[0]

				#clear the gossip_rare list, we're about to rebuild it
				self.gossip_rare = []

				#update gossip piece counts
				#this is weighted by the place of the piece in rare message
				#most rare =  count + 1.3, second most rare = count + 1.2, etc
				count = 1.3
				for i in msg[2]:
					# don't add it to the rarest list if we have it
					# ** In the all implementation  of gossip the else of this if should be an attempt to peer **
					if i not in self.have_pieces.keys():
						# don't add it to the rarest list if its in flight to us
						if self.want_pieces[i] != 0:
							if i in temp_dict.keys():
								temp_dict[i] = temp_dict[i] + count
							else:
								temp_dict[i] = count
					count = count - 0.1

				#rebuild the gossip_rare list
				for i in temp_dict.keys():
					self.gossip_rare.append([temp_dict[i], i])

				#sort the gossip_rare list, this returns least to greatest, but we want least to greatest
				self.gossip_rare.sort()

				#reverse the list so we get greatest to least
				self.gossip_rare.reverse()

				# Initialize the node's sequence number if necessary
				if msg[0] not in self.peer_gossip_numbers:
					self.peer_gossip_numbers[msg[0]] = 0
				
				# Update the gossip sequence number for this node.
				self.peer_gossip_numbers[msg[0]] = msg[1]

				# Forward the message to my peers
				for i in all_peers:
					nodes[i].add_gossip(msg)
				

		# Step 3: Clear the gossip queue
		self.gossip_queue = []



