#!/usr/bin/python

import logging
import json
import requests
import datetime
from flask import Flask, request
from BusBot import BusBot
from Bus_Arrival import Bus_Stop, Bus
from math import cos, asin, sqrt

b = BusBot()
app = Flask(__name__)
bus_stops = []
radius = 0.3
API_KEY = 'YOUR API KEY'
logging.basicConfig(filename = './TBot.log', level = logging.DEBUG)
logger = logging.getLogger()


lookup = {'SD' : u'\u2796', 'DD' : u'\u2797', u'BD' : 'Bendy', 'SEA' : u'\u2705', 'SDA' : u'\u26a0\ufe0f', 'LSD' : u'\u274c'}


@app.route('/webhookurl', methods=['GET', 'POST'])
def bottoken():
	data = request.data
	logger.info('Incoming POST: {}'.format(data))
	b.currentUpdate = json.loads(data)
	processUpdate()  #async this and try?
	return 'Reached hook!'


def processUpdate():
	if 'message' in b.currentUpdate and 'location' not in b.currentUpdate['message']:
		update = b.processTextMessage() #ends up as b.Update
		incomingText(update)
		return
	if 'callback_query' in b.currentUpdate:
		update = b.processCallbackQuery()  #ends up as b.Update
		incomingCallbackQuery(update)
		return
	if 'location' in b.currentUpdate['message']:
		update = b.processLocation()  #ends up as b.Update
		incomingLocation(update)
		return


def incomingText(Message):
	busStopCode = isBusCode(Message.Message_text)
	if busStopCode:
		arrivals = getBusArrivals(busStopCode)
		bus_stop = parseArrivals(arrivals)
		resp = constructBusArrivalResponse(bus_stop)
		b.sendInlineKeyboard(chat_id = Message.Chat_ID, text = resp, parse_mode = 'HTML', display_text = ['Refresh'], callback_data = [busStopCode])
	else:
		pass #means its not a bus arrival enquiry

def incomingCallbackQuery(CallbackQuery):
	busStopCode = isBusCode(CallbackQuery.Callback_Data)
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


def constructBusArrivalResponse(bus_stop_obj):
	c = bus_stop_obj
	#resp = u'\ud83d\ude8f<b>' + c.BusStopCode + u'</b>  Seating: \u2705\u26a0\ufe0f\u274c:\n'
	bus_stop = getBusStopByCode(c.BusStopCode)
	resp = u"\ud83d\ude8f<b>{} ({})</b> Seating: \u2705\u26a0\ufe0f\u274c\n".format(bus_stop.Description, c.BusStopCode)
	for buses in c.Services:
		for bus_no in buses:
			resp += u'\ud83d\ude8c<b>' + bus_no + "</b>: "
			for bus in buses[bus_no]:
				if bus.Type and bus.Load:
					if bus.Arrival <= 1:
						resp += u"{}{} ".format('Arr', lookup[bus.Load], lookup[bus.Type])
					else:
						resp += u"{} mins{} ".format(bus.Arrival, lookup[bus.Load], lookup[bus.Type])
			resp += '\n'
	return resp




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



def getBusStopByCode(busstopcode):
	for bus_stop in bus_stops:
		if bus_stop.BusStopCode == str(busstopcode):
			return bus_stop
	return None


def startHooking():
	app.run(debug = True)


if __name__ == '__main__':
	readBusStopsintoMem()
	startHooking()
