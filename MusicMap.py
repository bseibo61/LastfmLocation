import pandas as pd
import glob, os, json
import datetime
import bisect
import plotly.express as px
import itertools

# Generate list of songs that's played the number of times specified
def on_repeat(times_played, music_df):
    last_song = ""
    count = 0
    repeat_list = []

    times_played -= 2
    for song in music_df["song"]:
        if count >= times_played and last_song == song and song not in repeat_list:
            print(count, times_played)
            repeat_list.append(song)
            count = 0

        if last_song != song:
            count = 0
        else:
            count += 1

        last_song = song

    print(repeat_list)


location_path = r'Data\GoogleData1-1-2020\Location History\Semantic Location History\2019'
all_files = glob.glob(os.path.join('', "*.json"))

full_location_json = []
year_list = ['2018', '2019', '2020']
for year in year_list:
    for f in glob.glob(os.path.join(r'Data\GoogleData1-1-2020\Location History\Semantic Location History\{0}'.format(year), "*.json")):
        with open(f, encoding="utf8") as i:
            full_location_json.append(json.load(i))

# Get just the activities for visited places
places_json = []
for month in full_location_json:
    for activity in month["timelineObjects"]:
        for n in activity:
            if(n == 'placeVisit'):
                places_json.append(activity)

# Sort months chronologically
places_json = sorted(places_json, key = lambda i: i['placeVisit']['duration']['startTimestampMs'] )


# flatten json location to df
location_name_list = []
for place in places_json:
    temp_dict = {}
    temp_dict.update({'startTimestamp': ( float(place['placeVisit']['duration']['startTimestampMs'])/1000 ) })
    temp_dict.update({'endTimestamp': ( float(place['placeVisit']['duration']['endTimestampMs'])/1000 ) })
    temp_dict.update({'name': place['placeVisit']['location']['name']})
    temp_dict.update({'latitude': place['placeVisit']['location']['latitudeE7']})
    temp_dict.update({'longitude': place['placeVisit']['location']['longitudeE7']})
    location_name_list.append(temp_dict)

location_name_df = pd.DataFrame(location_name_list)
location_name_df.sort_values(['startTimestamp'], inplace=True)
# This changes the df, but doesn't actually completly sort it

music_df = pd.read_csv(r'Data\lastfm.csv', names=['artist', 'album', 'song', 'date'])

# Convert lastfm time string to timestamp like google has
music_df['timestamp'] = music_df['date'].apply(lambda date: datetime.datetime.timestamp(datetime.datetime.strptime(date, '%d %b %Y %H:%M')))

# Call this to get repeated songs
# on_repeat(2, music_df)

# Sorts songs by place listened
songsInPlace = {}
for index, song in music_df.iterrows():
    bi = bisect.bisect(location_name_df['startTimestamp'].tolist(), song['timestamp'])

    if ( (bi > 1) and (song['timestamp'] > location_name_df['startTimestamp'][bi-1]) and (song['timestamp'] < location_name_df['endTimestamp'][bi-1]) ):
        
        if location_name_df['name'][bi - 1] not in songsInPlace:
            songsInPlace[location_name_df['name'][bi - 1]] = [location_name_df['latitude'][bi - 1]]
            songsInPlace[location_name_df['name'][bi - 1]].append(location_name_df['longitude'][bi - 1])
            songsInPlace[location_name_df['name'][bi - 1]].append(song)
        else:
            # append song to existing dict value list
            songsInPlace[location_name_df['name'][bi - 1]].append(song)

# Removes places with only a few songs listened to
temp = {}
for place_key in songsInPlace.keys():
    if len(songsInPlace[place_key]) > 20:
       temp[place_key] = songsInPlace[place_key]
       
songsInPlace = temp


# Makes a csv for the map
map_csv = pd.DataFrame(songsInPlace.keys(), columns=['place'])

map_csv['latitude'] = map_csv.apply( lambda row: songsInPlace[row['place']][0] / 10000000, axis=1)
map_csv['longitude'] = map_csv.apply( lambda row: songsInPlace[row['place']][1] / 10000000, axis=1)

# Ranks songs in each place and puts them in a df to join with map_csv
top_songs_csv = []
for place_key in songsInPlace:
    played_in_place_counter = {}
    for i in range(2, len(songsInPlace[place_key]) - 1):
        if songsInPlace[place_key][i]['song'] in played_in_place_counter.keys():
            played_in_place_counter[songsInPlace[place_key][i]['song']] += 1
        else:
            played_in_place_counter[songsInPlace[place_key][i]['song']] = 1
        ordered_played_in_place_counter = sorted(played_in_place_counter.items(), key=lambda x: x[1], reverse=True)
    
    top_songs_csv.append(ordered_played_in_place_counter[:4])


top_songs_df = pd.DataFrame(top_songs_csv, columns=['1','2','3','4'])

map_csv = map_csv.join(top_songs_df)

print(map_csv['1'][1][1])
map_csv.drop(map_csv[map_csv['1'] > 1].index, inplace = True)

fig = px.scatter_mapbox(map_csv, lat="latitude", lon="longitude", hover_name="place", hover_data=["place", "1", "2", "3"],
                        color_discrete_sequence=["fuchsia"], zoom=3, height=300)
fig.update_layout(mapbox_style="open-street-map")
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
fig.show()



# TODO:
# Delete map csv rows that have number one songs with under two plays, get top songs per country
# Something is wrong with lastfm or google timestamps leading to some songs at wonky places but it can't really be fixed,













