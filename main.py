import random

from work_queue import WorkQueue, WorkQueueException



# Event format is: [time, type, X, ...] (X and ... can be anything and is determined by the type)
# Time must be non-negative integer.
# Type must be a string.

# Create the main event queue.
wq = WorkQueue()

# Create the main node dictionary.
nodes = {}

# Events:
# add_node: Additional parameters (id)
ADD_NODE = 'add_node'

def add_node(event):
	node_id = event[2]
	if node_id in nodes.keys():
		pass
	nodes[node_id] = {'friends': []}


	# Pick some friends (up to 5 for now)
	peers = []
	all_nodes = nodes.keys()
	MAX_FRIENDS = 5
	num_peers = min([MAX_FRIENDS, len(all_nodes)])
	for i in range(num_peers):
		done = False
		while not done:
			#print 'all_nodes',all_nodes
			if all_nodes != []:
				new_peer = random.choice(all_nodes);
			else:
				break

			all_nodes.remove(new_peer)

			if len(nodes[new_peer]['friends']) < MAX_FRIENDS:
				#print nodes
				#print node_id,'and',new_peer,'are now peers'
				nodes[new_peer]['friends'].append(node_id)
				peers.append(new_peer)
				done = True
	nodes[node_id]['friends'] = peers
		
	

# TODO: Make a list to store nodes.
# TODO: Figure out how to store peer connections.


for i in range(20,0, -1):
	wq.enqueue([i, ADD_NODE, i])

# Main queue loop
while not wq.empty():
	next_event = wq.dequeue()

	print 'Next event is',next_event[1],'at time',wq.cur_time

	if next_event[1] == ADD_NODE:
		add_node(next_event)

print nodes

print 'Done'
