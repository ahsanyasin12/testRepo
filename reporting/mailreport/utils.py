def insertfile(infile, outfile, line, analysis):
	data = open(infile,"r").read()	
	temp = open(outfile, 'r').readlines()
	temp.insert(line,data)
	f2 = open(outfile, "w")
	f2.write(''.join(temp))
	f2.close()

	print(">>> HTML Report modified").format(analysis['_id'])

def fileline(report, css, analysis):
	linecounter = 0

	with open(report, 'r+') as fh:
		for line in fh:
			linecounter += 1
			if line.startswith('<head>'):		
				break

	insertfile(css, report, linecounter, analysis)

