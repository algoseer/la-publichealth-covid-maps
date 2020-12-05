import bs4 as bs
import urllib.request
import json
import folium
import numpy as np
import collections

source = urllib.request.urlopen('http://ph.lacounty.gov/media/coronavirus/locations.htm#nonres-settings')
soup = bs.BeautifulSoup(source, features="html.parser")

table = soup.findAll('table', {"class":"table table-striped table-bordered table-sm overflow-y"})

table_rows = table[0].find_all('tr')



locs=[]

for tr in table_rows[1:-1]:
	td = tr.find_all('td')
	row = [i.text for i in td]

	d = dict(zip(["city", "case", "case-rate", "death", "death-rate"], row))

	locs.append(d)


# Parse by zip 
from collections import defaultdict
cases_by_area= {}
deaths_by_area= {}
normcases_by_area = {}
normdeaths_by_area = {}

for d in locs:
	
	city = d["city"]
	if city.startswith('City of'):
		city = city.replace('City of ','')
	elif city.startswith('Los Angeles -'):
		city = city.replace('Los Angeles - ','')
	elif city.startswith('Unincorporated'):
		city = city.replace('Unincorporated - ','')

	if int(d["case"]) == 0:
		continue

	cases_by_area[city]=int(d["case"])
	deaths_by_area[city]=int(d["death"])
	normcases_by_area[city] = int(d["case-rate"])
	normdeaths_by_area[city] = int(d["death-rate"])


areas = list(cases_by_area.keys())

with open('la_county.json') as fin:
	data = json.load(fin)


geozips = []
for i in range(len(data['features'])):
	if data['features'][i]['properties']['name'] in areas:
		dd = data['features'][i]
		dd['properties']['cases'] = cases_by_area[dd['properties']['name']]
		dd['properties']['deaths'] = deaths_by_area[dd['properties']['name']]
		dd['properties']['rate'] = normcases_by_area[dd['properties']['name']]
		dd['properties']['drate'] = normdeaths_by_area[dd['properties']['name']]

		geozips.append(dd)

new_json = dict.fromkeys(['type','features'])
new_json['type'] = 'FeatureCollection'
new_json['features'] = geozips


la_geo = 'data.json'
with open(la_geo,'w') as fout:
	json.dump(new_json, fout, sort_keys=True, indent=4, separators=(',',': '))


m = folium.Map(location = [34.0522, -118.2437], zoom_start = 11)

log_cases_by_area = {k:np.log2(cases_by_area[k]) for k in cases_by_area if cases_by_area[k]>0}

log_cases = folium.Choropleth(geo_data = la_geo,
	fill_opacity = 0.7,
	line_opactiy = 0.2,
	name="log NCOV cases",
	data = log_cases_by_area,
	key_on = 'feature.properties.name',
	fill_color = 'YlOrRd'
	)
log_cases.add_to(m)

log_cases.geojson.add_child(folium.features.GeoJsonTooltip(fields=['name','cases','deaths','rate','drate'], aliases=['Name', "Cases", "Cases per 1000", "Deaths","Deaths per 1000"],labels = True))

folium.LayerControl().add_to(m)

m.save(outfile = 'cities.html')
