"""
	A simple parser for the ccndstatus info
"""

import re, datetime
import pdb
from influxdb import InfluxDBClient

contentItems ={}
interests = {}
iTotals = {}
facesStats = []
facesRates = []
forwarding=[]

contentList=[]
dataList=[]

datapoints=[]

ccndout = open('ccndout').read().splitlines()
lineCount = len(ccndout)

for line in xrange(1, 4):
    pdb.set_trace()
    splitLine=re.split(': ',ccndout[line])
    rest=re.split(', ', splitLine[1])

    for item in rest:
        itemSplit=re.split(' ', item)
        if(line == 1):
            contentItems[itemSplit[1]] = itemSplit[0]
        elif(line == 2):
            interests[itemSplit[1]] = itemSplit[0]
        elif(line == 3):
            iTotals[itemSplit[1]] = itemSplit[0]

contentList.append({"name": 'content_items', "data": contentItems})
contentList.append({"name": 'interests', "data": interests})
contentList.append({"name": 'interest_totals', "data": iTotals})

line = 5

while (ccndout[line] != 'Face Activity Rates'):
	splitLine=re.split(' ', ccndout[line])
	try:
		rest=splitLine[8]
	except IndexError:
		rest = ''

	faceInfo={
		"face":		splitLine[2],
		"flags":	splitLine[4],
		"pending":	splitLine[6],
		"local": 	rest,
	}
	
	facesStats.append({"name": 'faces', "data": faceInfo})
	line += 1

line += 2

while (ccndout[line] != 'Forwarding'):
	face = re.split(': ', re.search('face: [0-9]+', ccndout[13]).group(0))
	faceStat = re.findall('[0-9]+ / [0-9]+', ccndout[line])

	Bytes=re.split(' / ', faceStat[0])
	rData=re.split(' / ', faceStat[1])
	sData=re.split(' / ', faceStat[2])

	faceInfo={
		"face":		face[1],
		"BIn":		Bytes[0],
		"BOut":		Bytes[1],
		"rData":	rData[0],
		"sInt":		rData[1],
		"sData":	sData[0],
		"rInt":		sData[1],
	}

	facesRates.append({"name": 'face_activity_rates', "data": faceInfo})

	line += 1

line += 1

while (line < (lineCount-1)):

	splitLine=re.split(' ', ccndout[line])
	
	faceInfo={
		"path":		splitLine[1],
		"face":		splitLine[3],
		"flags":	splitLine[5],
		"expires":	splitLine[7],
	}

	forwarding.append({"name": 'forwarding', "data": faceInfo})

	line += 1

dataList.append(contentList)
dataList.append(facesStats)
dataList.append(facesRates)
dataList.append(forwarding)

pdb.set_trace()

for data in dataList:
    for series in data:
        newEntry={
            "name": series['name'],
            #"tags": None,
            "time": datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            "fields": series['data']
        }
	
        datapoints.append(newEntry)

host='localhost'
port=8086
user='root'
passwd='root'
dbname='mn_ccnx_data'

client = InfluxDBClient(host, port, user, passwd, dbname)
client.drop_database(dbname)
client.create_database(dbname)
client.write_points(datapoints)

pdb.set_trace()
