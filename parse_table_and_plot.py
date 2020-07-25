import bs4 as bs
import urllib.request
import json
import folium
import numpy as np
import collections

source = urllib.request.urlopen('http://ph.lacounty.gov/media/coronavirus/locations.htm#nonres-settings')
soup = bs.BeautifulSoup(source, features="html.parser")

table = soup.findAll('table', {"class":"table table-striped table-bordered table-sm"})

table_rows = table[2].find_all('tr')

locs=[]

for tr in table_rows[1:-1]:
	td = tr.find_all('td')
	row = [i.text for i in td]

	d = dict(zip(["id", "name", "address", "cases", "symptomatic"], row))

	locs.append(d)

# Parse by zip 
from collections import defaultdict
cases_by_zip=defaultdict(int)
names_by_zip=defaultdict(list)

for d in locs:
	zipcode =d["address"].split(', ')[-1]

	cases_by_zip[zipcode]+=int(d["cases"])
	names_by_zip[zipcode].append(d["name"])


allzips = list(cases_by_zip.keys())

with open('la-zip-code-areas-2012.json') as fin:
	data = json.load(fin)


geozips = []
for i in range(len(data['features'])):
	if data['features'][i]['properties']['name'] in allzips:
		dd = data['features'][i]
		dd['properties']['cases'] = cases_by_zip[dd['properties']['name']]
		dd['properties']['businesses'] = '_'.join(names_by_zip[dd['properties']['name']])
		geozips.append(dd)

new_json = dict.fromkeys(['type','features'])
new_json['type'] = 'FeatureCollection'
new_json['features'] = geozips


la_geo = 'data.json'
with open(la_geo,'w') as fout:
	json.dump(new_json, fout, sort_keys=True, indent=4, separators=(',',': '))


m = folium.Map(location = [34.0522, -118.2437], zoom_start = 11)

cases = folium.Choropleth(geo_data = la_geo,
	fill_opacity = 0.7,
	line_opactiy = 0.2,
	name="NCOV cases",
	data = cases_by_zip,
	key_on = 'feature.properties.name',
	fill_color = 'YlOrRd'
	)
cases.add_to(m)


cases.geojson.add_child(folium.features.GeoJsonTooltip(fields=['name','cases'], aliases=["Zipcode","#Cases"],labels = True))

folium.LayerControl().add_to(m)

m.save(outfile = 'index.html')
