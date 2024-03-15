
# Instructions from the users
path_to_input_data = str(input(r"Paste path to your input dataset which must be in .parquet format (example C:\Users\..\..\imput_data.parquet): "))
path_to_out_dir = str(input(r"Paste the path to directory where the program will store the outputs (example C:\Users\..\..\tomtom_work: "))
N_route = int(input("Specify the number of routes you want to retrieve information (2000 for example but must be <= 2400): "))
N_waypoint = int(input("Specify the number of waypoints you want (150 for example but must <= 150: "))
batch_size = int(input("Specify the number of route in each output (for example for batch_size = 200 and N=2000, you will have 12 outputs with 200 routes in each output: "))
put_tomtom_key = str(input("Specify your API key (for example cykhzugopuybe.. <= 150): "))

# Import packages
import os
import time
from tqdm import tqdm
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import pyarrow.parquet as pq
import numpy as np
import geopandas as gpd
from shapely.geometry import LineString

# Define path to the directory where to store the outputs
os.chdir(path_to_out_dir)
os.getcwd

# Import the input data (in .parquet format)
gdf = gpd.read_parquet(path_to_input_data)

# Constituons N itinéaires avec un nombre "size" de noeuds
def generate_random_nodes(gdf, random_seed, N, size):
    start_time = time.time()
    RNG = np.random.default_rng(random_seed)
    selected_nodes = RNG.choice(gdf["source"], size = (N, size), replace = True)
    source_to_geometry = dict(zip(gdf["source"], gdf["geometry"]))
    node_geometries = np.array([[source_to_geometry.get(node) for node in nodes] for nodes in selected_nodes])
    coordinates = np.array([[(geom.xy[0][0], geom.xy[1][0]) for geom in row] for row in node_geometries])
    coordinates = coordinates.reshape(N, -1)
    end_time = time.time()
    print("Time taken in secondes:", end_time - start_time)
    return selected_nodes, coordinates

nodes, coordinates = generate_random_nodes(gdf=gdf, random_seed=13081996, N=N_route, size=N_waypoint)

# Via les reqêtes à l' API routing de TomTom, recupérons les informations sur les itinéaires constitués 
def make_tomtom_request(url, session, params):
    start_time = time.time()
    try:
        with session.get(url, params=params, stream=True) as response:
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                return None
    except Exception as e:
        return None


def process_batch(url_base, params, key, nodes, coordinates_batch, session):
    batch_results = []
    batch_tomtom_time = 0
    with tqdm(total=len(coordinates_batch), desc="Processing") as pbar:
        for points in coordinates_batch:
            
            url = f"{url_base}{':'.join([f'{lat},{lon}' for lat, lon in zip(points[1::2], points[::2])])}/json?key={key}"
            start_tomtom_time = time.time()
            data = make_tomtom_request(url, session, params)
            iteration_tomtom_time = time.time() - start_tomtom_time            
            batch_tomtom_time += iteration_tomtom_time
                       
            if data and "routes" in data:
                for route_index, route in enumerate(data["routes"]):
                    nodes_index = route_index
                    for leg_index, leg in enumerate(route['legs']):
                        source_index = nodes_index + leg_index
                        target_index = nodes_index + leg_index + 1
                        geom = LineString([[p["longitude"], p["latitude"]] for p in leg["points"]])
                        res = {
                            "source": nodes[route_index][source_index],
                            "target": nodes[route_index][target_index],                  
                            "length": leg["summary"]["lengthInMeters"],
                            "tt": leg["summary"]["noTrafficTravelTimeInSeconds"],
                            "tt_traffic": leg["summary"]["travelTimeInSeconds"],
                            "tt_historical": leg["summary"]["historicTrafficTravelTimeInSeconds"],
                            "geometry": geom,
                        }
                        batch_results.append(res)           
            else:
                pass
            pbar.update(1)
    return batch_results, batch_tomtom_time


def get_tomtom_data(url_base, params, key, nodes, coordinates, batch_size, max_retries=2):
    error_count = 0
    od_error = {}
    
    session = requests.Session()
    retries = Retry(total=max_retries, backoff_factor=0.)
    session.mount('https://', HTTPAdapter(max_retries=retries))
    
    total_iterations = len(coordinates)
    total_batches = total_iterations // batch_size + (1 if total_iterations % batch_size != 0 else 0)
    start_total_time = time.time()

    for i in range(total_batches):
        start_index = i * batch_size
        end_index = min((i + 1) * batch_size, total_iterations)
        coordinates_batch = coordinates[start_index:end_index]
        
        batch_results, batch_tomtom_time = process_batch(url_base, params, key, nodes, coordinates_batch, session)
        gdf = gpd.GeoDataFrame(batch_results)
        gdf.to_parquet(f'batch_results_{i}.parquet', index=False)
        print("Time just for tomtom request:", batch_tomtom_time)
        yield 
        

    end_total_time = time.time()
    total_code_time = end_total_time - start_total_time


url_base = 'https://api.tomtom.com/routing/1/calculateRoute/'
key = put_tomtom_key
params = {
    "computeTravelTimeFor": "all",
    "departAt": "2024-07-30T03:30:0"
}

for _ in get_tomtom_data(url_base=url_base, params=params, key=key, nodes=nodes, coordinates=coordinates, batch_size=batch_size):
    pass