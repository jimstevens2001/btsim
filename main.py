import random

try:
	import psyco
	psyco.full()
	print 'PYSCO ENABLED!!!'
except:
	print 'PYSCO NOT ENABLED!!!'

from events import handlers
from globals import *


# create a full have list for the seed
have_list = [PIECE_SIZE for i in range(NUM_PIECES)]
if not NO_SEED_TEST:
	wq.enqueue([0, 'ADD_NODE', 1001, 'priority', 'eternal_seed', 0, have_list, SEED_SPEED])

# Open the output files to store the logs
# This just creates the files that are then appended to by the log events
#fpf = open(file_progress_file, 'w')
locf = open(local_file, 'w')
globf = open(global_file, 'w')
distf = open(distance_file, 'w')
pcf = open(piece_count_file, 'w')
#cdf = open(curr_down_file, 'w')
#plf = open(priority_list_file, 'w')


# Close the output files that store the logs
#fpf.close()
locf.close()
globf.close()
distf.close()
pcf.close()
#cdf.close()
#plf.close()

#wq.enqueue([0, 'LOG', 'file_progress', 1001, fpf])


# Initialize the work queue with ADD_NODE operations.
start_times = [random.randint(0,100) for i in range(NUM_NODES)]
start_times.sort()

# Compute the number of pieces each node gets in the NO_SEED_TEST.
have_step = (NUM_PIECES / NUM_NODES)+275
pieces = range(NUM_PIECES)

for i in range(NUM_NODES):
	have = []
	if NO_SEED_TEST:
		# Distribute the pieces.
		if len(pieces) > have_step:
			piece_ids = pieces[0:have_step]
			del pieces[0:have_step]
		elif len(pieces) == 0:
			piece_ids = []
		else:
			piece_ids = pieces
			pieces = []
		if i == NUM_NODES - 1:
			# The last node gets whatever is left.
			piece_ids += pieces
		for j in range(NUM_PIECES):
			if j in piece_ids:
				have.append(PIECE_SIZE)
			else:
				have.append(0)

	wq.enqueue([start_times[i], 'ADD_NODE', i, 'priority', LEECHER_ALTRUISM, 0, have, None])


wq.enqueue([101, 'CHECK_DEAD'])
wq.enqueue([5000, 'KILL_SIM'])

# Main queue loop
while not wq.empty():
	cur_event = wq.dequeue()

	# Call the event handler
	handlers[cur_event[1]](cur_event)
