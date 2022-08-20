from datetime import datetime
import urllib.parse
import requests
from haversine import haversine
from battery import LithiumIonBattery
from motor import NeedEnergy
import math
import time as tm


class Environment:
    def __init__(self, origin_adr, destination_adr):
        self.origin = origin_adr
        self.destination = destination_adr
        self.make_map()
        self.battery = LithiumIonBattery(50000)  # Wh
        self.need_energy = NeedEnergy()
        self.charge_num = 0
        self.unreach_position_num = 0
        self.time = 0
        self.ii = 0
        self.status_dir_check = 0
        self.length = 1
        # self.s = requests.Session()
        self.envheightkm = 1
        self.latt = 0
        self.lngg = 0

    def geocoding_api(self, address):  # 2 output: status, position
        # address: key word of place
        # geocode_api = 'https://maps.googleapis.com/maps/api/geocode/json?'
        geocode_api = 'https://geocode.xyz/'
        # geocode_url = geocode_api + urllib.parse.urlencode({'address': address}) + "$key=AZuesYuds12_dsakd23456sdeHf"
        geocode_url = geocode_api + address + '?json=1&auth=186045329051577789542x77926'
        # geocode_json = requests.get(geocode_url, timeout=10).json()
        s = requests.Session()
        res = s.get(geocode_url)
        geocode_json = res.json()
        self.geocode_json_status = res.reason
        self.geoposition_tuple = ('g', 'g')
        if self.geocode_json_status == 'OK':
            # latt = 0
            # lngg = 0
            # geocode_data_results = geocode_json['results'][0]
            # geocode_data_results_geometry = geocode_data_results['geometry']
            # latt = geocode_data_results_geometry['location']['lat']
            # lngg = geocode_data_results_geometry['location']['lng']
            latt = float(geocode_json['latt'])
            lngg = float(geocode_json['longt'])
            self.latt = latt
            self.lngg = lngg
            # geocode_data_results_formattedaddress = geocode_data_results['formatted_address']
            # geocode_data_results_types = geocode_data_results['types']
            # geocode_data_results_placeid = geocode_data_results['place_id']
            self.geoposition = str(latt) + ',' + str(lngg)
            self.geoposition_tuple = (latt, lngg)
        else:
            # geocode_data_results_geometry = 'N / A'
            # geocode_data_results_formattedaddress = 'N / A'
            # geocode_data_results_types = 'N / A'
            # geocode_data_results_placeid = 'N / A'
            self.geoposition = 'N / A'
        return self.geocode_json_status, self.geoposition, self.geoposition_tuple

    def elevation_api(self, location):  # 2 output: elevation, resolution
        # location = '51.4700223,-0.4542955'
        # elevation_api = 'https://maps.googleapis.com/maps/api/elevation/json?'
        elevation_api = 'https://api.open-elevation.com/api/v1/lookup?'
        elevation_url = elevation_api + urllib.parse.urlencode({'locations': location})  # + "$key=AZuesYuds12_dsakd23456sdeHf"
        # elevation_json = requests.get(elevation_url, timeout=10).json()
        s = requests.Session()
        res = s.get(elevation_url)
        elevation_json = res.json()
        self.elevation_json_status = res.reason
        if self.elevation_json_status == 'OK':
            elevation_data_results = elevation_json['results'][0]
            self.elevation_data_results_elevation = elevation_data_results['elevation']
            # elevation_data_results_resolution = elevation_data_results['resolution']
        else:
            self.elevation_data_results_elevation = 'N/A'
            # elevation_data_results_resolution = 'N/A'
        return self.elevation_json_status, self.elevation_data_results_elevation

    def directions_api(self, origin, destination):  # 5 output: status, steps, bound
        # directions_api = 'https://maps.googleapis.com/maps/api/directions/json?'
        # directions_api = 'https://api.openrouteservice.org/v2/directions/driving-car?'
        directions_api = 'http://localhost:8989/route?'
        directions_url = directions_api + urllib.parse.urlencode({'point': ','.join(origin.split(','))}) + '&' + urllib.parse.urlencode(
            {'point': ','.join(destination.split(','))}) + '&' + 'profile=car&points_encoded=false'

        # directions_url = directions_api + urllib.parse.urlencode({'start': ','.join(origin.split(',')[::-1])}) + '&' + urllib.parse.urlencode(
        #     {'end': ','.join(destination.split(',')[::-1])}) + '&' + urllib.parse.urlencode(
        #     {'units': 'metric'}) + '&' + 'api_key=5b3ce3597851110001cf6248dcc3e4a51ec04c3c9da1eb5b43d4ef3e'  # + "$key=AZuesYuds12_dsakd23456sdeHf"
        # directions_json = requests.get(directions_url, timeout=10).json()
        s = requests.Session()
        res = s.get(directions_url)
        directions_json = res.json()
        self.directions_json_status = res.reason
        if self.directions_json_status == 'OK':
            # directions_data_routes = directions_json['routes'][0]
            # directions_data_routes_bounds = directions_data_routes['bounds']  # all are 'southwest', 'northeast'
            # directions_data_routes_legs = directions_data_routes['legs']
            self.directions_data_routes_legs_steps = directions_json['paths'][0]
            # directions_data_routes_summary = directions_data_routes['summary']
            #### process boundary ###
            self.north = self.directions_data_routes_legs_steps['bbox'][3]
            self.east = self.directions_data_routes_legs_steps['bbox'][2]
            self.south = self.directions_data_routes_legs_steps['bbox'][1]
            self.west = self.directions_data_routes_legs_steps['bbox'][0]
            self.bound = {'north': self.north, 'east': self.east, 'south': self.south, 'west': self.west}  # value of lat/lng
        else:
            # directions_data_routes_bounds = 'N/A'
            # directions_data_routes_legs = 'N/A'
            self.directions_data_routes_legs_steps = 'N/A'
            # directions_data_routes_summary = 'N/A'
            self.bound = 'N/A'
            # map_range = 'N/A'
        return self.directions_json_status, self.directions_data_routes_legs_steps, self.bound

    def make_map(self):
        origin_status, origin_position, origin_position_num = self.geocoding_api(self.origin)
        if origin_position_num == ('g', 'g'):
            origin_position_num = (self.latt, self.lngg)
        destination_status, destination_position, destination_position_num = self.geocoding_api(self.destination)
        if destination_position_num == ('g', 'g'):
            destination_position_num = (self.latt, self.lngg)
        direction_status, direction_step, self.map_bound = self.directions_api(origin_position, destination_position)
        self.Google_step = direction_step
        # self.stride_wide = (self.east - self.west) / self.map_range['width']   # positive
        # self.stride_height = (self.north - self.south) / self.map_bound['height']  # positive
        while direction_status != 'OK':
            direction_status, direction_step, self.map_bound = self.directions_api(origin_position, destination_position)
        self.current_position = origin_position_num  # position tuple (lat,lng)
        self.start_position = origin_position_num  # position tuple (lat,lng)
        self.end_position = destination_position_num  # position tuple (lat,lng)

    def stride_length(self, position):
        start_lat = self.start_position[0]
        start_lng = self.start_position[1]
        end_lat = self.end_position[0]
        end_lng = self.end_position[1]
        east = start_lng if start_lng > end_lng else end_lng
        west = start_lng if start_lng < end_lng else end_lng
        north = start_lat if start_lat > end_lat else end_lat
        south = start_lat if start_lat < end_lat else end_lat
        a = (north, west)
        b = (south, west)
        self.stridebounda = a
        self.strideboundb = b
        lat = position[0]
        # lng = position[1]
        right = (lat, east)
        left = (lat, west)
        height = haversine(a, b)  # km
        self.envheightkm = height
        wide = haversine(right, left)  # km
        self.stride_height = (north - south) / (height * self.length)  # positive   # 500m per stride
        self.stride_wide = (east - west) / (wide * self.length)
        # self.stride_height = (north - south) / (height * 2)  # positive   # 500m per stride
        # self.stride_wide = (east - west) / (wide * 2)

    def step(self, action):  # output:
        # action is in the set of (0,1,2,3) = (north, east, south, west)
        # self.current_position is tuple (lat, lng)
        self.step_reward = 0
        current_status = False
        step_reward = 0
        step_history = []
        # energy_consume = 0
        self.stride_length(self.current_position)
        stride_direction = -1 if action > 1 else 1
        if action == 0:  # north
            self.next_position = (self.current_position[0] + stride_direction * self.stride_height, self.current_position[1])
        if action == 1:  # east
            self.next_position = (self.current_position[0], self.current_position[1] + stride_direction * self.stride_wide)
        if action == 2:  # south
            self.next_position = (self.current_position[0] + stride_direction * self.stride_height, self.current_position[1])
        if action == 3:  # west
            self.next_position = (self.current_position[0], self.current_position[1] + stride_direction * self.stride_wide)

        current = str(self.current_position[0]) + ',' + str(self.current_position[1])
        next_position = str(self.next_position[0]) + ',' + str(self.next_position[1])
        #### check next_
        self.status_dir_check = 0
        status, leg_step, bound = self.directions_api(current, next_position)
        self.status_dir_check = status
        if status != 'OK' or self.next_position[0] > self.map_bound['north'] or self.next_position[0] < self.map_bound['south'] or self.next_position[1] > self.map_bound['east'] or \
                self.next_position[1] < self.map_bound['west']:
            # The step is not reachable
            if status != 'Too Many Requests' and status != 'Not Found':
                self.step_reward = -1
                self.unreach_position_num = self.unreach_position_num + 1
            self.next_position = self.current_position  # The step is not available or out of map bound then go back to previous step
            # self.unreach_position_num = self.unreach_position_num + 1
        else:
            self.step_reward -= 0.1  # get -0.1 reward for every transition
            coordinates = leg_step['points']['coordinates']
            leg_step = leg_step['instructions']
            for i in range(len(leg_step)):
                print("For " + str(i) + " in Step", end = '\r')
                waypoint = leg_step[i]['interval']
                start = (coordinates[waypoint[0]][1], coordinates[waypoint[0]][0])
                end = (coordinates[waypoint[1]][1], coordinates[waypoint[1]][0])
                duration = int(leg_step[i]['time'])  # second
                distance = leg_step[i]['distance']  # km
                start_position = str(start[0]) + ',' + str(start[1])
                end_position = str(end[0]) + ',' + str(end[1])
                status, height_start = self.elevation_api(start_position)
                status1, height_end = self.elevation_api(end_position)
                while status != 'OK' or status1 != 'OK':
                    status, height_start = self.elevation_api(start_position)
                    status1, height_end = self.elevation_api(end_position)
                elevation = height_end - height_start  # unit: m
                if duration <= 0:
                    duration = 1
                self.time = self.time + duration
                speed = math.sqrt(distance ** 2 + elevation ** 2) / duration  # m/s
                angle = math.atan2(distance * 1000, elevation)  # degree
                angle = angle if angle > 0 else 0
                power = self.need_energy.energy(angle=angle, V=speed)
                energy_consume = 0
                for t in range(duration):
                    charge = self.battery.use(duration=1, power=power)
                    energy_consume += self.battery.energy_consume
                    self.step_reward -= self.battery.energy_consume / 100000
                    if charge:  # this duration need to charge the battery
                        self.charge_num += 1
                        self.battery.charge(50000)  # make it full capacity
                        # self.step_reward -= 0.1   # we deduct 0.1 point of reward when charge

                # step_reward -= duration/60 * 1.05 ** elevation
                step_history.append([start, end, duration, distance, angle, speed, energy_consume])
            if abs(self.next_position[0] - self.end_position[0]) < self.stride_height and abs(self.next_position[1] - self.end_position[1]) < self.stride_wide:
                self.step_reward = 1  # really close to end position within one step
                self.step_reward -= 0.1
                ### calculate the reward between current position to the end
                # nextt = str(self.next_position[0]) + ',' + str(self.next_position[1])   # fix
                end_position = str(self.end_position[0]) + ',' + str(self.end_position[1])
                statusE, leg_stepE, boundE = self.directions_api(next_position, end_position)  # fix
                self.legE = leg_stepE
                
                coordinates = self.legE['points']['coordinates']
                self.legE = self.legE['instructions']
                if statusE == 'OK':
                    for i in range(len(self.legE)):
                        waypoint = self.legE[i]['interval']
                        start = (coordinates[waypoint[0]][1], coordinates[waypoint[0]][0])
                        end = (coordinates[waypoint[1]][1], coordinates[waypoint[1]][0])
                        duration = int(self.legE[i]['time'])  # second
                        distance = self.legE[i]['distance']  # km
                        start_position = str(start[0]) + ',' + str(start[1])
                        end_position = str(end[0]) + ',' + str(end[1])
                        status, height_start = self.elevation_api(start_position)
                        status1, height_end = self.elevation_api(end_position)
                        while status != 'OK' or status1 != 'OK':  # recheck again
                            status, height_start = self.elevation_api(start_position)
                            status1, height_end = self.elevation_api(end_position)
                        elevation = height_end - height_start  # unit: m
                        if duration <= 0:
                            duration = 1
                        # time = time + duration
                        self.time = self.time + duration
                        speed = math.sqrt(distance ** 2 + elevation ** 2) / duration  # m/s
                        angle = math.atan2(distance * 1000, elevation)  # degree
                        angle = angle if angle > 0 else 0  # we let downard as flat
                        power = self.need_energy.energy(angle=angle, V=speed)
                        energy_consume = 0
                        for t in range(duration):
                            charge = self.battery.use(duration=1, power=power)
                            energy_consume += self.battery.energy_consume
                            self.step_reward -= self.battery.energy_consume / 100000
                            if charge:  # this duration need to charge the battery
                                self.charge_num += 1
                                self.battery.charge(50000)  # make it full capacity
                                # self.step_reward -= 0.1   # we deduct 0.1 point of reward when charge

                current_status = True
                self.current_position = self.start_position

        # self.step_reward = step_reward
        self.current_step_history = step_history
        self.current_position = self.next_position
        batterySOC = self.battery.SOC
        return self.current_position, self.step_reward, current_status, self.charge_num, batterySOC

    def origine_map_reward(self):  # to get the step_reward, chargenum, SOC, time which the route google provided
        leg = self.Google_step['instructions']
        coordinates = self.Google_step['points']['coordinates']
        step_reward = 0
        time = 0
        for i in range(len(leg)):
            print("origine_map_reward for loop index - " + str(i) + " total - " + str(len(leg)) , end = '\r')
            waypoint = leg[i]['interval']
            start = (coordinates[waypoint[0]][1], coordinates[waypoint[0]][0])
            end = (coordinates[waypoint[1]][1], coordinates[waypoint[1]][0])
            duration = int(leg[i]['time'])  # second
            distance = leg[i]['distance']  # km
            start_position = str(start[0]) + ',' + str(start[1])
            end_position = str(end[0]) + ',' + str(end[1])
            status, height_start = self.elevation_api(start_position)
            status1, height_end = self.elevation_api(end_position)
            while status != 'OK' or status1 != 'OK':
                status, height_start = self.elevation_api(start_position)
                status1, height_end = self.elevation_api(end_position)
            elevation = height_end - height_start  # unit: m
            if duration <= 0:
                duration = 1
            time = time + duration
            speed = math.sqrt(distance ** 2 + elevation ** 2) / duration  # m/s
            angle = math.atan2(distance * 1000, elevation)  # degree
            angle = angle if angle > 0 else 0
            power = self.need_energy.energy(angle=angle, V=speed)
            energy_consume = 0
            for t in range(duration):
                charge = self.battery.use(duration=1, power=power)
                energy_consume += self.battery.energy_consume
                step_reward -= self.battery.energy_consume / 100000
                if charge:  # this duration need to charge the battery
                    self.charge_num += 1
                    self.battery.charge(50000)  # make it full capacity
                    # step_reward -= 0.1   # we deduct 0.1 point of reward when charge
        chargenum = self.charge_num
        SOC = self.battery.SOC
        self.battery.charge(50000)  # make it full capacity
        self.battery.use(0, 0)
        self.charge_num = 0
        return step_reward, chargenum, SOC, time

    # def last_end(self, position):
    # self.ii = 0

    def battery_charge(self):
        self.battery.charge(50000)
        self.battery.use(0, 0)
        # self.battery = lithium_ion_battery(50000) #Wh

    def battery_condition(self):
        soc = self.battery.SOC
        charge_numm = self.charge_num
        return soc, charge_numm



'http://localhost:8989/route?point=19.06099,72.82453&point=73.92145,18.51145&profile=car&points_encoded=false'