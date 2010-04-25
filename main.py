import random

from events import handlers
from globals import *


# Initialize the work queue with ADD_NODE operations.
for i in range(10,0, -1):
	x = random.randint(0, 100) + i
	wq.enqueue([x, 'ADD_NODE', i])
	wq.enqueue([x+50, 'REMOVE_NODE', i])
wq.enqueue([200, 'KILL_SIM'])


# Main queue loop
while not wq.empty():
	cur_event = wq.dequeue()

	print 'Current event is',cur_event[1],'at time',wq.cur_time

	# Call the event handler
	handlers[cur_event[1]](cur_event)

