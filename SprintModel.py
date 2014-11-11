
class Rider( object ):
	def __init__( self, bib, lastName, firstName, team = '', license = '' ):
		self.bib = bib
		self.firstName = firstName
		self.lastName = lastName
		self.team = team
		self.license = license
		
	@property
	def full_name( self ):
		if self.lastName and self.firstName:
			return '%s, %s' % (self.lastName, self.firstName)
		elif self.lastName:
			return self.lastName
		else:
			return self.firstName
		
openRider = Rider( -1, 'Open', '' )
		
class Fact( object ):

	# Noncontinue reasons
	DNF = 'DNF'
	DNS = 'DNS'
	DQ = 'DQ'

	def __init__( self, id, place = None, heat = None,
						qualifier = None, noncontinue = None,
						relegate = None, startPosition = None ):
		self.id = id
		self.place = place
		self.qualifier = qualifier
		self.heat = heat
		self.noncontinue = noncontinue
		self.relegate = relegate
		self.startPosition = startPosition
		
	def getRepr( self, labels ):
		s = ''
		for reason in ['place', 'qualifier', 'noncontinue', 'relegate', 'startPosition']:
			v = getattr(self, reason)
			if v is not None:
				if self.heat is not None:
					s = 'Fact: %s (%s) %s %s in heat %s' % (labels[self.id].full_name, self.id, reason, v, self.heat)
				else:
					s = 'Fact: %s (%s) %s %s' % (labels[self.id].full_name, self.id, reason, v)
				break
		return s

class Facts( object ):
	def __init__( self ):
		self.facts = []
		self.idFacts = {}
		
	def append( self, fact ):
		self.facts.append( fact )
		self.idFacts.setdefault(fact.id, []).append( fact )
		
	def extend( self, facts ):
		for f in facts:
			self.append( f )
		
	def getNumWins( self, id ):
		return sum( 1 for f in self.idFacts.get(id,[]) if f.place == 1 )
		
	def getQualifier( self, id ):
		for f in self.idFacts.get(id,[]):
			if f.qualifier is not None:
				return f.qualifier
		return None
		
	def getPlace( self, id ):
		for f in self.idFacts.get(id,[]):
			if f.place is not None:
				return f.place
		return None
		
	def getRepr( self, labels ):
		return '\n'.join( f.getRepr(labels) for f in self.facts )
	
class Competition( object ):
	def __init__( self, name, starters, tournaments ):
		self.name = name
		self.starters = starters
		self.tournaments = tournaments
		self.clear()
		
		# Make sure there are not repeated labels in the spec.
		inLabels = set()
		outLabels = set()
		for t, s, e in self.allEvents():
			e.system = s
			e.tournament = t
			s.tournament = t
			for c in e.composition:
				assert c not in inLabels
				inLabels.add( c )
			for c in e.getOutLabels():
				assert c not in outLabels
				outLabels.add( c )
		
	def clear( self ):
		self.facts = Facts()
		self.labels = {}
		self.qualifiers = {}

	def addFact( self, fact ):
		self.facts.append( fact )
		self.propagate()
	
	def allEvents( self ):
		for tournament in self.tournaments:
			for system in tournament.systems:
				for event in system.events:
					yield tournament, system, event
	
	def addQualifier( self, rider, t ):
		self.qualifiers[rider] = t
		if len(self.qualifiers) == self.starters:
			qualifiers = self.getQualifiers()
			self.facts.extend( [Fact('N%d' % (i+1), qualifier = t) for i, (t, r) in enumerate(qualifiers)] )
			self.labels = dict( [('N%d' % (i+1), r) for i, (t, r) in enumerate(qualifiers)] )
	
	def getQualifiers( self ):
		qualifiers = [(t, rider) for rider, t in self.qualifiers.iteritems()]
		qualifiers.sort()
		return qualifiers
	
	def getMeetsPreconditions( self ):
		return [(t, s, e) for t, s, e in self.allEvents() if e.meetsPreconditions(self.labels)]
		
	def propagate( self ):
		for t, s, e in self.allEvents():
			e.propagate( self.labels, self.facts )
		return [ self.labels.get('%dR' % (r+1), None) for r in xrange(self.starters) ]

	def getResults( self ):
		results = [None] * self.starters
		# Assign all riders based on qualifying time by group.
		iTT = self.starters
		for ttSuffix in ['TT1', 'TT2', 'TT']:
			tts = [label for label, rider in self.labels.iteritems() if label.endswith(ttSuffix)]
			tts.sort( key = lambda x: -self.qualifiers[self.labels[x]] )
			for tt in tts:
				iTT -= 1
				results[iTT] = self.labels[tt]
		for i in xrange(self.starters):
			try:
				results[i] = self.labels['%dR' % (i+1)]
			except KeyError:
				pass
		return results
		
