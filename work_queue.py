class WorkQueueException(Exception): pass

class WorkQueue:
	def __init__(self):
		self.wq = [] # Main work queue.
		self.cur_time = 0 # Current simulation time
		self.sorted = True # Keep track of if queue is sorted

	def get_queue(self):
		self.sort()
		return self.wq

	def empty(self):
		return (self.wq == [])

	def sort(self):
		# Sort the queue if necessary.
		# The sort is done right before a dequeue so we don't run it very often.
		if not self.sorted:
			self.wq.sort()
			self.sorted = True
		

	def dequeue(self):
		# Make sure the queue is not empty.
		if self.empty():
			# Throw exception
			raise WorkQueueException('WorkQueue.empty() called with empty queue')

		self.sort()

		# Get the event and set the current time.
		next_event = self.wq.pop(0)
		self.cur_time = next_event[0]

		return next_event

	def enqueue(self, event):
		# Check time
		if event[0] < self.cur_time:
			raise WorkQueueException('WorkQueue.enqueue() called with past time')

		# Insert event
		self.wq.append(event)
		self.sorted = False
	
	
	def remove_event(self, event):
		self.wq.remove(event)
		

def test():
	# Create the main event queue.
	wq = WorkQueue()

	print 'Empty (should be True):',wq.empty()
	print
			
	print 'Dequeue on empty test...'
	try:
		event = wq.dequeue()
		print 'No exception (incorrect)'
		print event
	except WorkQueueException, e:
		print 'Exception (correct)', e
	print

	print 'Enqueue test...'
	try:
		wq.enqueue([1,4])
		print 'No exception (correct)'
	except WorkQueueException, e:
		print 'Exception (incorrect)', e
	print

	print 'Empty (should be False):',wq.empty()
	print


	print 'Dequeue a value test...'
	try:
		event = wq.dequeue()
		print 'No exception (correct)'
		print event
	except WorkQueueException, e:
		print 'Exception (incorrect)', e


	print 'Enqueue old time test...'
	try:
		wq.enqueue([0,5])
		print 'No exception (incorrect)'
	except WorkQueueException, e:
		print 'Exception (correct)', e
	print

	print 'Testing done.'


if __name__ == '__main__':
	test()
