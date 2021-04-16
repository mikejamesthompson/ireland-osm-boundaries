import sys
import logging

import geojson
from shapely.geometry import shape

from shared import get_osm_geojson, elevate_tags_to_properties


LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
LOGGER.addHandler(handler)


def filter_features_by_county(features, county):
  filtered = []
  for feature in features:
    if feature["properties"]["county"] == county:
     filtered.append(feature)
  return filtered


def create_overpass_query(county):
  query = f"""
  [out:json][timeout:45];
  area["admin_level"="6"]["name"="County {county}"];
  (
    relation(area)["admin_level"="10"];
  );
  (._;>;);
  out body;
  """
  return query


def match_townlands_to_deds(townlands, deds):
  output = []

  for townland in townlands:
    townland = elevate_tags_to_properties(townland)
    townland_centroid = shape(townland["geometry"]).centroid

    for ded in deds:
      ded_shape = shape(ded["geometry"])
      if ded_shape.contains(townland_centroid):
        townland["properties"]["county"] = ded["properties"]["county"]
        townland["properties"]["ded"] = ded["properties"]["name"]
        output.append(townland)
        # Stop looking through deds and move onto the next townland
        # if we've found its parent
        break
  
  return output


def main():
  county = "Tyrone"

  LOGGER.info("Loading DED data")
  with open("./out/deds.geojson", mode="r") as f:
    ded_data = geojson.load(f)
    deds = filter_features_by_county(ded_data["features"], county)
  
  query = create_overpass_query(county)

  LOGGER.info("Querying Overpass for %s Townlands", county)
  townland_data = get_osm_geojson(query)
  
  if len(townland_data["features"]) == 0:
    LOGGER.warning("No features found in OSM data for %s", county)

  LOGGER.info("Processing townland data for %s", county)
  county_townlands = match_townlands_to_deds(townland_data["features"], deds)

  output = {"type": "FeatureCollection", "features": county_townlands}

  LOGGER.info("Writing output file")
  with open("./out/townlands.geojson", mode="w") as f:
    geojson.dump(output, f)


if __name__ == "__main__":
  main()