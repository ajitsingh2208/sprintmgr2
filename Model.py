import random
import datetime
import traceback

from collections import defaultdict

class Rider( object ):
	def __init__( self, bib, first_name = '', last_name = '', team = '', license = '', qualifyingTime = 60.0 ):
		self.bib = int(bib)
		self.first_name = first_name
		self.last_name = last_name
		self.team = team
		self.license = license
		self.qualifyingTime = qualifyingTime
		
	def copyDataFields( self, r ):
		if r != self:
			for attr in ('first_name', 'last_name', 'team', 'license'):
				setattr( self, attr, getattr(r, attr, '') )
		return self
		
	def key( self ):
		return tuple( getattr(self, a) for a in ('bib', 'first_name', 'last_name', 'team', 'license', 'qualifyingTime') )
		
	def keyDataFields( self ):
		return tuple( getattr(self, a) for a in ('bib', 'first_name', 'last_name', 'team', 'license') )
		
	@property
	def full_name( self ):
		if self.last_name and self.first_name:
			return '%s %s' % (self.first_name, self.last_name)
		return self.last_name if self.last_name else self.first_name
		
	@property
	def short_name( self ):
		if self.last_name and self.first_name:
			return '%s, %s.' % (self.last_name, self.first_name[:1])
		return self.last_name if self.last_name else self.first_name
	
	@property
	def bib_short_name( self ):
		return '%d %s' % (self.bib, self.short_name)
	
	@property
	def long_name( self ):
		n = self.full_name
		return '%s (%s)' % (n, self.team) if self.team else n
		
	def __repr__( self ):
		return '%d: %s' % (self.bib, self.full_name)

#------------------------------------------------------------------------------------------------

class State( object ):
	def __init__( self ):
		self.labels = {}
		self.noncontinue = {}
		self.OpenRider = Rider( 0, '', 'OPEN' )
		self.OpenRider.qualifyingTime = 1000.0
		
	def setQualifyingTimes( self, qtIn, competition ):
		''' Expect qtIn to be of the form [(rider1, t1), (rider2, t2), ...]'''
		self.labels = {}
		qt = [(t, rider) for rider, t in qtIn]
		qt.sort()
		qt = qt[:competition.starters]
		for i, (t, rider) in enumerate(qt):
			self.labels['N%d' % (i+1)] = rider
		# Set extra open spaces to make sure we have enough starters.
		for i in xrange(len(qtIn), 64):
			self.labels['N%d' % (i+1)] = self.OpenRider
		self.OpenRider.qualifyingTime =  1000.0

	def inContention( self, id ):
		return self.labels.get(id, None) != self.OpenRider and id not in self.noncontinue
		
	def getQualifyingTimes( self ):
		riders = [rider for label, rider in self.labels.iteritems() if label.startswith('N') and rider != self.OpenRider]
		return sorted( (rider.qualifyingTime, rider) for rider in riders )
		
	def canReassignStarters( self ):
		''' Check if not competitions have started and we can reasign starters. '''
		return all( label.startswith('N') for label in self.labels.iterkeys() )

#------------------------------------------------------------------------------------------------

