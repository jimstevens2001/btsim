from work_queue import WorkQueue, WorkQueueException


# Event format is: [time, type, X, ...] (X and ... can be anything and is determined by the type)


# Create the main event queue.
wq = WorkQueue()

# Main queue loop
while not wq.empty():
	pass

print 'Done'