class Tournament( object ):
	def __init__( self, name, systems ):
		self.name = name
		self.systems = systems

class System( object ):
	def __init__( self, name, events ):
		self.name = name
		self.events = events

class Start( object ):
	def __init__( self ):
		self.relegated = None
		self.startPosition = None
		
	def randomizeStartPosition( self, labels ):
		startCount = self.getStartCount( labels )
		
		self.startPosition = range(startCount)
		random.shuffle( self.startPosition )
		self.startPosition += range( startCount, len(self.event.composition) )
		self.startPositionOriginal = [s for s in self.startPosition]
	
class Heat( object ):
	def __init__( self, event, heat ):
		self.event = event
		self.heat = heat
		self.heatMax = heatMax
		self.restarted = False
		self.relegated = []
		self.noncontinue = {}
		self.startPosition = None
		self.startPositionOriginal = None
		self.starts = []
	
	def getStartCount( self, labels ):
		return sum( 1 for c in self.event.composition if labels[c] != riderOpen and c not in self.noncontinue )
	
	def randomizeStartPosition( self, labels ):
		startCount = self.getStartCount( labels )
		
		self.startPosition = range(startCount)
		random.shuffle( self.startPosition )
		self.startPosition += range( startCount, len(self.event.composition) )
		self.startPositionOriginal = [s for s in self.startPosition]
	
	def setRelegate( self, c ):
		self.relegated.append( c )
		startPosition = [event.composition.index(c)]
		startPosition += [sp for sp in self.startPosition if sp != startPosition[0]]
		self.startPosition = startPosition
	
	def setNoncontinue( self, c, reason ):
		self.noncontinue[c] = reason
		
	def getHeatPrev( self ):
		if self.heat == 1:
			return None
		return self.event.heats[self.heat-1]
	
	def meetsPreconditions( self, labels, facts ):
		# First check if all the starters are known.
		for c in self.event.composition:
			if not c in labels:
				return False, 'Starter "%s" is unknown.' % c
		
		# Create an initial start position.
		if not self.startPosition:
			if self.heat == 1 or self.heat == 3:
				self.randomizeStartPosition( labels )
				
		# Correct the start positions depending on the heat.
			else:
				heatPrev = self.event.heats[self.heat-2]
				if self.heat == 2:
					if heatPrev:
					pass
				else self.heat == 3:
					pass
		
		
		if self.heat == 1:
			
		else:
		
		for c in self.composition:
			try:
				starterFacts = facts[c]
			except:
				return False
				
			
	
	def propagate( self, labels, facts ):
		for c in self.composition:
			wins = facts.getNumWins( c )
			if (self.heatsMax == 1 and wins == 1) or (self.heatsMax == 3 and wins > 1):
				labels[self.winner] = labels[c]
				for o, r in zip(self.others, [k for k in self.composition if k != c]):
					labels[o] = labels[r]
				break
	
	def getOutLabels( self ):
		return [self.winner] + self.others
		
	def getHeat( self, facts ):
		winsTotal = sum( facts.getNumWins(c) for c in self.composition )
		return winsTotal + 1
	
	def getRepr( self, labels, facts ):
		def labName( id ):
			return '%s (%s)' % (labels[id].full_name, id) if id in labels else '(%s)' % id
		s = '%s, Heat %d/%d: %s => %s   %s' % (
			self.system.name,
			self.getHeat(facts), self.heatsMax, 
			', '.join(labName(c) for c in self.composition),
			labName(self.winner),
			', '.join(labName(c) for c in self.others) )
		if self.tournament.name:
			s = '[%s] %s' % (self.tournament.name, s)
		return s
		
