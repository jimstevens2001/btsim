impor trandom

from globals import *

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
		self.max_up = 100 # Default upload capacity
		self.max_down = 100 # Default download capacity
		self.remain_down = 100 # Download capacity not being used yet
		self.curr_up = [] # Values to keep track of current upload resources being spent, indexed by node id
		self.curr_down = [] # Values to keep track of current download resources being spent, indexed by node id
		self.want_pieces = [] # Blocks node is interested in, the next ones it'll download.
		self.have_pieces = [] # Current blocks held by the node, indexed by block number, contains 

		# don't care about any of thie for now
		#=================================================
		# self.gossip = [] # Recent gossip messages recieved (to be passed on when possible) - not sure about this
		# self.altruism = leave # Current altruism setting
		#=================================================

	def add_peer(self, node_id):
		self.desired_peers = self.desired_peers-1 # right now we don't need this
		self.peers.append(node_id)

	def remove_peer(self, node_id):
		done = 0
		for i in range(len(self.peers)):
			if self.peers[i] == node_id:
				self.peers.remove(node_id)
				self.desired_peers = self.desired_peers+1
				done = 1
				break
		if done == 0:
			for i in range(len(self.unchoked)):
				if self.unchoked[i] == node_id:
					self.unchoked.remove(node_id)
					self.desired_peers = self.desired_peers+1
					done = 1
					break

		print 'Done status was ',done

	def get_peers(self):
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
					nodes[new_peer].add_peer(self.id)
					self.add_peer(new_peer)
					done = True

	
	# unchoking process
	# there might be a much simpler way to do this, I was really tired when I wrote it
	def update_unchoke(self):
		#first clear the set of unchoked peers
		for i in unchoked:
			self.peers.append(i)
			self.unchoked.remove(i)

		#check to see that we have the number of peers that we wanted
		if(len(self.peers) < self.desired_peers):
			self.get_peers()

		#take care of the optimistic unchoke
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
			