class Start( object ):
	def __init__( self, event, lastStart ):
		self.event = event
		self.lastStart = lastStart
		self.startPositions = []
		self.places = {}		# In the format of places[composition] = place, place in 1, 2, 3, 4, etc.
		self.times = {}			# In the format of times[1] = winner's time, times[2] = runner up's time, etc.
		self.relegated = []		# Rider assigned a loss in this heat.
		self.inside = []		# Rider required to take inside position on next start.
		self.noncontinue = {}	# In the format of noncontinue[composition] = reason
		self.restartRequired = False
		self.canDrawLots = False

		remainingComposition = self.getRemainingComposition()
		
		if not lastStart:
			self.heat = 1
			self.firstStartInHeat = True
			self.startPositions = [c for c in remainingComposition]
			random.shuffle( self.startPositions )
			self.canDrawLots = True
		else:
			if lastStart.restartRequired:
				self.firstStartInHeat = False
				self.heat = lastStart.heat
				self.startPositions = [r for r in lastStart.inside] + \
						[c for c in lastStart.startPositions if c not in lastStart.inside]
				self.canDrawLots = False
			else:
				self.heat = lastStart.heat + 1
				self.firstStartInHeat = True
				if   self.heat == 2:
					# Find the non-restarted start of the heat.
					s = lastStart
					while s and not s.firstStartInHeat:
						s = s.lastStart
					self.startPositions = [r for r in lastStart.inside] + \
							[c for c in reversed(s.startPositions) if c not in lastStart.inside]
					self.canDrawLots = False
				elif self.heat == 3:
					if lastStart.inside:
						# Don't randomize the start positions again if the last run had a relegation.
						self.startPositions = [r for r in lastStart.inside] + \
								[c for c in lastStart.startPositions if c not in lastStart.inside]
						self.canDrawLots = False
					else:
						# Randomize the start positions again.
						self.startPositions = [c for c in remainingComposition]
						random.shuffle( self.startPositions )
						self.canDrawLots = True
				else:
					assert False, 'Cannot have more than 3 heats'
					
		state = event.competition.state
		self.startPositions = [c for c in self.startPositions if state.inContention(c)]

	def isHanging( self ):
		''' Check if there are no results, and this is not a restart.  If so, this start was interrupted and needs to be removed. '''
		if self.restartRequired:
			return False
		if self.places:
			return False
		return True
		
	def setPlaces( self, places ):
		''' places is of the form [(bib, status), (bib, status), ...] '''
		state = self.event.competition.state
		
		remainingComposition = self.getRemainingComposition()
		bibToId = dict( (state.labels[c].bib, c) for c in remainingComposition )
		
		place = 0
		for bib, status in places:
			id = bibToId[int(bib)]
			if not status:
				place += 1
				self.places[id] = place
			elif status == 'Rel':
				self.addRelegation( id ) 
			elif status == 'Inside':
				self.addInside( id ) 
			else:
				self.noncontinue[id] = status
	
	def setTimes( self, times ):
		''' times is of the form [(pos, t), (pos, t), ...] '''
		self.times = dict( times )
	
	def addRelegation( self, id ):
		self.relegated.append( id )
		
	def addInside( self, id ):
		self.inside.append( id )
		
	def getRemainingComposition( self ):
		state = self.event.competition.state
		return [c for c in self.event.composition if state.inContention(c)]
		
#------------------------------------------------------------------------------------------------

