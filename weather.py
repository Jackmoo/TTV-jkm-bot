#!/usr/bin/python
# -*- coding: utf8 -*-

#import requests
import json
import urllib2

# from https://works.ioa.tw/weather/api/doc/index.html
class Weather:
    def __init__(self):
        self.all_location = json.load(urllib2.urlopen('https://works.ioa.tw/weather/api/all.json'))
    
    def get_weather(self, city, towns):
        #print self.all_location[0]['name']
        #print self.all_location[0]['towns'][2]['name']

        city = city.decode('utf-8')
        towns = towns.decode('utf-8')

        found_city = False
        city_index = 0
        for idx, city_dict in enumerate(self.all_location):
            if city_dict['name'] == city:
                found_city = True
                city_index = idx
                break
        if not found_city:
            return '', 0

        found_towns = False
        towns_id = 0
        towns_name = ''
        for idx, towns_dict in enumerate(self.all_location[city_index]['towns']):
            print towns_dict['name']
            if towns in towns_dict['name']:
                towns_name = towns_dict['name']
                found_towns = True
                towns_id = towns_dict['id']
                break
        # if cannot find towns, use the 1st data in towns
        if not found_towns:
            towns_name = self.all_location[city_index]['towns'][0]['name']
            towns_id = self.all_location[city_index]['towns'][0]['id']

        weather_dict = json.load(urllib2.urlopen('https://works.ioa.tw/weather/api/weathers/%s.json' % towns_id))
        #print weather_dict['desc']
        #print weather_dict['specials'][0]['desc']
        return towns_name, weather_dict

 
if __name__ == '__main__':
    print Weather().get_weather('高雄', '大寮區')
