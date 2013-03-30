def getTestData():
	results = '''
1	Gregory Bauge (France)	9.854	 
2	Robert Foerstemann (Germany)	9.873	 
3	Kevin Sireau (France)	9.893	 
4	Chris Hoy (Great Britain)	9.902	 
5	Matthew Glaetzer (Australia)	9.902	 
6	Jason Kenny (Great Britain)	9.953	 
7	Edward Dawkins (New Zealand)	9.963	 
8	Shane Perkins (Australia)	9.965	 
9	Mickael Bourgain (France)	9.966	 
10	Stefan Boetticher (Germany)	9.983	 
11	Seiichiro Nakagawa (Japan)	10.003	 
12	Matthew Archibald (New Zealand)	10.034	 
13	Scott Sunderland (Australia)	10.040	 
14	Miao Zhang (People's Republic of China)	10.061	 
15	Hersony Canelon (Venezuela)	10.077	 
16	Rene Enders (Germany)	10.077	 
17	Juan Peralta Gascon (Spain)	10.101	 
18	Michael Blatchford (United States Of America)	10.118	 
19	Sam Webster (New Zealand)	10.122	 
20	Kazunari Watanabe (Japan)	10.159	 
21	Ethan Mitchell (New Zealand)	10.163	 
22	Hodei Mazquiaran Uria (Spain)	10.163	 
23	Matthew Crampton (Great Britain)	10.167	 
24	Charlie Conord (France)	10.169	 
25	Nikita Shurshin (Russian Federation)	10.178	 
26	Damian Zielinski (Poland)	10.192
'''

	testData = []
	
	for line in results.split( '\n' ):
		fields = line.split()
		if len(fields) < 2:
			continue
		bib = fields[0]
		first_name = ''
		last_name = ''
		team = ''
		qt = float(fields[-1])
		
		i = len(fields) - 2
		while 1:
			team = fields[i] + (' ' if team else '') + team
			if fields[i].startswith('('):
				break
			i -= 1
		team = team[1:-1]
				
		i -= 1
		last_name = fields[i]
		
		i -= 1
		while i > 0:
			first_name = fields[i] + (' ' if first_name else '') + first_name
			i -= 1
			
		testData.append( (bib, first_name, last_name, team, qt) )

	testData.reverse()
	return testData
