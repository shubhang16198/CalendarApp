from __future__ import print_function
from flask import Flask, request, url_for
from flask_pymongo import PyMongo
import flask
import httplib2
import os
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
import datetime
from collections import defaultdict
import time
import re

app = Flask(__name__,static_url_path='')

app.config['MONGO_DBNAME'] = 'test'
app.config['MONGO_URI'] = 'mongodb://localhost:27017/testdb'
app.config['SECRET_KEY'] = '0do3ITmMzXP0afu1Agg4XnGI'   #For Locally
#app.config['SECRET_KEY'] = 'R3yjfbBflLnIwn16RmovFCq0'  #For Deployment
mongo = PyMongo(app)

service = None

@app.route('/')
def home():
    return app.send_static_file('html/calendar.html')


def get_start_date(startDate):
    """
    Given a string startDate in the format of YYYY-mm-dd
    return a datetime object with the proper time zone
    """
    return (datetime.datetime
                    .strptime(startDate, "%Y-%m-%d")
                    .isoformat() + 'Z')

def get_now_date():
    """Return a datetime object of current time"""
    return (datetime.datetime.utcnow()
                    .isoformat() + 'Z')

def get_calendar_list_map(service):
    """Get the list of Calendar Names, and store their corresponding ids"""

    calendarMap = defaultdict()
    page_token = None

    calendars = (service.calendarList()
                        .list(pageToken = page_token).execute())

    for calendar in calendars['items']:
        id = calendar.get('id', None)
        summary = calendar.get('summary', None)
        calendarMap[summary] = id
    return calendarMap

def get_ts_from_datetime(start, end):
    """convert datetime string into a time event
       so we can perform time arithmetic on them"""

    if start[-2:] == '00':
        startHr = datetime.datetime.strptime(start[:-6], "%Y-%m-%dT%H:%M:%S")
    elif start[-1] == 'Z':
        startHr = datetime.datetime.strptime(start, "%Y-%m-%dT%H:%M:%SZ")
    else:
        startHr = datetime.datetime.strptime(start, "%Y-%m-%d")

    if end[-2:] == '00':
        endHr = datetime.datetime.strptime(end[:-6], "%Y-%m-%dT%H:%M:%S")
    elif end[-1] == 'Z':
        endHr = datetime.datetime.strptime(end, "%Y-%m-%dT%H:%M:%SZ")
    else:
        endHr = datetime.datetime.strptime(end, "%Y-%m-%d")

    startTS = time.mktime(startHr.timetuple())
    endTS = time.mktime(endHr.timetuple())
    return (startTS, endTS)


def get_events_in_calendar(calendarName, calendarMap, service, startDate, endDate=None):
    """Get all the events in a calendar for a specific time period"""

    print ('\nGet ' + calendarName + ' Events Since the beginning of the year.............')
    startDate = get_start_date(startDate)
    endDate = get_now_date()
    calendarId = calendarMap.get(calendarName)
    eventsResult = (service.events().list(calendarId = calendarId, timeMin = startDate, timeMax = endDate, maxResults = 1000, singleEvents = True, orderBy = 'startTime').execute())

    events = eventsResult.get('items', [])
    events_list = []

    if not events:
        print ('No events found.')
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))
        event_type = calendarName
        eventTitle = event.get('summary')
        #event_name = ''.join([i if ord(i) < 128 else '' for i in eventTitle.replace(',','')])
	event_id = event['id']
	#print()
        #print start[:10], duration, event_type, event_name
    	mongo.db.Events.insert_one(
        {
	"cal_id": calendarId,
        "_id": event_id,
        "name":eventTitle,
	"description":event.get('description'),
        "start":start,
        "end":end
        })
	#print("############## INSERTED ################")
        events_list.append([event_id,start,end,event_type, eventTitle])
    return events_list



