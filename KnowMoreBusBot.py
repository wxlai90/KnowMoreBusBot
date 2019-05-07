#!/usr/bin/python

import logging
import json
import requests
import datetime
import threading
import sys
from flask import Flask, request
from BusBot import BusBot
from Bus_Arrival import Bus_Stop, Bus
from math import cos, asin, sqrt
from cachetools import TTLCache



b = BusBot()
cache = TTLCache(maxsize=100, ttl=15)
app = Flask(__name__)
bus_stops = []
nus_bus_stops = []
radius = 0.3
API_KEY = 'YOUR LTA DATAMALL API KEY'
logging.basicConfig(filename = './Bus.log', level = logging.DEBUG)
logger = logging.getLogger()


lookup = {'SD' : u'\u2796', 'DD' : u'\u2797', u'BD' : 'Bendy', 'SEA' : u'\u2705', 'SDA' : u'\u26a0\ufe0f', 'LSD' : u'\u274c'}


@app.route('YOUR BOT TOKEN OR UUID', methods=['POST'])
def bottoken():
	data = request.data
	logger.info('Incoming POST: {}'.format(data))
	currentUpdate = json.loads(data)
	t = threading.Thread(target = processUpdate, args = (currentUpdate,))
	t.start()
	#processUpdate(currentUpdate)  #async this and try?
	return ""


def processUpdate(currentUpdate):
	if 'message' in currentUpdate and 'location' not in currentUpdate['message']:
		update = b.processTextMessage(currentUpdate)
		incomingText(update)
		return
	if 'callback_query' in currentUpdate:
		update = b.processCallbackQuery(currentUpdate)
		incomingCallbackQuery(update)
		return
	if 'location' in currentUpdate['message']:
		update = b.processLocation(currentUpdate)
		incomingLocation(update)
		return
	#except Exception as e:
	#	pass #other types of messages received, not supported

def incomingText(Message):
	busStopCode = isBusCode(Message.Message_text)
	if busStopCode:
		arrivals = getBusArrivals(busStopCode)
		bus_stop = parseArrivals(arrivals)
		resp = constructBusArrivalResponse(bus_stop)
		b.sendInlineKeyboard(chat_id = Message.Chat_ID, text = resp, parse_mode = 'HTML', display_text = ['Refresh'], callback_data = [busStopCode])
	elif Message.Message_text == '/start':
		welcome_text = u'''Welcome to <b>K(no)wMoreBusBot</b>

Start by sending either the bus stop code, e.g:

<b>19051</b>

OR

send your location to find bus stops around you by selecting <b>paperclip icon</b> and then <b>location</b>!
<i>Pro-tip: place location pin directly on top of bus stop to query bus stop without knowing bus stop code or bus stop name!</i>

Seats availability is indicated as follows:
\u2705 means there are quite a number of seats available

\u26a0 means there are limited seats and you will probably have to stand :(

\ufe0f\u274c means there is absolutely no room, you might even not be able to board! >:(
'''
		b.sendHTMLMessage(chat_id = Message.Chat_ID, text = welcome_text)
	elif Message.Message_text == '/about':
		text = 'K(no)wMoreBusBot is completely open-source, <a href="https://github.com/wxlai90/KnowMoreBusBot">view its code on Github!</a>\n'
		b.sendHTMLMessage(chat_id = Message.Chat_ID, text = text)
	else:
		pass #means its not a bus arrival enquiry

def incomingCallbackQuery(CallbackQuery):
	busStopCode = isBusCode(CallbackQuery.Callback_Data)
	nusBusStop = isNusBus(CallbackQuery.Callback_Data)
	sendNewKB = False
	if 'Bus Stops Around You (300m radius):' in CallbackQuery.Message_text:
		sendNewKB = True
	if busStopCode:
		arrivals = getBusArrivals(busStopCode)
		bus_stop = parseArrivals(arrivals)
		resp = constructBusArrivalResponse(bus_stop)
		if sendNewKB:
			b.sendInlineKeyboard(chat_id = CallbackQuery.Chat_ID, text = resp, parse_mode = 'HTML', display_text = ['Refresh'], callback_data = [busStopCode])
		else:
			b.editInlineKeyBoard(chat_id = CallbackQuery.Chat_ID, text = resp, parse_mode = 'HTML', message_id = CallbackQuery.Message_ID, display_text = ['Refresh'], callback_data = [busStopCode])
	if nusBusStop:
		name = CallbackQuery.Callback_Data.split('|')[1]
		arrivals = getNusArrivals(name)
		resp = constructNusArrivals(arrivals)
		b.sendTextMessage(chat_id = CallbackQuery.Chat_ID, text = resp)


