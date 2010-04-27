import random

from globals import *

#Node States - not sure if this should be in the node class


#Node class to contain explicit copies of the bit field and peer lists
class Node:
	def __init__(self, node_id, have):
		self.id = node_id

		# Specify the bounds on the number of allowed peers.
		self.min_peers = 5
		self.max_peers = 15

		# Pick a random number of desired peers.
		# Will always try to have at least this many peers (but may have more).
		self.desired_peers = random.randint(self.min_peers, self.max_peers)

		# peers dictionary
		# key: peers that are choked
		# value: the time the peering was made
		self.peers = {}

		# unchoked dictionary
		# key: peers that are unchoked
		# value: the time the peering was made
		self.unchoked = {} # Set of unchoked peers this list should never have more than 5 things in it

		self.interest = {} # Set of peers who are interested in us and their first choice piece

		self.op_unchoke = 0 # ID of current optimistically unchoked peer
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
		self.init_want()




	# Initialize the have_pieces dictionary
	def init_have(self, have):
		#copy the have list into the have_pieces dictionary
		for i in range(len(have)):
			self.have_pieces[i] = have[i] # I hope this works
		print 'Node',self.id,'starts with'
		print self.have_pieces


	# Initialize the want_pieces dictionary
	def init_want(self):
		for i in range(NUM_PIECES):
			if i in self.have_pieces:
				# Already have the piece, so skip it.
				pass
			else:
				self.want_pieces[i] = PIECE_SIZE
		
		

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

		self.sort_priority()

	def num_peers(self):
		return len(self.peers) + len(self.unchoked)


	def get_peers(self, time):
		# Check to see if more peers are needed.
		if self.num_peers() >= self.desired_peers:
			# If not, return because there is nothing to do.
			return

		print 'node',self.id,'(',len(self.peers),'peers ) is querying the tracker and now wants at least',self.desired_peers

		# Get a list of all the nodes that we are not peers with.
		available_nodes = nodes.keys()
		available_nodes.remove(self.id)
		[available_nodes.remove(i) for i in self.unchoked.keys()]
		[available_nodes.remove(i) for i in self.peers.keys()]
		[available_nodes.remove(i) for i in nodes.keys() if nodes[i].num_peers() > nodes[i].max_peers]

		# Otherwise, get more peers until we have desired_peers (or there are none left to get).
		peers_needed = min([self.desired_peers-self.num_peers(), len(available_nodes)])

		for i in range(peers_needed):
			# Pick a random peer among those left
			new_peer = random.choice(available_nodes)
			
			# Remove it from the available nodes list and set the peer for both nodes.
			available_nodes.remove(new_peer)
			nodes[new_peer].add_peer(self.id, time)
			self.add_peer(new_peer, time)
			
		print 'peers for node',self.id,'at time',wq.cur_time
		print self.peers 
		print self.unchoked
		print

	
	# unchoking process
	# there might be a much simpler way to do this, I was really tired when I wrote it
	def update_unchoke(self, time):
		# Move all unchoked nodes back into the peers list.
		for i in self.unchoked:
			self.peers[i] = self.unchoked[i]
		self.unchoked.clear()


		# Pick the unchoked nodes
		if len(self.peers) >= 4:
		        # find the top four uploaders among the unchoked peers
			unchoke_list = []
			for i in self.curr_down:
				unchoke_list.append([self.curr_down[i], i])
				
			unchoke_list.sort();
			unchoke_list.reverse();
			unchoke_list = unchoke_list[0:4]
			
			# update unchoked set with the new top four peers
			for i in range(4):
				id = unchoke_list[i][1]
				self.unchoked[id] = self.peers[id]
				del self.peers[id]

		else:
			# we have so few peers that we make all of them unchoked
			for i in self.peers:
				self.unchoked[i] = self.peers[i]
			self.peers.clear()

		# see if the op_unchoke got picked
		for i in self.unchoked:
			if i == self.op_unchoke:
				# if it was picked, reset the op_unchoke
				self.op_unchoke_count = 0

		# if it wasn't picked, put it back into unchoked
		if self.op_unchoke_count != 0:
			self.unchoked[self.op_unchoke] = self.peers[self.op_unchoke]
			del self.peers[self.op_unchoke]
		
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


			if self.op_unchoke_count == 0: # first time we're here or old op_unchoke was removed
				# Create a new list of the keys of the peers list
				op_unchoke_list = []

				for i in self.peers:
					op_unchoke_list.append([self.peers[i], i])

				op_unchoke_list.sort()
				op_unchoke_list.reverse()

				# Add the newest peers in the op_unchoke_list an extra two times
				# so they are three times more likely to be picked
				new_list = op_unchoke_list[0:3]
				op_unchoke_list += new_list*2
					
				temp = random.choice(op_unchoke_list)	

				self.op_unchoke = temp[1] # should be a node_id

				self.unchoked[self.op_unchoke] = self.peers[self.op_unchoke]
				del self.peers[self.op_unchoke]

				self.op_unchoke_count = 1				
				
			else:
				# Run this op_unchoke peer for another round.
				self.op_unchoke_count = self.op_unchoke_count + 1


	# Sorts the priority list of the node based on rarity
	def sort_priority(self):
		self.priority_list = [] # clear the list cause the priority will change between rounds
		count_dict = {}
		count_list = []
		all_peers = self.peers.keys() + self.unchoked.keys()
		for i in self.want_pieces:
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
		
				