class Event( object ):
	def __init__( self, composition, winner, others, heatsMax ):
		super( Event, self ).__init__( composition )
		self.composition = composition
		self.winner = winner
		if not isinstance( others, list ):
			others = [others]
		self.others = others
		self.heatsMax = heatsMax
		self.heats = [Heat(self, self.composition, self.winner, self.others, heat, self.heatsMax) for heat in xrange(1, 1 + self.heatsMax)]
		
	def meetsPreconditions( self, labels, facts ):
		# First check if all the starters are known.
		for c in self.composition:
			if not c in labels:
				return False

	def getRepr( self, labels, facts ):
		def labName( id ):
			return '%s (%s)' % (labels[id].full_name, id) if id in labels else '(%s)' % id
		s = '%s, Heat %d/%d: %s => %s   %s' % (
			self.system.name,
			self.getHeat(facts), self.heatsMax, 
			', '.join(labName(c) for c in self.composition),
			labName(self.winner),
			', '.join(labName(c) for c in self.others) )
		if self.tournament.name:
			s = '[%s] %s' % (self.tournament.name, s)
		return s
		

		
class EventFour( EventBase ):
	def __init__( self, composition, bestPlace ):
		super( EventFour, self ).__init__( composition )
		self.bestPlace = bestPlace

	def meetsPreconditions( self, labels ):
		return super(EventFour, self).meetsPreconditions(labels) and \
				not all( ('%dR' % i) in labels for i in xrange(self.bestPlace, self.bestPlace+4) )
		
	def propagate( self, labels, facts ):
		if not self.meetsPreconditions(labels):
			return

		for c in self.composition:
			if facts.getPlace(c) is None:
				return
				
		for c in self.composition:
			labels['%dR' % (facts.getPlace(c) - 1 + self.bestPlace)] = labels[c]

	def getOutLabels( self ):
		return [('%dR' % i)for i in xrange(self.bestPlace, self.bestPlace+4)]
	
	def getRepr( self, labels, facts ):
		def labName( id ):
			return '%s (%s)' % (labels[id].full_name, id) if id in labels else '(%s)' % id
		return '%s, Heat 1: %s => %s' % (
			self.system.name,
			', '.join(labName(c) for c in self.composition),
			', '.join(labName('%dR' % i) for i in xrange(self.bestPlace, self.bestPlace+4)) )
	
			
