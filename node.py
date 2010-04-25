import random

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
					self.add_peer(new_peer, time)
					done = True

	
	# unchoking process
	# there might be a much simpler way to do this, I was really tired when I wrote it
	def update_unchoke(self, time):
		# first clear the set of unchoked peers
		for i in self.unchoked:
			self.peers[i] = self.unchoked[i]
			del self.unchoked[i]

		if len(self.peers) < 4:
		        # find the top four uploaders among your peers
			unchoke_list = []
			for i in self.curr_down:
				unchoke_list.append([self.curr_down[i], i])
				
			unchoke_list.sort();
			unchoke_list.reverse();
			unchoke_list = unchoke_list[0:3]

			# update unchoked set with the new top four peers
			self.unchoked[unchoke_list[0][1]] = unchoke_list[0][0]
			self.unchoked[unchoke_list[1][1]] = unchoke_list[1][0]
			self.unchoked[unchoke_list[2][1]] = unchoke_list[2][0]
			self.unchoked[unchoke_list[3][1]] = unchoke_list[3][0]
		else:
			# we have so few peers that we make all of them unchoked
			for i in self.peers:
				self.unchoked[i] = self.peers[i]
				del self.peers[i]
		
		#take care of the optimistic unchoke
		self.update_op_unchoke()


	# I guess this could've just been included in the unchoking process
	# this should get called every 10 seconds
	def update_op_unchoke(self):	
		if len(self.peers) > 0: 
			if self.op_unchoke == 0: # first time we're here
				# Create a new list of the keys of the peers list
				op_unchoke_list = []

				for i in self.peers:
					op_unchoke_list.append([self.peers[i], i])

				op_unchoke_list.sort()
				op_unchoke_list.reverse()

				newest = op_unchoke_list[2]
				newerer = op_unchoke_list[1]
				newer = op_unchoke_list[0]

				op_unchoke_list.append(newest)
				op_unchoke_list.append(newest)
				op_unchoke_list.append(newerer)
				op_unchoke_list.append(newerer)
				op_unchoke_list.append(newer)
				op_unchoke_list.append(newer)
					
				temp = random.choice(op_unchoke_list)	

				self.op_unchoke = temp[1] # should be a node_id
					
				self.unchoked[self.op_unchoke] = peers[self.op_unchoke]
				del self.peers[self.op_unchoke]
				self.unchoke_count = 1
			elif self.unchoke_count < 4:
				self.unchoke_count = self.unchoke_count + 1
			else:
				self.peers[self.op_unchoke] = self.unchoked[self.op_unchoke]
				del self.unchoked[self.op_unchoke] # if he uploaded enough, he should get selected as
			                                      # one of the four unchoked peers this round

				# Create a new list of the keys of the peers list
				op_unchoke_list = []

				for i in self.peers:
					op_unchoke_list.append([self.peers[i], i])

				op_unchoke_list.sort()
				op_unchoke_list.reverse()

				newest = op_unchoke_list[2]
				newerer = op_unchoke_list[1]
				newer = op_unchoke_list[0]

				op_unchoke_list.append(newest)
				op_unchoke_list.append(newest)
				op_unchoke_list.append(newerer)
				op_unchoke_list.append(newerer)
				op_unchoke_list.append(newer)
				op_unchoke_list.append(newer)
					
				temp = random.choice(op_unchoke_list)	

				self.op_unchoke = temp[1] # should be a node_id
					
				self.unchoked[self.op_unchoke] = peers[self.op_unchoke]
				del self.peers[self.op_unchoke]
				self.unchoke_count = 1
			
			
			
			
			