class Event( object ):
	def __init__( self, composition, winner, others, heatsMax ):
		self.composition = composition
		self.winner = winner
		if not isinstance( others, list ):
			others = [others]
		self.others = others
		self.heatsMax = heatsMax
		self.starts = []
		
		# The following fields are set by the competition.
		self.competition = None
		self.system = None
		self.tournament = None
		
	def getHeat( self ):
		heats = sum( 1 for s in self.starts if not s.restartRequired )
		return min(heats, self.heatsMax)
	
	def getHeatPlaces( self, heat ):
		state = self.competition.state
		remainingComposition = [c for c in self.composition if state.inContention(c)]
		
		heatCur = 0
		for start in self.starts:
			if start.restartRequired:
				continue
			heatCur += 1
			if heatCur != heat:
				continue
			
			placeStatus = start.noncontinue.copy()
			for c in remainingComposition:
				if c not in placeStatus:
					placeStatus[c] = str(start.places.get(c, ''))
			heatPlaces = [placeStatus.get(c, '') for c in remainingComposition]
			heatPlaces = ['Win' if p == '1' else '-' for p in heatPlaces]
			return heatPlaces
			
		return [''] * len(remainingComposition)
	
	def __repr__( self ):
		state = self.competition.state
		remainingComposition = [c for c in self.composition if state.inContention(c)]
		remainingOthers = self.others[:len(remainingComposition)-1]
		def labName( id ):
			return '%s=%-12s' % (id, state.labels[id].full_name) if id in state.labels else '%s' % id
		s = '%s, Heat %d/%d  Start %d:  %s => %s %s' % (
			self.system.name,
			self.getHeat(), self.heatsMax, len(self.starts),
			' '.join(labName(c) for c in remainingComposition),
			labName(self.winner),
			' '.join(labName(c) for c in remainingOthers) )
		if self.tournament.name:
			s = '[%s] %s' % (self.tournament.name, s)
		return s
	
	@property
	def multi_line_name( self ):
		return '%s%s\nHeat %d/%d' % ('"%s" ' % self.tournament.name if self.tournament.name else '', self.system.name, self.getHeat(), self.heatsMax)
		
	@property
	def multi_line_bibs( self ):
		state = self.competition.state
		remainingComposition = [c for c in self.composition if state.inContention(c)]
		return '\n'.join((str(state.labels[c].bib)) for c in remainingComposition)
		
	@property
	def multi_line_rider_names( self ):
		state = self.competition.state
		remainingComposition = [c for c in self.composition if state.inContention(c)]
		return '\n'.join(state.labels[c].full_name for c in remainingComposition)
		
	@property
	def multi_line_rider_teams( self ):
		state = self.competition.state
		remainingComposition = [c for c in self.composition if state.inContention(c)]
		return '\n'.join(state.labels[c].team for c in remainingComposition)
		
	@property
	def multi_line_inlabels( self ):
		state = self.competition.state
		remainingComposition = [c for c in self.composition if state.inContention(c)]
		return '\n'.join( remainingComposition )
	
	@property
	def multi_line_outlabels( self ):
		state = self.competition.state
		remainingComposition = [c for c in self.composition if state.inContention(c)]
		outlabels = [self.winner]
		outlabels.extend( self.others[0:len(remainingComposition)-1] )
		return '\n'.join( outlabels )
	
	def getRepr( self ):
		return self.__repr__()
	
	def getStart( self ):
		if not self.canStart():
			return None
		self.starts.append( Start(self, self.starts[-1] if self.starts else None) )
		return self.starts[-1]
	
	def isFinished( self ):
		return self.winner in self.competition.state
	
	def canStart( self ):
		state = self.competition.state
		return  all(c in state.labels for c in self.composition) and \
				any(state.inContention(c) for c in self.composition) and \
				self.winner not in state.labels
	
	def propagate( self ):
		if not self.canStart():
			#print ', '.join(self.composition), 'Cannot start or already finished - nothing to propagate'
			return False
			
		state = self.competition.state
		
		# Update all non-continuing riders into the competition state.
		for s in self.starts:
			state.noncontinue.update( s.noncontinue )
			if len(self.composition) > 2:
				for r in s.relegated:
					state.noncontinue[r] = 'Rel'
		
		# Check for a default winner.
		remainingComposition = [c for c in self.composition if state.inContention(c)]
		
		if len(remainingComposition) == 1:
			state.labels[self.winner] = state.labels[remainingComposition[0]]
			# Mark the "others" as open riders.
			for o in self.others:
				state.labels[o] = state.OpenRider
			return True
			
		# Check if we have a rider with a majority of wins in the heats.
		winCount = defaultdict( int )
		for s in self.starts:
			if s.restartRequired:
				continue
			for p, v in s.places.iteritems():
				if v != 1 or not state.inContention(p):
					continue
				winCount[p] += 1
				if winCount[p] < self.heatsMax - 1:
					continue
				
				# We have a winner of the event.  Propagate the results.
				# Set the winner.
				state.labels[self.winner] = state.labels[p]
				
				# Set the "others" to the remaining placed riders.
				finishOrder = [c for c in self.composition if c != p and state.inContention(c)]
				finishOrder.sort( key = lambda c: s.places[c] )
				
				# If this is a 3 or 4 rider race, check if any riders were relegated.
				# If so, add them to the finish order.
				if len(self.composition) > 2:
					for stateRel in reversed(self.starts):
						for r in stateRel.relegated:
							if r not in finishOrder:
								finishOrder.append( r )
				
				# Set the labels of the finishers.
				for o, c in zip(self.others, finishOrder):
					state.labels[o] = state.labels[c]
					
				# Set any extra others to "OpenRider".
				for i in xrange(len(finishOrder), len(self.others)):
					state.labels[self.others[i]] = state.OpenRider
				return True
				
		return False

