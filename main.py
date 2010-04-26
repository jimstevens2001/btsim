import random

from events import handlers
from globals import *


# Initialize the work queue with ADD_NODE operations.
start_times = []
for i in range(10):
	start_times.append(random.randint(0, 100))
start_times.sort()

for i in range(10):
	x = start_times[i]
	wq.enqueue([x, 'ADD_NODE', i])
	#wq.enqueue([x+50, 'REMOVE_NODE', i])
for i in range(20):
        wq.enqueue([10*i, 'LOG', 'node_state'])

wq.enqueue([150, 'KILL_SIM'])


# Main queue loop
while not wq.empty():
	cur_event = wq.dequeue()

	#print 'Current event is',cur_event[1],'at time',wq.cur_time

	# Call the event handler
	handlers[cur_event[1]](cur_event)

