"""
Metrics colector for mn-ccnx.
The Metrics Collector class should be instantiated in every node to interact with the database.
The DBManager class is a singleton and its purpose is to manage the database.
Author: Caio Elias; 
"""

#import argparse
import re
import datetime
import threading
from mininet.log import info
#from subprocess import Popen, PIPE, STDOUT

#backwards compatible library fo InfluxDB 0.8:
#from influxdb.influxdb08 import InfluxDBClient

#for InfluxDB 0.9 and above:
from influxdb import InfluxDBClient

import pdb

class MetricsCollector(object):
    """ A simple agent to collect ccndstatus output and insert it into the selected database"""

    def getCCNStatus(self):
        
        ccndout=self.ccnhost.cmd('ccndstatus').splitlines()
        
        output={
            "host": str(self.ccnhost),
            "ccndstatus": ccndout,
        }

        return output
    
    def ccndstatusParser(self, data):
        """Reads output from command ccndstatus, parse it, 
            and return a list ready to be written into influxDB.
            Note that this is function was built specifically for
            parsing the contents of ccndstatus' output by the way 
            it is formatted in CCNx version 0.8.2. In case of version 
            changes, this code might need to be updated too!"""

        contentItems ={}
        interests = {}
        iTotals = {}
        facesStats = []
        facesRates = []
        forwarding=[]

        contentList=[]
        dataList=[]

        datapoints=[]

        #print ccndout = open('ccndout').read().splitlines()
        hostname = data['host']
        ccndout = data['ccndstatus']
        lineCount = len(ccndout)

        for line in xrange(1, 4):    
            splitLine=re.split(': ', ccndout[line])
            rest=re.split(', ', splitLine[1])
            
            for item in rest:
                itemSplit=re.split(' ', item)
                if(line == 1):
                    contentItems[itemSplit[1]] = itemSplit[0]
                elif(line == 2):
                    interests[itemSplit[1]] = itemSplit[0]
                elif(line == 3):
                    iTotals[itemSplit[1]] = itemSplit[0]

        contentItems['host']=hostname
        interests['host']=hostname
        iTotals['host']=hostname

        contentList.append({"name": 'content_items', "data": contentItems})
        contentList.append({"name": 'interests', "data": interests})
        contentList.append({"name": 'interest_totals', "data": iTotals})

        line = 5

        while (ccndout[line] != 'Face Activity Rates'):
            local=''
            remote=''
            face=''
            flags=''
            pending=''
            count=1;

            splitLine=re.split(' ', ccndout[line])
            for item in splitLine:

                try:
                    if (splitLine[count]=='face:'):
                        face = splitLine[count+1]
                    elif (splitLine[count]=='flags:'):
                        flags = splitLine[count+1]
                    elif (splitLine[count]=='pending:'):
                        pending = splitLine[count+1]
                    elif (splitLine[count]=='local:'):
                        local = splitLine[count+1]
                    elif (splitLine[count]=='remote:'):
                        remote = splitLine[count+1]
                    count += 2
                except IndexError:
                    break

            faceInfo={
                "face":     face,
                "flags":    flags,
                "pending":  pending,
                "local":    local,
                "remote":   remote,
                "host":     hostname,
            }
    
            facesStats.append({"name": 'faces', "data": faceInfo})
            line += 1

        line += 2

        while (ccndout[line] != 'Forwarding'):
            face = re.split(': ', re.search('face: [0-9]+', ccndout[line]).group(0))
            faceStat = re.findall('[0-9]+ / [0-9]+', ccndout[line])

            Bytes=re.split(' / ', faceStat[0])
            rData=re.split(' / ', faceStat[1])
            sData=re.split(' / ', faceStat[2])

            faceInfo={
                "face":     face[1],
                "BIn":      Bytes[0],
                "BOut":     Bytes[1],
                "rData":    rData[0],
                "sInt":     rData[1],
                "sData":    sData[0],
                "rInt":     sData[1],
                "host":     hostname,
            }

            facesRates.append({"name": 'face_activity_rates', "data": faceInfo})

            line += 1

        line += 1

        while (line < (lineCount-1)):

            splitLine=re.split(' ', ccndout[line])
    
            faceInfo={
                "path":     splitLine[1],
                "face":     splitLine[3],
                "flags":    splitLine[5],
                "expires":  splitLine[7],
                "host":     hostname,
            }

            forwarding.append({"name": 'forwarding', "data": faceInfo})

            line += 1

        dataList.append(contentList)
        dataList.append(facesStats)
        dataList.append(facesRates)
        dataList.append(forwarding)


        for data in dataList:
            for series in data:
                newEntry={
                    "name": series['name'],
                    #"tags": None,
                    "time": datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                    "fields": series['data']
                }
    
                datapoints.append(newEntry)
        
        return datapoints

    def checkDatabase(self, dbname='miniccnx_data'):
        dblist=self.client.get_list_database()
        
        for database in dblist:
            if(database['name'] == dbname):
                return True;

        return False

    def writeToDatabase(self, datapoints):
        self.client.write_points(datapoints)
        
    def scheduledTasks(self):

        self.scheduler = threading.Timer(self.timerInt, self.scheduledTasks)
        self.scheduler.start()
        #print ("Collecting data at %s!" % self.ccnhost)
        ccndout = self.getCCNStatus()

        if(len(ccndout['ccndstatus']) > 0):
            datapoints = self.ccndstatusParser(ccndout)
            self.writeToDatabase(datapoints)
            #print("Alright at " + ccndout['host'])
        else:
            print("Problem collecting data at " + ccndout['host'])

    def stop(self):
        self.scheduler.cancel()
        if(self.scheduler.isAlive()):
            self.scheduler.join(self.timerInt)

    def __init__ (self, host, timer, dbPrefs):

        if(dbPrefs['dbHost']):
            dbhost = dbPrefs['dbHost']
        else:
            dbhost = 'localhost'

        if(dbPrefs['dbPort']):
            dbport = dbPrefs['dbPort']
        else:
            dbport = 8086

        if(dbPrefs['dbUser']):
            dbuser = dbPrefs['dbUser']
        else:
            dbuser = 'root'

        if(dbPrefs['dbPass']):
            dbpass = dbPrefs['dbPass']
        else:
            dbpass = 'root'

        if(dbPrefs['dbName']):
            self.dbname = dbPrefs['dbName']
        else:
            #do not use hifens '-' in the database name! InfluxDB doesn't like them
            self.dbname = 'miniccnx_data'

        self.client = InfluxDBClient(dbhost, dbport, dbuser, dbpass, self.dbname)

        self.ccnhost = host
        self.timerInt = float(timer)

        if(not self.checkDatabase(self.dbname)):
            info( 'Host %s: creating database %s.\n' % (str(self.ccnhost),self.dbname)) 
            self.client.create_database(self.dbname)
        else:
            info( 'Host %s: database %s already exists: appending data.\n' % (str(self.ccnhost),self.dbname)) 

        self.scheduler = None

        #while(self.scheduler.isAlive()):
        #    pass
        #self.scheduler.start() 
        self.scheduledTasks()