def incomingLocation(Location):
	lat = Location.Lat
	long = Location.Long
	chat_id = Location.Chat_ID
	text = "Bus Stops Around You (300m radius):"
	bus_stops = within_distance(radius = radius, lat = lat, long = long)
	bus_desc = []
	bus_code = []
	sorted_bus_stops = sorted(bus_stops, key = lambda x: x.Distance, reverse = False)
	for i in range(0, len(sorted_bus_stops)):
		if i == 0:
			bus_desc.append(sorted_bus_stops[i].Description + " (Nearest)")
			bus_code.append(sorted_bus_stops[i].BusStopCode)
		elif i == len(sorted_bus_stops) - 1:
			bus_desc.append(sorted_bus_stops[i].Description + " (Furthest)")
			bus_code.append(sorted_bus_stops[i].BusStopCode)
		else:
			bus_desc.append(sorted_bus_stops[i].Description)
			bus_code.append(sorted_bus_stops[i].BusStopCode)
	b.sendInlineKeyboard(chat_id = chat_id, text = text, display_text = bus_desc, callback_data = bus_code)


def isBusCode(s):
	a = ''.join([i for i in s if i.isdigit()])
	if len(a) == 5:
		return a
	return False


def isNusBus(s):
	return s.split('|')[0] == 'nus'


def constructBusArrivalResponse(bus_stop_obj):
	c = bus_stop_obj
	if c.BusStopCode in cache:
		return cache[c.BusStopCode]
	#resp = u'\ud83d\ude8f<b>' + c.BusStopCode + u'</b>  Seating: \u2705\u26a0\ufe0f\u274c:\n'
	bus_stop = getBusStopByCode(c.BusStopCode)
	resp = u"\ud83d\ude8f<b>{} ({})</b>\n".format(bus_stop.Description, c.BusStopCode)
	for buses in c.Services:
		for bus_no in buses:
			resp += u'\ud83d\ude8c<b>' + bus_no + "</b>: "
#			resp += u'<b>' + bus_no + "</b>: "
			for bus in buses[bus_no]:
				if bus.Type and bus.Load:
					if bus.Arrival <= 1:
						resp += u"{}{}, ".format('Arr', lookup[bus.Load], lookup[bus.Type])
					else:
						resp += u"{}min{}, ".format(bus.Arrival, lookup[bus.Load], lookup[bus.Type])
			resp = resp.rstrip(', ')
			resp += '\n'
	cache[c.BusStopCode] = resp
	return resp


def constructNusArrivals(bus_stops):
	content = ""
	for bus in bus_stops:
		content += "{}: {}\n".format(bus.name, bus.arrival)
	return content


def getBusArrivals(bus_stop_code):
	headers = {
					'AccountKey' : '{}'.format(API_KEY),
					'accept' : 'application/json'
			}


	baseurl = 'http://datamall2.mytransport.sg/'
	url_path = 'ltaodataservice/BusArrivalv2'

	params = {
					'BusStopCode' : '{}'.format(bus_stop_code)
	}

	r = requests.get(baseurl + url_path, headers = headers, params = params)
	if r.status_code != 200:
		pass # in future add in possibile notification msg that LTA's API is wonky

	return r.content


def parseArrivals(bus_arrival_json):
	b = json.loads(bus_arrival_json)
	busstop = Bus_Stop()
	busstop.BusStopCode = b['BusStopCode']
	for i in b['Services']:
		s = {}
		service_no = i['ServiceNo']
		if 'NextBus' in i:
			bus1 = Bus()
			bus1.Arrival = simpletimedelta(i['NextBus']['EstimatedArrival'])
			bus1.Type = i['NextBus']['Type']
			bus1.Load = i['NextBus']['Load']
		if 'NextBus2' in i:
			bus2 = Bus()
			bus2.Arrival = simpletimedelta(i['NextBus2']['EstimatedArrival'])
			bus2.Type = i['NextBus2']['Type']
			bus2.Load = i['NextBus2']['Load']
		if 'NextBus3' in i:
			bus3 = Bus()
			bus3.Arrival = simpletimedelta(i['NextBus3']['EstimatedArrival'])
			bus3.Type = i['NextBus3']['Type']
			bus3.Load = i['NextBus3']['Load']
		s[service_no] = [bus1, bus2, bus3]
		busstop.Services.append(s)
	return busstop



