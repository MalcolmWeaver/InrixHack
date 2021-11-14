import requests
import json
import math

app_id = "04czqoql6k"
hash_token = "MDRjenFvcWw2a3xKQU9XalBlRmxmM1ZvNUJVN3dHNEU0c2EyRmphTmkxejJvQWZkTG45"
auth = requests.get('https://api.iq.inrix.com/auth/v1/appToken?appId=' + app_id + '&hashToken=' + hash_token)
json_data = auth.json()
api_key = json_data['result']['token']

header = {'Authorization' : 'Bearer ' + api_key}


def getParkAndTime(start, end, startTime):
    coords, off_prob, on_prob = closestParking(end, startTime)
    coords.reverse()
    coords[:] = [str(x) for x in coords]
    driveRouteArg = '%2C'.join(coords)
    # print(driveRouteArg)
    # print('Parktime: ',parkTime(off_prob))
    return coords, driveRoute(start, driveRouteArg) + parkTime(off_prob), probToInt(on_prob)


def probToInt(prob):
    if(prob < 25):
        return 1
    elif(prob < 50):
        return 2
    elif(prob < 75):
        return 3
    return 4


def closestParking(end, event_time):
    radius = '1609'
    off_data = requests.get('https://api.iq.inrix.com/lots/v3?point=' + end + '&radius=' + radius + '&entry_time=' + event_time + '&duration=1', headers = header)
    off_lots = off_data.json()
    off_ind = 0
    off_min = off_lots['result'][0]['distance']
    for index, plot in enumerate(off_lots['result']):
        if plot['distance'] < off_min:
            off_min = plot['distance']
            off_ind = index

    #Closest off-street parking
    off_prob = off_lots['result'][off_ind]['occupancy']['probability']
    # print(off_lots['result'][off_ind]['occupancy']['probability'])
    # print(off_lots['result'][off_ind]['point']['coordinates'])
    # print('Off_prob:', off_prob)
    on_data = requests.get('https://api.iq.inrix.com/blocks/v3?point=' + end + '&radius=' + str(off_min) + '&entry_time=' + event_time + '&duration=1', headers = header)
    on_lots = on_data.json()
    # print(on_lots)
    unscaled_prob = 0
    total_spots = 0
    for street in on_lots['result']:
        if street['probability'] != None:
            street_spots = 0
            for plot in street['segments']:
                street_spots += plot['spacesTotal']
                total_spots += plot['spacesTotal']
            unscaled_prob += (street['probability'] * street_spots)

    #Probability of a spot being open within radius of nearest parking.
    open_prob = unscaled_prob / total_spots
    # print('Open_prob: ',open_prob)
    return off_lots['result'][off_ind]['point']['coordinates'], off_prob, open_prob
    # 0-25 is bad, 25-50 is weak, 50-75 is decent, 75-100 look for street side!


def driveRoute(start,parking):
    route_data = requests.get('https://api.iq.inrix.com/findRoute?wp_1=' + start + '&wp_2=' + parking + '&format=json', headers = header)
    routing = route_data.json()
    routes = dict()
    for item in routing['result']['trip']['routes']:
        routes[item['id']] = item['travelTimeMinutes']
    fastest_routes = sorted(routes.items(), key = lambda x: x[1])
    # print('Fastest Routes: ', fastest_routes)
    return fastest_routes[0][1]

def parkTime(prob):
    prob = prob / 100
    if prob <= .1:
        return 20
    elif prob >= .9:
        return 5
    return math.ceil((-15/.9) * prob + 20)