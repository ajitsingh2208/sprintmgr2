from Model import Competition, Tournament, System, Event
import Model
from TestData import getTestData

def getCompetitions():
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
					Event( ['1P', '2P', '3P', '4P'], '5R', ['6R', '7R', '8R'], 1 )
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
					Event( ['N1', 'N24'], '1A', '1TT', 1 ),
					Event( ['N2', 'N23'], '2A', '2TT', 1 ),
					Event( ['N3', 'N22'], '3A', '3TT', 1 ),
					Event( ['N4', 'N21'], '4A', '4TT', 1 ),
					Event( ['N5', 'N20'], '5A', '5TT', 1 ),
					Event( ['N6', 'N19'], '6A', '6TT', 1 ),
					Event( ['N7', 'N18'], '7A', '7TT', 1 ),
					Event( ['N8', 'N17'], '8A', '8TT', 1 ),
					Event( ['N9', 'N16'], '9A', '9TT', 1 ),
					Event( ['N10', 'N15'], '10A', '10TT', 1 ),
					Event( ['N11', 'N14'], '11A', '11TT', 1 ),
					Event( ['N12', 'N13'], '12A', '12TT', 1 ),
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
					Event( ['1B2', '4B2', '6B2'], '1C', ['13TT', '14TT'], 1 ),
					Event( ['2B2', '3B2', '5B2'], '2C', ['15TT', '16TT'], 1 ),
				]),
				System( '1/4 Finals', [
					Event( ['1B1', '2C'], '1D', '1P', 3 ),
					Event( ['2B1', '1C'], '2D', '2P', 3 ),
					Event( ['3B1', '6B1'], '3D', '3P', 3 ),
					Event( ['4B1', '5B1'], '4D', '4P', 3 ),
					Event( ['1P', '2P', '3P', '4P'], '5R', ['6R', '7R', '8R'], 1 )
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
					Event( ['1P', '2P', '3P', '4P'], '9R', ['10R', '11R', '12R'], 1 )
				]),
				System( '1/4 Finals', [
					Event( ['1C1', '2D'],  '1F', '1Q', 3 ),
					Event( ['2C1', '1D'],  '2F', '2Q', 3 ),
					Event( ['3C1', '6C1'], '3F', '3Q', 3 ),
					Event( ['4C1', '5C1'], '4F', '4Q', 3 ),
					Event( ['1Q', '2Q', '3Q', '4Q'], '5R', ['6R', '7R', '8R'], 1 )
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
		
		Competition( '1/2 World Championships', 12, [
			Tournament( '', [
				System( '1/8 Finals', [
					Event( ['N1', 'N12'], '1B1', '1B2', 1 ),
					Event( ['N2', 'N11'], '2B1', '2B2', 1 ),
					Event( ['N3', 'N10'], '3B1', '3B2', 1 ),
					Event( ['N4', 'N9'], '4B1', '4B2', 1 ),
					Event( ['N5', 'N8'], '5B1', '5B2', 1 ),
					Event( ['N6', 'N7'], '6B1', '6B2', 1 ),
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
					Event( ['1P', '2P', '3P', '4P'], '5R', ['6R', '7R', '8R'], 1 )
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
		
		Competition( '1/2 World Cup', 8, [
			Tournament( '', [
				System( '1/4 Finals', [
					Event( ['N1', 'N8'], '1B', '1P', 1 ),
					Event( ['N2', 'N7'], '2B', '2P', 1 ),
					Event( ['N3', 'N6'], '3B', '3P', 1 ),
					Event( ['N4', 'N5'], '4B', '4P', 1 ),
					Event( ['1P', '2P', '3P', '4P'], '5R', ['6R', '7R', '8R'], 1 )
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
	return competitions

def SetDefaultData():
	model = Model.Model()
	for competition in getCompetitions():
		#if 'Olympic' in competition.name:
		#if '1/2 World Cup' in competition.name:
		if 'World Championships' in competition.name:
			model.competition = competition
			break
	testData = getTestData()
	for bib, first_name, last_name, team, qt in testData:
		rider = Model.Rider( bib, first_name, last_name, team, '', qt )
		model.riders.append( rider )
		
	model.setQualifyingTimes()
	Model.model = model
	return model
		