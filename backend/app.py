from flask import Flask, request, jsonify, render_template_string, send_from_directory
import pandas as pd
import folium
import requests
import polyline
import numpy as np
import json
from itertools import cycle
import os
from geopy.distance import geodesic
from shapely.geometry import LineString, Point
import math
from folium.plugins import PolyLineTextPath

app = Flask(__name__, static_folder='../frontend/dist', static_url_path='')

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)



class Vehicle:
    def __init__(self, cap):
        self.capacity = cap
        self.assigned = False

    def assign(self):
        self.assigned = True

    def unassign(self):
        self.assigned = False

    def display_status(self):
        print(f"Vehicle capacity: {self.capacity}, Assigned: {'Yes' if self.assigned else 'No'}")

class Saving:
    def __init__(self, node_i, node_j, saving_value):
        self.i = node_i
        self.j = node_j
        self.saving = saving_value

    def display_saving(self):
        print(f"Saving between node {self.i} and node {self.j} is: {self.saving}")

    def compare_vehicles_on_capacity(a, b):
        return a.capacity < b.capacity

    def compare_savings(a, b):
        return a.saving > b.saving

def calculate_saving(dist, i, j):
    return dist[0][i-1] + dist[0][j-1] - dist[i-1][j-1]

class Route:
    def __init__(self, load, distance):
        self.customers = []
        self.load = load
        self.distance = distance
        self.vehicle = -1

    def add_customer(self, customer):
        self.customers.append(customer)

    def add_customer_front(self, customer):
        self.customers.insert(0, customer)

    def update_distance(self, distance_matrix):
        self.distance = distance_matrix[0][self.customers[0]]
        for i in range(1, len(self.customers)):
            self.distance += distance_matrix[self.customers[i-1]][self.customers[i]]
        self.distance += distance_matrix[self.customers[-1]][0]

    def update_load(self, load_on_every_node):
        self.load = sum(load_on_every_node[customer] for customer in self.customers)

    def display_route(self):
        print(f"Vehicle: {self.vehicle}, Load: {self.load}, Distance: {self.distance}")
        print(f"Route: {self.customers}")

def compare_routes_based_on_load(a, b):
    return a.load < b.load

def find_route_index(node, routes):
    for i, route in enumerate(routes):
        if route.customers[0] == node or route.customers[-1] == node:
            return i
    return -1


def get_complete_distance_matrix(nodes, api_key):
    base_url = "https://api.openrouteservice.org/v2/matrix/driving-car"
    headers = {
        "Content-Type": "application/json",
        "Authorization": api_key
    }
    # Ensure [longitude, latitude] format for all nodes
    locations = [[node[1], node[0]] for node in nodes]
    body = {
        "locations": locations,
        "sources": list(range(len(nodes))),  # All nodes are sources
        "destinations": list(range(len(nodes))),  # All nodes are destinations
        "metrics": ["distance"]
    }
    
    response = requests.post(base_url, headers=headers, json=body)
    if response.status_code != 200:
        raise ValueError(f"API returned status code {response.status_code}: {response.text}")

    data = response.json()
    # print(data)
    # Debugging: Print the raw response
    # print("Response Data:", data)

    # Check for errors in the response
    if "error" in data:
        if isinstance(data["error"], dict):
            raise ValueError(f"Error from OpenRouteService: {data['error']['message']}")
        else:
            raise ValueError(f"Error from OpenRouteService: {data['error']}")

    # Extract distances into a matrix
    distances = data.get("distances", [])
    if not distances:
        raise ValueError("No distance data found in the response.")
    print(distances)
    return distances

