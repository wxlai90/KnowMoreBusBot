#!/usr/bin/python

import json

class Bus(object):
	def __init__(self):
		self.Arrival = None
		self.Load = None


class Bus_Stop(object):
	def __init__(self):
		self.BusStopCode = None
		self.Services = []
