import pandas as pd
import glob, os, json
import datetime
import bisect
import itertools
import xml.etree.ElementTree as et

location_path = r'Data\GoogleData1-1-2020\Location History\Semantic Location History\2019'
smsPath = r'smsData'
all_files = glob.glob(os.path.join('', "*.json"))

def findkeys(node, kv):
    if isinstance(node, list):
        for i in node:
            for x in findkeys(i, kv):
               yield x
    elif isinstance(node, dict):
        if kv in node:
            yield node[kv]
        for j in node.values():
            for x in findkeys(j, kv):
                yield x

# print intresting bits of full_json
def printFinalJson(json):
    for i in json:
        match i['name']:
            case 'text':
                print("{0}: {1}".format(i['contactName'], i['body']))
            case 'activitySegment':
                print(i['activityType'])
            case 'placeVisit':
                print(i['placeName'])
            case _:
                raise Exception("Trying to print unrecognized name")


# Read location json
full_location_json = []
year_list = ['2020']
for year in year_list:
    # for f in glob.glob(os.path.join(r'Data\GoogleData1-1-2020\Location History\Semantic Location History\{0}'.format(year), "*.json")):
    for f in glob.glob(os.path.join(location_path, "*.json")):
        with open(f, encoding="utf8") as i:
            full_location_json.append(json.load(i))

# Read lastFM csv
music_df = pd.read_csv(r'Data/lastfm.csv', names=['artist', 'album', 'song', 'date'])

# Read SMS xml
sms_xml = open('Data/SmsDataTest.xml', 'r', encoding="utf8").read()
root = et.XML(sms_xml)
sms_json = []
for child in root:
    if child.tag == 'sms':
        sms_json.append({
            'name':'text', 'body': child.attrib['body'], 'startTime': child.attrib['date'], 'type': child.attrib['type'], 'contactName': child.attrib['contact_name']
        })


# Convert lastfm time string to timestamp like google has
music_df['timestamp'] = music_df['date'].apply(lambda date: datetime.datetime.timestamp(datetime.datetime.strptime(date, '%d %b %Y %H:%M')))


temp_location_json = []
for month in full_location_json:
    for activity in month['timelineObjects']:
        segmentName = next(iter(activity))
        startTime = list(findkeys(activity, 'startTimestampMs'))[0]

        activityType = ''
        placeAddress = ''
        placeName = ''

        # get activity type
        if(segmentName == 'activitySegment'):
            activityType = activity['activitySegment']['activityType']
        if(segmentName == 'placeVisit'):
            placeName = activity['placeVisit']['location']['name']
            # need .get beacuse some places don't have addresses
            placeAddress = activity['placeVisit']['location'].get('address')
        
        temp_location_json.append(
            {
                'name': segmentName, 'activityType': activityType, 'startTime': startTime, 'placeName': placeName, 'placeAddress': placeAddress
            })

full_location_json = temp_location_json

full_json = full_location_json + sms_json
# Sort months chronologically
full_json = sorted(full_json, key = lambda i: i['startTime'] )

# TODO add in markers for each new day, get lastfm songs in full_json, look into making a webpage to display everything
# more text analytics? like most used words with people, texting frequency with people ect

printFinalJson(full_json)
    