competitions = [
	Competition( 'World Cup', 16, [
		Tournament( '', [
			System( '1/8 Finals', [
				Event( ['N1', 'N16'], '1A1', '1A2', 1 ),
				Event( ['N2', 'N15'], '2A1', '2A2', 1 ),
				Event( ['N3', 'N14'], '3A1', '3A2', 1 ),
				Event( ['N4', 'N13'], '4A1', '4A2', 1 ),
				Event( ['N5', 'N12'], '5A1', '5A2', 1 ),
				Event( ['N6', 'N11'], '6A1', '6A2', 1 ),
				Event( ['N7', 'N10'], '7A1', '7A2', 1 ),
				Event( ['N8', 'N9'],  '8A1', '8A2', 1 ),
			]),
			System( '1/4 Finals', [
				Event( ['1A1', '8A1'], '1B', '1P', 3 ),
				Event( ['2A1', '7A1'], '2B', '2P', 3 ),
				Event( ['3A1', '6A1'], '3B', '3P', 3 ),
				Event( ['4A1', '5A1'], '4B', '4P', 3 ),
				EventFour( ['1P', '2P', '3P', '4P'], 5 )
			]),
			System( '1/2 Finals', [
				Event( ['1B', '4B'], '1C1', '1C2', 3 ),
				Event( ['2B', '3B'], '2C1', '2C2', 3 ),
			]),
			System( 'Finals', [
				Event( ['1C1', '2C1'], '1R', '2R', 3 ),
				Event( ['1C2', '2C2'], '3R', '4R', 3 )
			]),
		]),
		Tournament( 'B', [
			System( '1/4 Finals', [
				Event( ['1A2', '8A2'], '1D1', '1TT', 1 ),
				Event( ['2A2', '7A2'], '2D1', '2TT', 1 ),
				Event( ['3A2', '6A2'], '3D1', '3TT', 1 ),
				Event( ['4A2', '5A2'], '4D1', '4TT', 1 ),
			]),
			System( '1/2 Finals', [
				Event( ['1D1', '4D1'], '1E1', '1E2', 1 ),
				Event( ['2D1', '3D1'], '2E1', '2E2', 1 ),
			]),
			System( 'Finals', [
					Event( ['1E1', '2E1'],  '9R', '10R', 1 ),
					Event( ['1E2', '2E2'], '11R', '12R', 1 ),
			]),
		]),
	]),
	
	Competition( 'World Championships', 24, [
		Tournament( '', [
			System( '1/16 Finals', [
				Event( ['N1', 'N24'], '1A', '1TT1', 1 ),
				Event( ['N2', 'N23'], '2A', '2TT1', 1 ),
				Event( ['N3', 'N22'], '3A', '3TT1', 1 ),
				Event( ['N4', 'N21'], '4A', '4TT1', 1 ),
				Event( ['N5', 'N20'], '5A', '5TT1', 1 ),
				Event( ['N6', 'N19'], '6A', '6TT1', 1 ),
				Event( ['N7', 'N18'], '7A', '7TT1', 1 ),
				Event( ['N8', 'N17'], '8A', '8TT1', 1 ),
				Event( ['N9', 'N16'], '9A', '9TT1', 1 ),
				Event( ['N10', 'N15'], '10A', '10TT1', 1 ),
				Event( ['N11', 'N14'], '11A', '11TT1', 1 ),
				Event( ['N12', 'N13'], '12A', '12TT1', 1 ),
				]),
			System( '1/8 Finals', [
				Event( ['1A', '12A'], '1B1', '1B2', 3 ),
				Event( ['2A', '11A'], '2B1', '2B2', 3 ),
				Event( ['3A', '10A'], '3B1', '3B2', 3 ),
				Event( ['4A', '9A'], '4B1', '4B2', 3 ),
				Event( ['5A', '8A'], '5B1', '5B2', 3 ),
				Event( ['6A', '7A'], '6B1', '6B2', 3 ),
			]),
			System( 'Repechages', [
				Event( ['1B2', '4B2', '6B2'], '1C', ['13TT2', '14TT2'], 1 ),
				Event( ['2B2', '3B2', '5B2'], '2C', ['15TT2', '16TT2'], 1 ),
			]),
			System( '1/4 Finals', [
				Event( ['1B1', '2C'], '1D', '1P', 3 ),
				Event( ['2B1', '1C'], '2D', '2P', 3 ),
				Event( ['3B1', '6B1'], '3D', '3P', 3 ),
				Event( ['4B1', '5B1'], '4D', '4P', 3 ),
				EventFour( ['1P', '2P', '3P', '4P'], 5 )
			]),
			System( '1/2 Finals', [
				Event( ['1D', '4D'], '1E1', '1E2', 3 ),
				Event( ['2D', '3D'], '2E1', '2E2', 3 ),
			]),
			System( 'Finals', [
				Event( ['1E1', '2E1'], '1R', '2R', 3 ),
				Event( ['1E2', '2E2'], '3R', '4R', 3 ),
			]),
		])
	]),
	
	Competition( 'Olympic Games', 18, [
		Tournament( '', [
			System( '1/16 Finals', [
				Event( ['N1', 'N18'], '1A1', '1A2', 1 ),
				Event( ['N2', 'N17'], '2A1', '2A2', 1 ),
				Event( ['N3', 'N16'], '3A1', '3A2', 1 ),
				Event( ['N4', 'N15'], '4A1', '4A2', 1 ),
				Event( ['N5', 'N14'], '5A1', '5A2', 1 ),
				Event( ['N6', 'N13'], '6A1', '6A2', 1 ),
				Event( ['N7', 'N12'], '7A1', '7A2', 1 ),
				Event( ['N8', 'N11'], '8A1', '8A2', 1 ),
				Event( ['N9', 'N10'], '9A1', '9A2', 1 ),
			]),
			System( 'Repechages 1', [
				Event( ['1A2', '6A2', '9A2'], '1B', ['1TT', '2TT'], 1 ),
				Event( ['2A2', '5A2', '7A2'], '2B', ['3TT', '4TT'], 1 ),
				Event( ['3A2', '4A2', '8A2'], '3B', ['5TT', '6TT'], 1 ),
			]),
			System( '1/8 Finals', [
				Event( ['1A1', '3B'],  '1C1', '1C2', 1 ),
				Event( ['2A1', '2B'],  '2C1', '2C2', 1 ),
				Event( ['3A1', '1B'],  '3C1', '3C2', 1 ),
				Event( ['4A1', '9A1'], '4C1', '4C2', 1 ),
				Event( ['5A1', '8A1'], '5C1', '5C2', 1 ),
				Event( ['6A1', '7A1'], '6C1', '6C2', 1 ),
			]),
			System( 'Repechages 2', [
				Event( ['1C2', '4C2', '6C2'], '1D', ['1P', '2P'], 1 ),
				Event( ['2C2', '3C2', '5C2'], '2D', ['3P', '4P'], 1 ),
				EventFour( ['1P', '2P', '3P', '4P'], 9 )
			]),
			System( '1/4 Finals', [
				Event( ['1C1', '2D'],  '1F', '1Q', 3 ),
				Event( ['2C1', '1D'],  '2F', '2Q', 3 ),
				Event( ['3C1', '6C1'], '3F', '3Q', 3 ),
				Event( ['4C1', '5C1'], '4F', '4Q', 3 ),
				EventFour( ['1Q', '2Q', '3Q', '4Q'], 5 )
			]),
			System( '1/2 Finals', [
				Event( ['1F', '4F'], '1G1', '1G2', 3 ),
				Event( ['2F', '3F'], '2G1', '2G2', 3 ),
			]),
			System( 'Finals', [
				Event( ['1G1', '2G1'], '1R', '2R', 3 ),
				Event( ['1G2', '2G2'], '3R', '4R', 3 ),
			]),
		]),
	]),
	
	Competition( '12 Starters', 12, [
		Tournament( '', [
			System( '1/8 Finals', [
				Event( ['1N', '12N'], '1B1', '1B2', 1 ),
				Event( ['2N', '11N'], '2B1', '2B2', 1 ),
				Event( ['3N', '10N'], '3B1', '3B2', 1 ),
				Event( ['4N', '9N'], '4B1', '4B2', 1 ),
				Event( ['5N', '8N'], '5B1', '5B2', 1 ),
				Event( ['6N', '7N'], '6B1', '6B2', 1 ),
			]),
			System( 'Repechages', [
				Event( ['1B2', '4B2', '6B2'], '1C', ['9TT', '10TT'], 1 ),
				Event( ['2B2', '3B2', '5B2'], '2C', ['11TT', '12TT'], 1 ),
			]),
			System( '1/4 Finals', [
				Event( ['1B1', '2C'], '1D', '1P', 3 ),
				Event( ['2B1', '1C'], '2D', '2P', 3 ),
				Event( ['3B1', '6B1'], '3D', '3P', 3 ),
				Event( ['4B1', '5B1'], '4D', '4P', 3 ),
				EventFour( ['1P', '2P', '3P', '4P'], 5 )
			]),
			System( '1/2 Finals', [
				Event( ['1D', '4D'], '1E1', '1E2', 3 ),
				Event( ['2D', '3D'], '2E1', '2E2', 3 ),
			]),
			System( 'Finals', [
				Event( ['1E1', '2E1'], '1R', '2R', 3 ),
				Event( ['1E2', '2E2'], '3R', '4R', 3 ),
			]),
		])
	]),
	
	Competition( '8 Starters', 8, [
		Tournament( '', [
			System( '1/4 Finals', [
				Event( ['1N', '8N'], '1B', '1P', 1 ),
				Event( ['2N', '7N'], '2B', '2P', 1 ),
				Event( ['3N', '6N'], '3B', '3P', 1 ),
				Event( ['4N', '5N'], '4B', '4P', 1 ),
				EventFour( ['1P', '2P', '3P', '4P'], 5 )
			]),
			System( '1/2 Finals', [
				Event( ['1B', '4B'], '1C1', '1C2', 3 ),
				Event( ['2B', '3B'], '2C1', '2C2', 3 ),
			]),
			System( 'Finals', [
				Event( ['1C1', '2C1'], '1R', '2R', 3 ),
				Event( ['1C2', '2C2'], '3R', '4R', 3 )
			]),
		])
	]),
	
]

