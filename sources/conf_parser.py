import ConfigParser, re
import pdb

class confCCNHost():

    def __init__(self, name, app='', uri_tuples='', cpu=None, cores=None, cache=None, startCommand=''):
        self.name = name
        self.app = app
        self.uri_tuples = uri_tuples
        self.cpu = cpu
        self.cores = cores
        self.cache = cache

    def __repr__(self):
        return 'Name: ' + self.name + ' Start Command: ' + self.app + ' URIS: ' + str(self.uri_tuples) + ' CPU:' + str(self.cpu) + ' Cores:' +str(self.cores) + ' Cache: ' + str(self.cache)

class confSwitch():

    def __init__(self, name, switchType='', stopCommand='', sflow=None, switchIP='', dpid=None, dpctl='', startCommand='', netflow=None, externalInterfaces='', controllers=''):
        self.name = name
        self.switchType = switchType
        self.stopCommand = stopCommand
        self.sflow = sflow
        self.switchIP = switchIP
        self.dpid = dpid
        self.dpctl = dpctl
        self.startCommand = startCommand
        self.netflow = netflow
        self.externalInterfaces = externalInterfaces
        self.controllers = controllers

    def __repr__(self):
        return 'Name: ' + self.name + ' SwitchType: ' + self.switchType + ' StopCommand: ' + self.stopCommand + ' sflow:' + str(self.sflow) + ' SwitchIP:' + self.switchIP + ' dpid: ' + str(self.dpid) + ' dpctl: ' + self.dpctl + ' StartCommand: ' + self.startCommand + ' Netflow: ' + str(self.netflow) + ' ExternalInterfaces: ' + ','.join(self.externalInterfaces) + ' Controllers: ' + ','.join(self.controllers)

class confController():

    def __init__(self, name, remotePort=None, controllerProtocol='', remoteIP='', controllerType=''):
        self.name = name
        self.remotePort = remotePort
        self.controllerProtocol = controllerProtocol
        self.remoteIP = remoteIP
        self.controllerType = controllerType

    def __repr__(self):
        return 'Name: ' + self.name + ' RemotePort: ' + str(self.remotePort) + ' controllerProtocol: ' + self.controllerProtocol + ' RemoteIP:' + self.remoteIP + ' ControllerType:' + self.controllerType


class confCCNLink():

    def __init__(self,h1,h2,linkDict=None):
        self.h1 = h1
        self.h2 = h2
        self.linkDict = linkDict

    def __repr__(self):
        return 'h1: ' + self.h1 + ' h2: ' + self.h2 + ' params: ' + str(self.linkDict)

def parse_hosts(conf_arq):
    'Parse hosts section from the conf file.'
    config = ConfigParser.RawConfigParser()
    config.read(conf_arq)

    hosts = []

    items = config.items('hosts')

    #makes a first-pass read to hosts section to find empty host sections
    for item in items:
        name = item[0]
        rest = item[1].split()
        if len(rest) == 0:
            config.set('hosts', name, '_')
            #updates 'items' list
    items = config.items('hosts')

    #makes a second-pass read to hosts section to properly add hosts
    for item in items:
        name = item[0]

        rest = item[1].split("'")

        if (len(rest) > 1):
                app = rest[1]
                uris = rest[2].split()
        else: 
                uris = item[1].split()
                app='_'

        uri_list=[]
        cpu = None
        cores = None
        cache = None

        if '_' in uris:
            pass
        else:
            for uri in uris:
                if re.match("cpu",uri):
                    cpu = float(uri.split('=')[1])
                elif re.match("cores",uri):
                    cores = uri.split('=')[1]
                elif re.match("cache",uri):
                    cache = uri.split('=')[1]
                elif re.match("mem",uri):
                    mem = uri.split('=')[1]         
                else:
                    uri_list.append((uri.split(',')[0],uri.split(',')[1]))

        hosts.append(confCCNHost(name, app, uri_list, cpu, cores, cache))

    return hosts

def parse_routers(conf_arq):
    'Parse routers section from the conf file.'
    config = ConfigParser.RawConfigParser()
    config.read(conf_arq)

    routers = []

    items = config.items('routers')

    for item in items:
        name = item[0]

        rest = item[1].split()

        uri_list=[]

        cpu = None
        cores = None
        cache = None

        if '_' in rest:
            pass
        else:
            for opt in rest:
                if re.match("cpu",opt):
                    cpu = float(opt.split('=')[1])
                elif re.match("cores",opt):
                    cores = opt.split('=')[1]
                elif re.match("cache",opt):
                    cache = opt.split('=')[1]
                elif re.match("mem",opt):
                    mem = opt.split('=')[1]
                else:
                    uri_list.append((opt.split(',')[0],opt.split(',')[1]))

        routers.append(confCCNHost(name=name, uri_tuples=uri_list, cpu=cpu, cores=cores, cache=cache))

    return routers