@app.route('/')
def index():
    # Serve the React app
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/process-data', methods=['POST'])
def process_data():
    file = request.files['file']
    numvehicles = int(request.form['numVehicles'])
    capacities = list(map(int, request.form['capacities'].split(',')))
    vehicles = []
    for cap in capacities:
        vehicles.append(Vehicle(cap))

    if len(capacities) != numvehicles:
        return "Number of capacities does not match number of vehicles.", 400

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    # Dummy distance matrix calculation
    excel_file = "./uploads/LocationData.xlsx"
    data = pd.read_excel(excel_file)

    # Handle missing data
    data = data.dropna(subset=[data.columns[0], data.columns[1]])  # Drop rows with NaN in the first or second column

    # Convert to numeric and handle any non-numeric values
    data.iloc[:, 0] = pd.to_numeric(data.iloc[:, 0], errors='coerce')
    data.iloc[:, 1] = pd.to_numeric(data.iloc[:, 1], errors='coerce')

    # Drop rows where conversion resulted in NaN
    data = data.dropna(subset=[data.columns[0], data.columns[1]])

    # Extract nodes as (latitude, longitude) tuples
    nodes = list(zip(data.iloc[:, 0], data.iloc[:, 1]))
    number_of_nodes = len(nodes)
    # print(nodes)
    last_column_name = data.columns[-1]
    # print("Last column name:", last_column_name)

    # Access the last column by its name
    load_on_every_node = data[last_column_name].tolist()
    # print("Load values:", load_on_every_node)
    api_key = "5b3ce3597851110001cf6248b25f679e952847bb9fdf8c814574bcc5"
    max_distance_per_vehicle  = 10000000 
    distance_matrix = get_complete_distance_matrix(nodes, api_key)
    # print(distance_matrix)
    # Dummy routes


    # SORT VEHICLES IN ASCENDING CAPACITIES
    vehicles.sort(key=lambda x: x.capacity)

    # CALCULATE SAVINGS
    savings = []
    for i in range(1, number_of_nodes + 1):
        for j in range(i + 1, number_of_nodes + 1):
            saving_value = calculate_saving(distance_matrix, i, j)
            savings.append(Saving(i, j, saving_value))

    savings.sort(key=lambda x: x.saving, reverse=True)

    # CREATE ROUTES
    # CREATE ROUTES
    routes = []
    for i in range(1, number_of_nodes):  # Ensure the loop goes up to number_of_nodes
        if i <= len(load_on_every_node):  # Check if the index is within bounds for load_on_every_node
            if i < len(distance_matrix[0]):  # Check if the index is within bounds for distance_matrix
                route = Route(load_on_every_node[i], 2 * distance_matrix[0][i])
                route.add_customer(i)
                routes.append(route)
            else:
                print(f"Error: distance_matrix index {i} out of bounds")
                break
        else:
            print(f"Error: load_on_every_node index {i} out of bounds")
            break

    # CONSIDER EVERY SAVING AND MERGE ROUTES.
    for saving in savings:
        i, j = saving.i, saving.j

        # Find which routes nodes i and j are in
        route_idx_i = find_route_index(i, routes)
        route_idx_j = find_route_index(j, routes)

        # If nodes i and j are in different routes
        if route_idx_i != -1 and route_idx_j != -1 and route_idx_i != route_idx_j:
            route_i = routes[route_idx_i]
            route_j = routes[route_idx_j]
            
            # Check if merging these two routes exceeds vehicle capacity
            if route_i.load + route_j.load <= vehicles[-1].capacity and \
               route_i.distance + route_j.distance - saving.saving <= max_distance_per_vehicle:
                # Merge routes: move all customers from routeJ to routeI
                if route_i.customers[0] == i:
                    route_i.customers.reverse()
                if route_j.customers[-1] == j:
                    route_j.customers.reverse()

                route_i.customers.extend(route_j.customers)

                # Update the load and distance of the merged route
                route_i.update_load(load_on_every_node)
                route_i.update_distance(distance_matrix)

                # Remove the old routeJ after merging
                routes.pop(route_idx_j)

    routes.sort(key=lambda route: route.load)

    for vehicle in vehicles:
        vehicle.unassign()

    # ASSIGN VEHICLES TO FINAL ROUTES
    for route in routes:
        # Find the smallest vehicle that can handle this route's load
        for vehicle in vehicles:
            if not vehicle.assigned and vehicle.capacity >= route.load:
                route.vehicle = vehicle.capacity  # Assign vehicle
                vehicle.assign()                   # Mark vehicle as assigned
                break  # Move to the next route once vehicle is assigned
    final_routes = []
    for route in routes:
        final_routes.append(route.customers)
        print(f"{route.vehicle} is vehicle for {route.customers}")
    print(final_routes)

    # Generate map
    nodes = data[['Latitude', 'Longitude','LocationName']].to_dict('records')
    fixed_coordinates = [
        {'longitude': node['Longitude'], 'latitude': node['Latitude']}
        for node in nodes
    ]
    # Initialize the map
    map_obj = folium.Map(location=[22.726348, 75.874801], zoom_start=14)
    initial_node = fixed_coordinates[0]
    def get_route_data(route):
        url2 = "https://api.openrouteservice.org/v2/directions/driving-car/json"
        headers = {"Authorization": "5b3ce3597851110001cf6248873b6bd6bed0487185d13594db9926cd"}  # Replace with your API key
        body = {
            "coordinates": route,            # Pass the route coordinates
            # "radiuses": [10000] * len(route),        # Search up to 5,000 meters for both origin and destination
            "profile": "driving-car",        # Set the profile (driving, walking, etc.)
            "format": "json"                 # Response format
        }
        route.insert(0,[75.874177, 22.726347])
        print(route)

        response = requests.post(url2, json=body, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API request failed with status code {response.status_code}: {response.text}")

    # def plot_routes_on_map(routes_data, nodes, map_obj):
    # Define colors for routes and markers
        route_colors = ["blue", "red", "green", "purple", "orange", "brown", "pink", "black", "yellow"]
        marker_colors = ["blue", "red", "green", "purple", "orange", "darkred", "cadetblue", "gray", "darkpurple"]
    
        route_color_cycle = cycle(route_colors)
        marker_color_cycle = cycle(marker_colors)

        # Plot all routes
        for idx, route_data in enumerate(routes_data, start=1):
            coordinates = polyline.decode(route_data["geometry"])  # Decode polyline
            route_color = next(route_color_cycle)

            # Optional: Extract route node info for tooltip (if available)
            node_list = route_data.get("nodes", [])  # You need to pass this in routes_data
            tooltip_text = f"Route {idx}" if not node_list else f"Route {idx}: " + " → ".join(map(str, node_list))

            # Draw the route with hover tooltip
            line = folium.PolyLine(
                locations=coordinates,
                color=route_color,
                weight=5,
                opacity=0.6,
                tooltip=tooltip_text
                ).add_to(map_obj)

            # Add directional arrows to the route
            PolyLineTextPath(
            line,
            '   ▶   ',
            repeat=True,
            offset=7,
            attributes={'fill': route_color, 'font-weight': 'bold', 'font-size': '16'}
            ).add_to(map_obj)

        # Plot all node markers
        for node in nodes:
            marker_color = next(marker_color_cycle)
            location = [node['Longitude'], node['Latitude']]
            folium.Marker(
            location,
            popup=str(node),
            icon=folium.Icon(color=marker_color)
            ).add_to(map_obj)

        # Save the map
        map_obj.save("routes_map.html")
        print("✅ Map saved as routes_map.html")



    def plot_routes_on_map(routes_data):
        
        colors = ["blue", "red", "green", "purple", "orange", "brown", "pink", "black", "yellow"]
        color_cycle = cycle(colors)  # Cycle through the colors list
        # Iterate over all routes and add them to the map
        for idx, route_data in enumerate(routes_data, start=1):
            # Decode the geometry (polyline) to coordinates
            coordinates = polyline.decode(route_data["geometry"])
            # Get the next color from the cycle
            route_color = next(color_cycle)
            # Add the route to the map
            line = folium.PolyLine(
                locations=coordinates,
                color=route_color,
                weight=5,
                opacity=0.5,
                tooltip=f"Route {idx}"
        ).add_to(map_obj)
            PolyLineTextPath(
            line,
            '   ◀   ',
            repeat=True,
            offset=7.5,
            attributes={'fill': route_color, 'font-weight': 'bold', 'font-size': '16'}
        ).add_to(map_obj)
        
        for node in nodes:
            node_colour = next(color_cycle)
            location = [node['Longitude'], node['Latitude']]
            folium.Marker(location,
                        popup=f"{node['LocationName']}",
                           icon=folium.Icon(color=node_colour)).add_to(map_obj)
        
        # Save the map to an HTML file and display it
        map_obj.save("routes_map.html")
        print("Map saved as routes_map.html")
    def map_routes_to_coordinates(routes, nodes):
        mapped_routes = []
        for route in routes:
        # Convert indices to [Longitude, Latitude] format
            mapped_route = [[nodes[index]['Latitude'],nodes[index]['Longitude']] for index in route]
            mapped_routes.append(mapped_route)
        print("Mapped Routes:", mapped_routes)
        return mapped_routes

    routes_as_indices = final_routes  # Read routes as indices
    print(routes_as_indices)
    mapped_routes = map_routes_to_coordinates(routes_as_indices, nodes)  # Map to coordinates

    routes_data = []
    for idx, route in enumerate(mapped_routes, start=1):
        print(f"Fetching data for route {idx}...")
        try:
            response_data = get_route_data(route)
            # Extract the first route's data
            if "routes" in response_data and len(response_data["routes"]) > 0:
                routes_data.append(response_data["routes"][0])  # Add the first route only
            else:
                print(f"No route data found for route {idx}.")
        except Exception as e:
            print(f"Error fetching data for route {idx}: {e}")
    if(routes_data):
        map_obj = folium.Map(location=[22.7196, 75.8577], zoom_start=13)
        plot_routes_on_map(routes_data)
    # if routes_data:
    #     plot_routes_on_map(routes_data)
    # map_route = folium.Map(location=[nodes[0]['Latitude'], nodes[0]['Longitude']], zoom_start=13)
    

    # for route in routes:
    #     coordinates = [(nodes[node]['Latitude'], nodes[node]['Longitude']) for node in route]
    #     folium.PolyLine(coordinates, color="blue", weight=2.5, opacity=1).add_to(map_route)
    #     for lat, lon in coordinates:
    #         folium.Marker([lat, lon]).add_to(map_route)

    map_html = map_obj._repr_html_()

    return map_html

@app.route('/<path:path>')
def serve_static(path):
    # Serve static files for React
    return send_from_directory(app.static_folder, path)

if __name__ == '__main__':
    app.run(debug=True)
