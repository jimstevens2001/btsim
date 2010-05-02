import random
import psyco
psyco.full()

from events import handlers
from globals import *

# would like to be set this from the command line
# but its not necessary right now
file_progress_file = 'file_progress_record'
can_fill_file = 'can_fill_record'
peers_file = 'peers_record'
curr_down_file = 'curr_down_record'
curr_up_file = 'curr_up_record'
interest_file = 'interest_record'
priority_file = 'priority_record'
want_file = 'want_record'
local_file = 'local_record'
global_file = 'global_record'
distance_file = 'distance_record'

# Initialize the work queue with ADD_NODE operations.
start_times = []
for i in range(100):
	start_times.append(random.randint(0, 100))
start_times.sort()

# create a full have list for the seed
have_list = []
for i in range(NUM_PIECES):
	have_list.append(0)
wq.enqueue([0, 'ADD_NODE', 101, 'priority', have_list])

# Open the output files to store the logs
fpf = open(file_progress_file, 'w')
cff = open(can_fill_file, 'w')
pf = open(peers_file, 'w')
cdf = open(curr_down_file, 'w')
cuf = open(curr_up_file, 'w')
intf = open(interest_file, 'w')
pqf = open(priority_file, 'w')
wf = open(want_file, 'w')
locf = open(local_file, 'w')
globf = open(global_file, 'w')
distf = open(distance_file, 'w')

wq.enqueue([0, 'LOG', 'file_progress', 101, fpf])

# Records for the seed
for j in range(10, 300, 10):
	wq.enqueue([j, 'LOG', 'node_peers', 101, pf])
	wq.enqueue([j, 'LOG', 'curr_down', 101, cdf])
	wq.enqueue([j, 'LOG', 'curr_up', 101, cuf])
	wq.enqueue([j, 'LOG', 'interest', 101, intf])

for i in range(100):
	x = start_times[i]
	wq.enqueue([x, 'ADD_NODE', i, 'priority'])
	# periodic checks on the progression of the swarm
	for j in range(x+1, 300, 5):
		wq.enqueue([j, 'LOG', 'priority_queue', i, pqf])
		wq.enqueue([j, 'LOG', 'file_progress', i, fpf])
		wq.enqueue([j, 'LOG', 'node_peers', i, pf])
		wq.enqueue([j, 'LOG', 'curr_down', i, cdf])
		wq.enqueue([j, 'LOG', 'curr_up', i, cuf])
		wq.enqueue([j, 'LOG', 'interest', i, intf])
		wq.enqueue([j, 'LOG', 'want', i, wf])
		wq.enqueue([j, 'LOG', 'compare', i, locf, globf, distf])
		
	wq.enqueue([x+100, 'REMOVE_NODE', i])
#for i in range(20):
#        wq.enqueue([10*i, 'LOG', 'node_state'])

#wq.enqueue([10, 'LOG', 'interest_dict', 11])
#wq.enqueue([150, 'LOG', 'interest_dict', 11])
wq.enqueue([300, 'KILL_SIM'])


# Main queue loop
while not wq.empty():
	cur_event = wq.dequeue()

	#print 'Current event is',cur_event[1],'at time',wq.cur_time

	# Call the event handler
	handlers[cur_event[1]](cur_event)

# Close the output files that store the logs
fpf.close()
cff.close()
pf.close()
cdf.close()
cuf.close()
intf.close()
pqf.close()
wf.close()
locf.close()
globf.close()
distf.close()

