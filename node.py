import random

from globals import *

#Node States - not sure if this should be in the node class


#Node class to contain explicit copies of the bit field and peer lists
class Node:
	def __init__(self, node_id, selection, altruism, leave, have):
		self.id = node_id

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
		self.unchoked = {} # Set of unchoked peers this list should never have more than 5 things in it

		# interest dictionary
		# key: peers that are interested in downloading from this node
		# value: the highest priority piece that this peer wants that we have
		self.interest = {} 

		self.op_unchoke = -1 # ID of current optimistically unchoked peer
		self.op_unchoke_count = 0 # number of times we've tried to unchoke this peer, try 3 times then switch

		self.max_up = 100 # Default upload capacity
		self.max_down = 100 # Default download capacity
		self.remain_down = 100 # Download capacity not being used yet

		self.curr_up = {} # Values to keep track of current upload resources being spent, indexed by node id
		self.curr_down = {} # Values to keep track of current download resources being spent, indexed by node id


		# List of piece IDs we want in order of their rarity
		self.priority_list = []

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




	# Initialize the have_pieces dictionary
	def init_have(self, have):
		#copy the have list into the have_pieces dictionary
		for i in range(len(have)):
			if have[i] == PIECE_SIZE:
				self.have_pieces[i] = 'recovered' # I hope this works

		#print 'Node',self.id,'starts with'
		#print self.have_pieces


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
		
		#if self.id == 2:
			#print 'We are readding node 2'
			#print have
			#print self.have_pieces
			#print self.want_pieces
		
		

	def add_peer(self, node_id, time):
		self.peers[node_id] = time
		self.curr_down[node_id] = 0

	def remove_peer(self, node_id):
		if node_id in self.peers:
			del self.peers[node_id]
		
		if node_id in self.unchoked:
			del self.unchoked[node_id]
			if self.op_unchoke == node_id:
				self.op_unchoke_count = 0
				
		# also need to check the curr_up and curr_down dictionaries for this peer
		if node_id in self.curr_up:
			del self.curr_up[node_id]

		if node_id in self.curr_down:
			del self.curr_down[node_id]

		if node_id in self.interest:
			del self.interest[node_id]			

		self.sort_priority()

		self.update_full_interest()

	def num_peers(self):
		return len(self.peers) + len(self.unchoked)


	def get_peers(self, time):
		# Check to see if more peers are needed.
		if self.num_peers() >= self.desired_peers:
			# If not, return because there is nothing to do.
			pass

		else:
			#print 'node',self.id,'(',self.num_peers(),'peers ) is querying the tracker and now wants at least',self.desired_peers
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
			
		#print 'peers for node',self.id,'at time',wq.cur_time
		#print

	
	# unchoking process
	# there might be a much simpler way to do this, I was really tired when I wrote it
	def update_unchoke(self, time):
		
		#print 'Node ',self.id,'has Peers (6):',self.peers
		#print 'Node ',self.id,'has Unchoked (6):',self.unchoked,'\n'

		# Move all unchoked nodes back into the peers list.
		for i in self.unchoked:
			self.peers[i] = self.unchoked[i]
		self.unchoked.clear()

		# build the unchoke list for the peers we have
		unchoke_list = []
		if self.want_pieces.keys() == []:
			#print 'Curr_up is: ',self.curr_up
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
			self.unchoked[id] = self.peers[id]
			del self.peers[id]

		#print 'Unchoked:',self.unchoked

		# see if the op_unchoke got picked
		for i in self.unchoked:
			if i == self.op_unchoke:
				# if it was picked, reset the op_unchoke
				self.op_unchoke_count = 0

		# if it wasn't picked, put it back into unchoked
		if self.op_unchoke_count != 0:
			self.unchoked[self.op_unchoke] = self.peers[self.op_unchoke]
			del self.peers[self.op_unchoke]

		#print 'Node ',self.id,'has Peers (7):',self.peers
		#print 'Node ',self.id,'has Unchoked (7):',self.unchoked,'\n'

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
				self.peers[self.op_unchoke] = self.unchoked[self.op_unchoke]
				del self.unchoked[self.op_unchoke] # if he uploaded enough, he should get selected as
				                                   # one of the four unchoked peers this round
				self.op_unchoke = -1
			# make sure the current optimistic unchoke is still interested
			elif self.op_unchoke != -1:
				if self.op_unchoke not in self.interest.keys():
					if self.op_unchoke_count != 0:
						self.op_unchoke_count = 0

						# Move the op_unchoke back to the choked list
						#print 'Unchoked(4):',self.unchoked
						self.peers[self.op_unchoke] = self.unchoked[self.op_unchoke]
						del self.unchoked[self.op_unchoke]
						self.op_unchoke = -1


			if self.op_unchoke_count == 0: # first time we're here or old op_unchoke was removed
				# Create a new list of the keys of the peers list
				op_unchoke_list = []

				for i in self.peers:
					if i in self.interest.keys():
						op_unchoke_list.append([self.peers[i], i])

				op_unchoke_list.sort()
				op_unchoke_list.reverse()

				# Add the newest peers in the op_unchoke_list an extra two times
				# so they are three times more likely to be picked
				new_list = op_unchoke_list[0:3]
				op_unchoke_list += new_list*2

				if len(op_unchoke_list) > 0:
					temp = random.choice(op_unchoke_list)
				
					self.op_unchoke = temp[1] # should be a node_id

					self.unchoked[self.op_unchoke] = self.peers[self.op_unchoke]
					del self.peers[self.op_unchoke]

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

		#print 'Node ',self.id,' temp_peer dictionary is ',temp_peers


		# clear our entry in all of our peers interest dictionaries because it might be out of date
		# however, if the entry is a partially downloaded piece, instead remove that peer from
		# temp_peers cause we don't want to touch that dictionary entry
		del_list = []
		for i in range(len(temp_peers)):
			if self.id in nodes[temp_peers[i]].interest.keys():
				piece_index = nodes[temp_peers[i]].interest[self.id]
				#print nodes[temp_peers[i]].interest[self.id]
				if piece_index in nodes[temp_peers[i]].want_pieces.keys():
					if nodes[temp_peers[i]].want_pieces[piece_index] == PIECE_SIZE:
						del nodes[temp_peers[i]].interest[self.id]
				elif piece_index in nodes[temp_peers[i]].have_pieces.keys():
					del nodes[temp_peers[i]].interest[self.id]
				else:
					del_list.append(temp_peers[i])
		
		for i in range(len(del_list)):
			temp_peers.remove(del_list[i])

		#print 'Node ',self.id,' temp_peer dictionary is ',temp_peers
				
		# go through the priority list and find out which peers have these pieces
		temp_del2 = []
		for i in range(len(self.priority_list)):
			temp_del = len(temp_peers)+1
			for j in range(len(temp_peers)):
				if self.priority_list[i] in nodes[temp_peers[j]].have_pieces:
					nodes[temp_peers[j]].interest[self.id] = self.priority_list[i]
					temp_del = temp_peers[j]
					temp_del2.append(self.priority_list[i])
					# break out of the loop cause we've found a peer for that piece
					break
			# remove the peer we found for this piece so we don't associate it with another piece
			if temp_del != len(temp_peers)+1:
				temp_peers.remove(temp_del)
			# remove this piece from the list so we don't try to get it again
		if temp_del2 != []:
			#print 'we are removing something from the priority list'
			for i in range(len(temp_del2)):
				#print temp_del2[i]
				self.priority_list.remove(temp_del2[i])	
				#print 'priority_list:',self.priority_list

		#print self.id
		#print self.want_pieces
		#print self.priority_list
		#print self.interest

	# Update our entry in the interest dictionary of a specific peer
	def update_interest(self, peer):
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
		all_peers = self.peers.keys() + self.unchoked.keys()
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
				