def Simulate( competition ):
	print competition.name, 'Simulation'
	print

	print 'Qualifying Times:'
	for i, (t, rider) in enumerate(competition.getQualifiers()):
		print '%2d: %s %f' % (i+1, rider.full_name, t)
	print
	
	tse = competition.getMeetsPreconditions()
	while tse:
		print
		print 'Facts:'
		print competition.facts.getRepr( competition.labels )
		print
		print 'Available Events:'
		print '\n'.join( e.getRepr(competition.labels, competition.facts) for t, s, e in competition.getMeetsPreconditions() )
		raw_input()
		e = tse[0][2]
		if len(e.composition) == 4:
			place = range(1,5)
			random.shuffle( place )
			print
			for c, p in zip(e.composition, place):
				f = Fact( c, place=p, heat=1 )
				print f.getRepr( competition.labels )
				competition.addFact( f )
		else:
			f = Fact( e.composition[random.randint(0, len(e.composition)-1)], place=1, heat=e.getHeat(competition.facts) )
			print
			print f.getRepr( competition.labels)
			competition.addFact( f )
		tse = competition.getMeetsPreconditions()
		raw_input()
			
	print
	print 'Results:'
	for i, r in enumerate(competition.getResults()):
		print '%2d: %s' % (i+1, r.full_name)