def callNusAPI(stopname):
	'''returns dictionary'''
	url = 'http://nextbus.comfortdelgro.com.sg/testMethod.asmx/GetShuttleService?busstopname='
	r = requests.get(url + stopname)
	a = r.content
	j = a.split('>')[2].split('<')[0]
	d = json.loads(j)
	return d['ShuttleServiceResult']


def getNusArrivals(stopname):
	a = callNusAPI(stopname)
	buses = []
	for i in a['shuttles']:
		bus = Bus()
		name = i['name']
		atime = i['nextArrivalTime']
		bus.name = name
		bus.arrival = atime
		buses.append(bus)
	return buses

def simpletimedelta(time2):
	'''returns time difference as tuple in (HH, MM, SS) format, t2 must be later than t1'''
	if not time2:
		return
	time_2 = time2.split('T')[1].split('+')[0]
	time_1 = str(datetime.datetime.now()).split()[1].split('.')[0]
	h1, m1, s1 = time_1.split(':')[0], time_1.split(':')[1], time_1.split(':')[2]
	h2, m2, s2 = time_2.split(':')[0], time_2.split(':')[1], time_2.split(':')[2]
	t1 = int(h1) * 60 * 60 + int(m1) * 60 + int(s1)
	t2 = int(h2) * 60 * 60 + int(m2) * 60 + int(s2)
	diff = t2 - t1
	if diff < -82800:
			diff += 86400
	elif diff < 0 > -82800:
			return 0
	ss = diff % 60
	mm = (diff / 60) % 60
	hh = diff / 60 / 60
	return mm

def distance(lat1, lon1, lat2, lon2):
    p = 0.017453292519943295     #Pi/180
    a = 0.5 - cos((lat2 - lat1) * p)/2 + cos(lat1 * p) * cos(lat2 * p) * (1 - cos((lon2 - lon1) * p)) / 2
    return 12742 * asin(sqrt(a)) #2*R*asin... # returns in KM


def within_distance(**kargs): #d is in km, will return all bus stops within a given range
	d = kargs['radius']
	la = kargs['lat']
	lo = kargs['long']
	b = []
	for bus_stop in bus_stops:
		distance_between = distance(float(la), float(lo), bus_stop.Latitude, bus_stop.Longitude)
		if distance_between < d:
			#print "{}: {}".format(bus_stop.Description, bus_stop.BusStopCode)
			bus_stop.Distance = distance_between
			b.append(bus_stop)
	return b


def readBusStopsintoMem():
	with open('bus_stops', 'r') as f:
		c = f.readlines()

	global bus_stops

	for i in c:
		b = Bus_Stop()
		bus_stop = eval(i)
		BusStopCode = bus_stop["BusStopCode"]
		RoadName = bus_stop["RoadName"]
		Description = bus_stop["Description"]
		Latitude = bus_stop["Latitude"]
		Longitude = bus_stop["Longitude"]
		b.BusStopCode = BusStopCode
		b.RoadName = RoadName
		b.Description = Description
		b.Latitude = Latitude
		b.Longitude = Longitude
		bus_stops.append(b)



def readNusStopsIntoMem():
	with open('nus_buses', 'r') as f:
		d = eval(f.read())

	global bus_stops

	for i in d:
		bus = Bus()
		bus.Description = i['caption']
		bus.BusStopCode = i['name']
		bus.Latitude = i['latitude']
		bus.Longitude = i['longitude']
		bus_stops.append(bus)


def getBusStopByCode(busstopcode):
	for bus_stop in bus_stops:
		if bus_stop.BusStopCode == str(busstopcode):
			return bus_stop
	return None


def startHooking():
	app.run(host = '0.0.0.0', port = 8443, debug = True, ssl_context = ('ssl.crt', 'ssl.key'))


if __name__ == '__main__':
	readBusStopsintoMem()
	readNusStopsIntoMem()
	startHooking()
