import os
import sys
import time
import logging

import geojson
import requests

from shared import get_osm_geojson, elevate_tags_to_properties


GRAPHQL_ENDPOINT = "https://api-ext.ireland-census-preview.cantabular.com/graphql"

COUNTY_CATEGORIES_QUERY = """
query VariableCategories {
  dataset(name: "Ireland-1911-no-SDC") {
    variables(names: ["county_geoid"]) {
      edges {
        node {
          categories {
            edges {
              node {
                code
                label
              }
            }
          }
        }
      }
    }
  }
}
"""

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
LOGGER.addHandler(handler)


def get_county_names():
  response = requests.post(GRAPHQL_ENDPOINT, data={
    "query": COUNTY_CATEGORIES_QUERY
  })
  response.raise_for_status()

  json = response.json()
  if "errors" in json:
      raise RuntimeError(json["errors"][0]["message"])
  
  category_edges = json["data"]["dataset"]["variables"]["edges"][0]["node"]["categories"]["edges"]
  
  return [translate_county_name(e["node"]["label"]) for e in category_edges]


def translate_county_name(name):
  # Translate historic county names into
  # modern equivalents to send to Overpass
  translations = {
    "Queen's Co.": "Laois",
	  "King's Co.": "Offaly",
  }
  
  if name in translations.keys():
    name = translations[name]

  return "County " + name


def create_overpass_query(county):
  query = f"""
  [out:json][timeout:30];
  area["admin_level"="6"]["name"="{county}"];
  (
    relation(area)["admin_level"="9"];
  );
  (._;>;);
  out body;
  """
  return query


def process_features(geo, county):
  if len(geo["features"]) == 0:
    LOGGER.warning("No features found in OSM data for %s", county)
  
  for feature in geo["features"]:
    # Add the name of the county so we can cross-reference
    # against the names from the census data 
    feature["properties"]["county"] = county
    
    # Move OSM tags up into feature properties
    feature = elevate_tags_to_properties(feature)

  return geo["features"]


def main():
  LOGGER.info("Getting county names from Cantabular Extended API")
  county_names = get_county_names()

  # Dict used to combine together all the features
  # fetched from OSM
  output = {"type": "FeatureCollection", "features": []}

  for county in county_names:
    query = create_overpass_query(county)

    # Keep retrying the request to Overpass
    # (up to a max of 5 times) until it returns data
    result = False
    i = 0
    while result == False and i < 5:
      i += 1
      LOGGER.info("Querying Overpass for %s DEDs", county)
      result = get_osm_geojson(query)
    
    if result:
      LOGGER.info("Processing DED data for %s", county)
      features = process_features(result, county)
      output["features"].extend(features)
    else:
      LOGGER.warning("No DED data received for %s", county)
    
    # Add a delay between requests to be kind and to limit
    # the number of times we have to back-off for a longer
    # period
    LOGGER.info("Pausing for 20 seconds")
    time.sleep(20)
  
  LOGGER.info("Writing output file")
  with open("./out/deds.geojson", mode="w") as f:
    geojson.dump(output, f)

  # TODO: consider using https://github.com/mattijn/topojson to simplify and compress


if __name__ == "__main__":
  main()