class DBManager ():
    
    def createDatabase(self, createdb = 'miniccnx_data'):
        """ Creates a database on the specified host. 
            Returns true if database was created, false otherwise. """

        if(self.lookForDatabase(createdb)):
            print("Database: %s already exists. Nothing to be done." % createdb)
            return False
        else:
            self.client.create_database(createdb)

        if(self.lookForDatabase(createdb)):
            print("Database: %s created successfully!" % createdb)
            return True
        else:
            #raise RuntimeError("Unable to create Database " + createdb)
            print("Unable to create Database " + createdb)
            return False

    def listDatabases(self):
        """ Returns a list of all existing databases """

        dbs=self.client.get_list_database()
        dblist=[]

        for database in dbs:
            dblist.append(database['name'])

        return dblist

    def lookForDatabase(self, lookupDB = 'miniccnx_data' ):
        """ Returns TRUE if a database exists in the host. False otherwise. """

        dblist=self.client.get_list_database()

        for database in dblist:
            if(database['name'] == lookupDB):
                return True

        return False

    def dropAllDatabases(self):
        """ Drops all databases on selected host. """
        
        dblist=self.client.get_list_database()

        for database in dblist:
            self.client.drop_database(database['name'])

    def dropDatabase(self, dropdb = 'miniccnx_data'):
        """ Drops a specific database on selected host.
            Returns true if database was dropped. False otherwise. """

        if(self.lookForDatabase(dropdb)):
            self.client.drop_database(dropdb)
        else:
            print("Database: %s does not exist." % dropdb)
            return False

        if(not self.lookForDatabase(dropdb)):
            print("Database: %s dropped successfully!" % dropdb)
            return True
        else:
            print("Something is not right. Database: %s was not dropped." % dropdb)
            return False

    def createUser(self, newUser = 'newRoot', newPasswd = 'newRoot'):
        """ Creates a new InfluxDB user in selected host """

        self.client.create_user(newUser, newPasswd)

    def removeUser(self, dropUser = 'oldRoot'):
        """ Removes an user from InfluxDB in selected host """

        self.client.drop_user(dropUser)

    def listUsers(self):
        """ Returns a list of all existing users in InfluxDB """

        users=self.client.get_list_users()
        userslist=[]

        for user in users:
            userslist.append(user['name'])

        return userslist
    

    def listSeries(self, db='miniccnx_data'):
        """ Returns a list of all existing series in the database """

        if(not self.lookForDatabase(db)):
            print("Specified database does not exist. Create it using 'createdb %s' command." % db)
            return []

        sl=self.client.get_list_series(db)
        serieslist=[]

        for serie in sl:
            serieslist.append(serie['name'])

        return serieslist

    def queryDB(self, query = "", db='miniccnx_data'):
        """ Queries the database returns the result """

        result = self.client.query(query, database=db)
        return result

    def __init__ (self):
        dbhost = 'localhost'
        dbport = 8086
        dbuser = 'root'
        dbpass = 'root'
        #do not use hifens '-' in the database name! InfluxDB doesn't like them
        self.dbname = 'miniccnx_data'
        self.client = InfluxDBClient(dbhost, dbport, dbuser, dbpass)

        