#------------------------------------------------------------------------------------------------

class Competition( object ):
	def __init__( self, name, starters, tournaments ):
		self.name = name
		self.starters = starters
		self.tournaments = tournaments
		self.state = State()
		
		# Check that there are no repeated labels in the spec.
		inLabels = set()
		outLabels = set()
		for t, s, e in self.allEvents():
			e.competition = self
			e.system = s
			e.tournament = t
			s.tournament = t
			for c in e.composition:
				assert c not in inLabels
				inLabels.add( c )
			assert e.winner not in outLabels
			outLabels.add( e.winner )
			for c in e.others:
				assert c not in outLabels
				outLabels.add( c )
				
		# Assign indexes to each component for sorting purposes.
		for i, tournament in enumerate(self.tournaments):
			tournament.i = i
			for j, system in enumerate(tournament.systems):
				system.i = j
				for k, event in enumerate(system.events):
					event.i = k
	
	def canReassignStarters( self ):
		return self.state.canReassignStarters()
	
	def allEvents( self ):
		for tournament in self.tournaments:
			for system in tournament.systems:
				for event in system.events:
					yield tournament, system, event
	
	def fixHangingStarts( self ):
		for t, s, e in self.allEvents():
			while e.starts and e.starts[-1].isHanging():
				del e.starts[-1]
	
	def getCanStart( self ):
		return [(t, s, e) for t, s, e in self.allEvents() if e.canStart()]
		
	def propagate( self ):
		while 1:
			success = False
			for t, s, e in self.allEvents():
				success |= e.propagate()
			if not success:
				break
		labels = self.state.labels
		return [ labels.get('%dR' % (r+1), None) for r in xrange(self.starters) ]

	def getResults( self ):
		results = [None] * self.starters
		
		# Rank the rest of the riders based on their results in the competition.
		for i in xrange(self.starters):
			try:
				results[i] = self.state.labels['%dR' % (i+1)]
			except KeyError:
				pass

		# Rank the remaining riders based on qualifying time.
		iTT = self.starters
		tts = [rider for label, rider in self.state.labels.iteritems() if label.endswith('TT')]
		tts.sort( key = lambda r: r.qualifyingTime, reverse = True )	# Sort these in reverse as we assign them in from most to least.
		for rider in tts:
			iTT -= 1
			results[iTT] = rider
			
		# Get the DNF and DQ'd riders.
		DQs = set( self.state.labels[id] for id, reason in self.state.noncontinue.iteritems() if reason == 'DQ' )
		DNFs = set( self.state.labels[id] for id, reason in self.state.noncontinue.iteritems()
					if reason == 'DNF' and self.state.labels[id] not in DQs )
		
		return (	results,
					sorted(DNFs, key = lambda r: r.qualifyingTime),
					sorted(DQs,  key = lambda r: r.qualifyingTime) )
		
class Tournament( object ):
	def __init__( self, name, systems ):
		self.name = name
		self.systems = systems

class System( object ):
	def __init__( self, name, events ):
		self.name = name
		self.events = events

class Model( object ):
	def __init__( self ):
		self.competition_name = 'My Competition'
		self.date = datetime.date.today()
		self.category = 'My Category'
		self.track = 'My Track'
		self.organizer = 'My Organizer'
		self.chief_official = 'My Chief Official'
		self.competition = None
		self.riders = []
		self.changed = False
		self.showResults = 0
		
	def setQualifyingTimes( self ):
		qt = [(r, r.qualifyingTime) for r in self.riders]
		self.competition.state.setQualifyingTimes( qt, self.competition )
		
	def canReassignStarters( self ):
		return self.competition.state.canReassignStarters()
		
	def setChanged( self, changed ):
		self.changed = changed
		
model = Model()

