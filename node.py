impor trandom

from globals import *

#Node States - not sure if this should be in the node class


#Node class to contain explicit copies of the bit field and peer lists
class Node:
	def __init__(self, node_id):
		self.id = node_id
		self.peers = {} # Current set of peers that are not unchoked.
		self.unchoked = {} # set of unchoked peers this list should never have more than 5 things in it
		self.min_peers = 5
		self.max_peers = 15
		self.desired_peers = random.randint(self.min_peers, self.max_peers)
		self.op_unchoke = 0 # will be id of current optomistically unchoked peer
		self.unchoke_count = 0 # number of times we've tried to unchoke this peer, try 3 times then switch
		self.max_up = 100 # Default upload capacity
		self.max_down = 100 # Default download capacity
		self.remain_down = 100 # Download capacity not being used yet
		self.curr_up = {} # Values to keep track of current upload resources being spent, indexed by node id
		self.curr_down = {} # Values to keep track of current download resources being spent, indexed by node id
		self.want_pieces = {} # Blocks node is interested in, the next ones it'll download.
		self.have_pieces = {} # Current blocks held by the node, indexed by block number, contains 

		# don't care about any of thie for now
		#=================================================
		# self.gossip = [] # Recent gossip messages recieved (to be passed on when possible) - not sure about this
		# self.altruism = leave # Current altruism setting
		#=================================================

	def add_peer(self, node_id, time):
		self.desired_peers = self.desired_peers-1 # right now we don't need this
		self.peers[node_id] = time

	def remove_peer(self, node_id):
		done = 0
		if node_id in self.peers:
			del self.peers[node_id]
			self.desired_peers = self.desired_peers+1
			done = 1
		if done == 0:
			if node_id in self.unchoked:
				del self.unchoked[node_id]
				self.desired_peers = self.desired_peers+1
				done = 1

		print 'Done status was ',done

	def get_peers(self, time):
		# Get a list of all the nodes that we are not peers with.
		all_nodes = nodes.keys()
		all_nodes.remove(self.id)
		[all_nodes.remove(i) for i in self.peers]

		# Randomly decide how many peers we desire right now.

		# Right now I think we need to keep the number of desired peers constant for a node
		#===========================================================
		# self.desired_peers = random.randint(self.min_peers, self.max_peers)
		#===========================================================

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
					nodes[new_peer].add_peer(self.id, time)
					self.add_peer(new_peerm, time)
					done = True

	
	# unchoking process
	# there might be a much simpler way to do this, I was really tired when I wrote it
	def update_unchoke(self, time):
		#first clear the set of unchoked peers
		for i in unchoked:
			self.peers[i] = self.unchoked[i]
			del self.unchoked[i]

		#find the top four uploaders among your peers
		first = second = third = fourth = 0
		ind1 = ind2 = ind3 = ind4 = 0
		for i in curr_down:
			if(curr_down[i] > first):
				fourth = third
				ind4 = ind3
				third = second
				ind3 = ind2
				second = first
				ind2 = ind1
				first = curr_down[i]
				ind1 = i
			elif(curr_down[i] > second):
				fourth = third
				ind4 = ind3
				third = second
				ind3 = ind2
				second = curr_down[i]
				ind2 = i
			elif(curr_down[i] > third):
				fourth = third
				ind4 = ind3
				third = curr_down[i]
				ind3 = i
			elif(curr_down[i] > fourth):
				fourth = curr_down[i]
				ind4 = i

		#update unchoked set with the new top four peers
		self.unchoked[ind1] = first
		self.unchoked[ind2] = second
		self.unchoked[ind3] = third
		self.unchoked[ind4] = fourth
		
		#take care of the optimistic unchoke
		self.update_op_unchoke()


	# I guess this could've just been included in the unchoking process
	# this should get called every 10 seconds
	def update_op_unchoke(self):	
		if self.op_unchoke == 0: # first time we're here
			# Copy the peers dictionary into an inverted dictionary
			temp_dict = {}
			for i in self.peers:
				temp_dict[self.peers[i]] = i

			temp_list = temp_dict.keys()
			temp_list.sort()

			newest_key = temp_list.pop() # this should be the largest number in the list
			newerer_key = temp_list.pop()
			newer_key = temp_list.pop()

			temp_dict[newest_key+1] = temp_dict[newest_key]
			temp_dict[newest_key+2] = temp_dict[newest_key]
			temp_dict[newest_key+3] = temp_dict[newerer_key]
			temp_dict[newest_key+4] = temp_dict[newerer_key]
			temp_dict[newest_key+5] = temp_dict[newer_key]
			temp_dict[newest_key+6] = temp_dict[newer_key]
					
			self.op_unchoke = random.choice(temp_dict) # should be a node_id		
					
			self.unchoked[self.op_unchoke] = peers[self.op_unchoke]
			del self.peers[self.op_unchoke]
			self.unchoke_count = 1
		elif self.unchoke_count < 4:
			self.unchoke_count = self.unchoke_count + 1
		else:
			self.peers[self.op_unchoke] = self.unchoked[self.op_unchoke]
			del self.unchoked[self.op_unchoke] # if he uploaded enough, he should get selected as
			                                      # one of the four unchoked peers this round
			
			# Copy the peers dictionary into an inverted dictionary
			temp_dict = {}
			for i in self.peers:
				temp_dict[self.peers[i]] = i

			temp_list = temp_dict.keys()
			temp_list.sort()

			newest_key = temp_list.pop() # this should be the largest number in the list
			newerer_key = temp_list.pop()
			newer_key = temp_list.pop()

			temp_dict[newest_key+1] = temp_dict[newest_key]
			temp_dict[newest_key+2] = temp_dict[newest_key]
			temp_dict[newest_key+3] = temp_dict[newerer_key]
			temp_dict[newest_key+4] = temp_dict[newerer_key]
			temp_dict[newest_key+5] = temp_dict[newer_key]
			temp_dict[newest_key+6] = temp_dict[newer_key]
					
			self.op_unchoke = random.choice(temp_dict) # should be a node_id		
					
			self.unchoked[self.op_unchoke] = peers[self.op_unchoke]
			del self.peers[self.op_unchoke]
			self.unchoke_count = 1
			
			
			
