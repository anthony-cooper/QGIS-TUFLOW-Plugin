

class TuResultsIndex():
	"""
	Class for helping get indexed results.
	
	"""
	
	def __init__(self, result, resultType, timestep, max):
		#if resultType == 'Bed Elevation' or resultType == 'Time of Peak h' or resultType == 'Time of Peak V':
		#	self.result = result
		#	self.resultType = resultType
		#	self.timestep = '0.000000'
		#else:
		self.result = result
		self.resultType = '{0}/Maximums'.format(resultType) if max else resultType
		self.timestep = '-99999' if max else timestep