@app.route('/login')
def login():
  if 'credentials' not in flask.session:
    return flask.redirect(flask.url_for('oauth2callback'))
  credentials = client.OAuth2Credentials.from_json(flask.session['credentials'])
  if credentials.access_token_expired:
    return flask.redirect(flask.url_for('oauth2callback'))
  else:
    mongo.db.Events.drop()
    http_auth = credentials.authorize(httplib2.Http())
    global service
    service = discovery.build('calendar', 'v3', http = http_auth)
    global calendarMap
    calendarMap = get_calendar_list_map(service)
    for calendarName in calendarMap:
        print ("processing..." + calendarName + "..........")
        events_list = get_events_in_calendar(calendarName, calendarMap, service, '2015-01-01')
        #print (events_list)
    #s = '\n'.join([calendar for calendar in calendarMap])
    return flask.redirect(flask.url_for('home'))

@app.route('/oauth2callback')
def oauth2callback():
  flow = client.flow_from_clientsecrets(
      'client_secrets.json', #For running Locally
      #'deployment.json', #For deployment over server
      scope='https://www.googleapis.com/auth/calendar',
      redirect_uri=flask.url_for('oauth2callback', _external=True))

  if 'code' not in flask.request.args:
    auth_uri = flow.step1_get_authorize_url()
    return flask.redirect(auth_uri)
  else:
    auth_code = flask.request.args.get('code')
    credentials = flow.step2_exchange(auth_code)
    flask.session['credentials'] = credentials.to_json()
    #print(credentials.to_json())
    return flask.redirect(flask.url_for('login'))

@app.route('/delete/<event_id>')
def delete(event_id):
	Events = mongo.db.Events.find({"_id":event_id})
	for event in Events:
		e=event
	#print (e['cal_id'])
	service.events().delete(calendarId=e['cal_id'], eventId=event_id).execute()
	mongo.db.Events.remove({"_id":event_id})
	return "Event Deleted"

@app.route('/update',methods=['POST'])
def update(event_id):
   new_Event = {
   '_id' : request.form['_id'],
   'description': request.form['description'],
   'name' : request.form['name'],
   'start': request.form['start'],
   'end' : request.form['end']
   }
   Event = mongo.db.Events.find({"_id":new_Event['_id']})
   e = None
   for t in Event:
    e = t

    if e!=None:
        for key in new_Event.keys():
            e[key] = new_Event[key]
        mongo.db.Events.save(e)
        e['start'] = {'dateTime': e['start']}
        e['end'] = {'dateTime':e['end']}
        e['summary'] = e['name']
        updated_event=service.events().update(calendarId='primary', eventId=e['_id'], body=e).execute()
        return "Event Updated"
    else:
      return "Invalid Event ID"

@app.route('/all')
def list_all():
	Events = mongo.db.Events.find()
	E =[]
	for e in Events:
		E.append(e)
	return str(E)
@app.route('/all/<year>/<month>/<day>')
def list_day_events(year,month,day):
    date = datetime.date(int(year), int(month), int(day))
    print("###############"+str(date)+"#############")
    #{"start":{$regex:/^2015-01-31*/}}
    DayEvent = mongo.db.Events.find({"start":re.compile("^"+str(date)+"*")})
    result = []
    for e in DayEvent:
        print(e)
        result.append(e)
    return str(result)

@app.route('/create',methods=['POST'])
def create():
	event = {
  		'summary': request.form['name'],
  		'description': request.form['description'],
  		'start': {
    			'dateTime': request.form['start'] #'2017-03-28T12:29:59+05:30'
  			 },
  		'end': {
    			'dateTime': request.form['end']   #'2017-03-29T12:29:59+05:30',
  			},
		}

	event = service.events().insert(calendarId='primary', body=event).execute()
	print(event)
	mongo.db.Events.insert_one(
        {
	"cal_id": 'primary',
        "_id":    event['id'],
        "name":   event['summary'],
	"description":event['description'],
        "start":  event['start'].get('dateTime', event['start'].get('date')),
        "end":    event['end'].get('dateTime', event['end'].get('date'))
        })

	return 'Event created: %s' % (event.get('htmlLink'))

@app.route('/find/<event_id>')
def find(event_id):
    Event = mongo.db.Events.find({"_id":event_id})
    E = []
    for e in Event:
        E.append(e)
    return str(E)


if __name__ == "__main__":
    app.run()
