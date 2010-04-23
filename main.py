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
KILL_SIM = 'kill_sim'

def add_node(event):
	node_id = event[2]
	if node_id in nodes.keys():
		pass
	nodes[node_id] = {'peers': []}


	# Pick some peers (up to 5 for now)
	peers = []
	all_nodes = nodes.keys()
	all_nodes.remove(node_id)
	MIN_PEERS = 5
	MAX_PEERS = 15
	desired_peers = random.randint(MIN_PEERS, MAX_PEERS)
	print 'desired_peers for node',node_id,'is',desired_peers
	num_peers = min([desired_peers, len(all_nodes)])
	for i in range(num_peers):
		done = False
		while not done:
			#print 'all_nodes',all_nodes
			if all_nodes != []:
				new_peer = random.choice(all_nodes);
			else:
				break

			all_nodes.remove(new_peer)

			if len(nodes[new_peer]['peers']) < MAX_PEERS:
				#print nodes
				#print node_id,'and',new_peer,'are now peers'
				nodes[new_peer]['peers'].append(node_id)
				peers.append(new_peer)
				done = True
	nodes[node_id]['peers'] = peers
		
	



for i in range(100,0, -1):
	x = random.randint(0, 100) + i
	wq.enqueue([x, ADD_NODE, i])
wq.enqueue([400, KILL_SIM])

# Main queue loop
while not wq.empty():
	cur_event = wq.dequeue()

	print 'Next event is',cur_event[1],'at time',wq.cur_time

	event_type = cur_event[1]

	if event_type == ADD_NODE:
		add_node(cur_event)
	elif event_type == KILL_SIM:
		print 'KILL_SIM event at time',cur_event[0]
		break
	else:
		print 'Invalid event type'
		break

print nodes

print 'Done'
