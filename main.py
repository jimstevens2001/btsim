import random

try:
	import psyco
	psyco.full()
except:
	pass

from events import handlers
from globals import *

# Initialize the work queue with ADD_NODE operations.
start_times = []

for i in range(NUM_PEERS):
	start_times.append(random.randint(0,100))
start_times.sort()

# create a full have list for the seed
have_list = []
for i in range(NUM_PIECES):
	have_list.append(PIECE_SIZE)
wq.enqueue([0, 'ADD_NODE', 1001, 'priority', 'eternal_seed', 0, have_list])

# Open the output files to store the logs
# This just creates the files that are then appended to by the log events
fpf = open(file_progress_file, 'w')
locf = open(local_file, 'w')
globf = open(global_file, 'w')
distf = open(distance_file, 'w')
pcf = open(piece_count_file, 'w')

#Disabled Logs
#======================================
#cff = open(can_fill_file, 'w')
#pf = open(peers_file, 'w')
#cdf = open(curr_down_file, 'w')
#cuf = open(curr_up_file, 'w')
#intf = open(interest_file, 'w')
#pqf = open(priority_file, 'w')
#wf = open(want_file, 'w')
#======================================

# Close the output files that store the logs
fpf.close()
locf.close()
globf.close()
distf.close()
pcf.close()

#Disabled Logs
#======================================
#cff.close()
#pf.close()
#cdf.close()
#cuf.close()
#intf.close()
#pqf.close()
#wf.close()
#======================================


wq.enqueue([0, 'LOG', 'file_progress', 1001, fpf])

# Records for the seed
#for j in range(10, 300, 10):
	#wq.enqueue([j, 'LOG', 'node_peers', 101, pf])
	#wq.enqueue([j, 'LOG', 'curr_down', 101, cdf])
	#wq.enqueue([j, 'LOG', 'curr_up', 101, cuf])
	#wq.enqueue([j, 'LOG', 'interest', 101, intf])

for i in range(NUM_PEERS):
	x = start_times[i]

	#wq.enqueue([x, 'ADD_NODE', i, 'priority', 'leave_on_complete', 0])
	wq.enqueue([x, 'ADD_NODE', i, 'priority', 'eternal_seed', 0])

	# periodic checks on the progression of the swarm
	#for j in range(x+1, 900, 10):
		#wq.enqueue([j, 'LOG', 'priority_queue', i, pqf])
	wq.enqueue([x+1, 'LOG', 'file_progress', i, file_progress_file])
		#wq.enqueue([j, 'LOG', 'node_peers', i, pf])
		#wq.enqueue([j, 'LOG', 'curr_down', i, cdf])
		#wq.enqueue([j, 'LOG', 'curr_up', i, cuf])
		#wq.enqueue([j, 'LOG', 'interest', i, intf])
		#wq.enqueue([j, 'LOG', 'want', i, wf])
	wq.enqueue([x+1, 'LOG', 'compare', i, local_file, global_file, distance_file, piece_count_file])
		
	#wq.enqueue([x+100, 'REMOVE_NODE', i])
#wq.enqueue([100, 'REMOVE_NODE', 2])
#wq.enqueue([150, 'ADD_NODE', 2, 'priority', 'leave_on_complete', 0])
#for i in range(20):
#        wq.enqueue([10*i, 'LOG', 'node_state'])

#wq.enqueue([10, 'LOG', 'interest_dict', 11])
#wq.enqueue([150, 'LOG', 'interest_dict', 11])
#wq.enqueue([900, 'KILL_SIM'])


# Main queue loop
while not wq.empty():
	cur_event = wq.dequeue()

	#print 'Current event is',cur_event[1],'at time',wq.cur_time

	# Call the event handler
	handlers[cur_event[1]](cur_event)