def parse_links(conf_arq):
    'Parse links section from the conf file.'
    arq = open(conf_arq,'r')

    links = []

    while True:
        line = arq.readline()
        if line == '[links]\n':
            break

    while True:
        line = arq.readline()
        if line == '':
            break

        args = line.split()
    
        #checks for non-empty line
        if len(args) == 0:
            continue

        h1, h2 = args.pop(0).split(':')

        link_dict = {}

        for arg in args:
            arg_name, arg_value = arg.split('=')
            key = arg_name
            value = arg_value
            if key in ['bw','jitter','max_queue_size']:
                value = int(value)
            if key in ['loss']:
                value = float(value)
            link_dict[key] = value

        links.append(confCCNLink(h1,h2,link_dict))

    return links

def parse_switches(conf_arq):
    'Parse switches section from the conf file.'
    config = ConfigParser.RawConfigParser()
    config.read(conf_arq)

    def parse_list(inString):
        outList=[]

        for item in inString.split(','):
            outList.append(item)

        return outList 

    switches = []

    items = config.items('switches')

    for item in items:
        name = item[0]

        rest = item[1].split()

        switchType = ''
        stopCommand = ''
        sflow = None
        switchIP = ''
        dpid = None
        dpctl = ''
        startCommand = ''
        netflow = None
        externalInterfaces = ''
        controllers = ''

        for opt in rest:
            if re.match("switchtype",opt):
                switchType = opt.split('=')[1]
                if (switchType == 'legacyswitch'):
                    break
            elif re.match("stopcommand",opt):
                stopCommand = opt.split('=')[1]
            elif re.match("sflow",opt):
                sflow = int(opt.split('=')[1])
            elif re.match("switchIP",opt):
                switchIP = opt.split('=')[1]
            elif re.match("dpid",opt):
                dpid = int(opt.split('=')[1])
            elif re.match("dpctl",opt):
                dpctl = opt.split('=')[1]
            elif re.match("startcommand",opt):
                startCommand = opt.split('=')[1]
            elif re.match("netflow",opt):
                netflow = int(opt.split('=')[1])
            elif re.match("externalinterfaces",opt):
                externalInterfaces = parse_list(opt.split('=')[1])
            elif re.match("controllers",opt):
                controllers = parse_list(opt.split('=')[1])

        switches.append(confSwitch(name, switchType, stopCommand, sflow, switchIP, dpid, dpctl, startCommand, netflow, externalInterfaces, controllers))

    return switches

def parse_controllers(conf_arq):
    'Parse controllers section from the conf file.'
    config = ConfigParser.RawConfigParser()
    config.read(conf_arq)

    controllers = []

    items = config.items('controllers')

    for item in items:
        name = item[0]

        rest = item[1].split()

        remotePort = None
        controllerProtocol = ''
        remoteIP = ''
        controllerType = ''

        for opt in rest:
            if re.match("remoteport",opt):
                remotePort = int(opt.split('=')[1])
            elif re.match("controllerprotocol",opt):
                controllerProtocol = opt.split('=')[1]
            elif re.match("remoteip",opt):
                remoteIP = opt.split('=')[1]
            elif re.match("controllertype",opt):
                controllerType = opt.split('=')[1]

        controllers.append(confController(name, remotePort, controllerProtocol, remoteIP, controllerType))

    return controllers

def parse_preferences(conf_arq):
    'Parse preferences section from the conf file.'
    config = ConfigParser.RawConfigParser()
    config.read(conf_arq)

    items = config.items('preferences')

    getMetrics = None
    metricsTimer = None
    ipBase = ''
    terminalType = ''
    startCLI = ''
    dbName = ''
    dbHost = ''
    dbPort = None
    dbUser = ''
    dbPass = ''

    for item in items:

        if re.match("getmetrics", item[0]):
            getMetrics = int(item[1])
        elif re.match("metricstimer",item[0]):
            metricsTimer = float(item[1])
        elif re.match("ipbase",item[0]):
            ipBase = item[1]
        elif re.match("terminaltype",item[0]):
            terminalType = item[1]
        elif re.match("startcli",item[0]):
            startCLI = int(item[1])
        elif re.match("dbname",item[0]):
            dbName = item[1]
        elif re.match("dbhost",item[0]):
            dbHost = item[1]
        elif re.match("dbport",item[0]):
            dbPort = int(item[1])
        elif re.match("dbuser",item[0]):
            dbUser = item[1]
        elif re.match("dbpass",item[0]):
            dbPass = item[1]

    
    preferences={"getMetrics": getMetrics,
                 "metricsTimer": metricsTimer,
                 "ipBase": ipBase,
                 "terminalType": terminalType,
                 "startCLI": startCLI,
                 "dbPrefs": { "dbHost": dbHost,
                              "dbPort": dbPort,
                              "dbName": dbName,
                              "dbUser": dbUser,
                              "dbPass": dbPass
                            },        
                 }

    return preferences
