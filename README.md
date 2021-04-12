# Fetch Ireland electoral division boundaries from OSM

This script gets DED spatial boundaries from OSM per county for each of the counties on the
island of Ireland. The list of counties comes from a Cantabular dataset built from Irish
1911 Census data derived from the digitised census returns on the National Archives of
Ireland website.

The OSM source is the Overpass API at https://overpass-api.de/api/interpreter.

DED geometries taken from OSM are converted to GeoJSON and then the name of the containing
county is added in a `county` field within each GeoJSON feature's `properties` field. So
the data can be matched up with census data held in Cantabular.

## Requirements

Listed in `pyproject.toml`.
