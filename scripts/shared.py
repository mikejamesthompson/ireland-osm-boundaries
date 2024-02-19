import logging
import requests

from osm2geojson import json2geojson


OVERPASS_ENDPOINT = "https://overpass-api.de/api/interpreter"

LOGGER = logging.getLogger(__name__)


def get_osm_geojson(query):
  response = requests.post(OVERPASS_ENDPOINT, 
    data={"data": query},
    headers={'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'})
  
  # If we receive 429 Too Many Requests or 504 Gateway Timeout
  # then back off and return False to trigger a retry
  # Response codes documented at: http://overpass-api.de/command_line.html
  if response.status_code == 429:
    LOGGER.info("Received too many requests response from Overpass")
    LOGGER.info("Waiting for 10 minutes")
    time.sleep(600)
    return False
  elif response.status_code == 504:
    LOGGER.info("Received gateway timeout response from Overpass")
    LOGGER.info("Waiting for 10 minutes")
    time.sleep(600)
    return False
  else:
    response.raise_for_status()
  
  json = response.json()
  
  try:
    geojson = json2geojson(json)
  except Exception:
    LOGGER.warning("Failed to convert OSM JSON to GeoJSON for query '%s'", query)
    geojson = None

  return geojson


def elevate_tags_to_properties(feature):
  """
  Move all the properties in the sub-field "tags"
  into the higher level properties field so it's
  easier to work with.
  """
  for tag in feature["properties"]["tags"].keys():
    feature["properties"][tag] = feature["properties"]["tags"][tag]
  
  del feature["properties"]["tags"]

  return feature