if __name__ == '__main__':
	import random
	import copy
	nameStr = '''JAMES	3.318	 4,840,833	1
JOHN	3.271	 4,772,262	2
ROBERT	3.143	 4,585,515	3
MICHAEL	2.629	 3,835,609	4
WILLIAM	2.451	 3,575,914	5
DAVID	2.363	 3,447,525	6
RICHARD	1.703	 2,484,611	7
CHARLES	1.523	 2,221,998	8
JOSEPH	1.404	 2,048,382	9
THOMAS	1.38	 2,013,366	10
CHRISTOPHER	1.035	 1,510,025	11
DANIEL	0.974	 1,421,028	12
PAUL	0.948	 1,383,095	13
MARK	0.938	 1,368,506	14
DONALD	0.931	 1,358,293	15
GEORGE	0.927	 1,352,457	16
KENNETH	0.826	 1,205,102	17
STEVEN	0.78	 1,137,990	18
EDWARD	0.779	 1,136,531	19
BRIAN	0.736	 1,073,795	20
RONALD	0.725	 1,057,747	21
ANTHONY	0.721	 1,051,911	22
KEVIN	0.671	 978,963	23
JASON	0.66	 962,914	24
MATTHEW	0.657	 958,538	25
GARY	0.65	 948,325	26
TIMOTHY	0.64	 933,735	27
JOSE	0.613	 894,343	28'''

	names = [ n.split()[0] for n in nameStr.split('\n')]
	
	worldCup = competitions[0]
	worldChampionships = competitions[1]
	olympics = competitions[2]
	
	competition = copy.copy( worldCup )
	
	riders = [Rider(101 + i, '', name) for i, name in enumerate(names)]
	for i in xrange(competition.starters):
		competition.addQualifier( riders[i], random.gauss(57/5, 0.5) )
	
	print '--------------------------------------------------------------------'
	Simulate( competition )
	
	'''
	print competition.facts
	print '\n'.join( '%s = %s' % (id, rider.full_name) for id, rider in competition.labels.iteritems())
	print '\n'.join( e.getRepr(competition.labels) for t, s, e in competition.getMeetsPreconditions() )
	
	print
	competition.addFact( Fact('N1', place=1) )
	print '\n'.join( e.getRepr(competition.labels) for t, s, e in competition.getMeetsPreconditions() )
	
	print
	competition.addFact( Fact('N2', place=1) )
	print '\n'.join( e.getRepr(competition.labels) for t, s, e in competition.getMeetsPreconditions() )

	print
	competition.addFact( Fact('N9', place=1) )
	print '\n'.join( e.getRepr(competition.labels) for t, s, e in competition.getMeetsPreconditions() )
	
	print
	competition.addFact( Fact('N13', place=1) )
	print '\n'.join( e.getRepr(competition.labels) for t, s, e in competition.getMeetsPreconditions() )
	'''
	
