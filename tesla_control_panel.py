import json
import requests
import time
import tkinter as tk

#Tesla API class
class TeslaAPI:
    TOKEN_FILENAME = "tesla_token.json"
    API_URL = 'https://owner-api.teslamotors.com/api/1'
    HEADERS = {"content-type": "application/json; charset=UTF-8"}

    def __init__(self):
        with open(self.TOKEN_FILENAME, 'r') as f:
            self.token = json.load(f)
            self.headers = {**self.HEADERS, 'Authorization': 'Bearer {}'.format(self.token["access_token"])}

    def make_request(self, method, endpoint, data=None):
        response = requests.request(method, f'{self.API_URL}/{endpoint}', headers=self.headers, data=data)
        response.raise_for_status()
        return response.json()

    def get_vehicle(self):
        response = self.make_request('GET', 'vehicles')
        if "response" in response and response["response"]:
            return response["response"][0]
        else:
            return None

    #wake up the vehicle before sending a request
    def wake_up(self, vehicle_id):
        for _ in range(10):
            response = self.make_request('POST', f'vehicles/{vehicle_id}/wake_up')
            if response["response"]["state"] == 'online':
                break
            time.sleep(5)

    def get_vehicle_data(self, vehicle_id):
        return self.make_request('GET', f'vehicles/{vehicle_id}/vehicle_data')["response"]

    def start_climate(self, vehicle_id):
        return self.make_request('POST', f'vehicles/{vehicle_id}/command/auto_conditioning_start')["response"]

    def stop_climate(self, vehicle_id):
        return self.make_request('POST', f'vehicles/{vehicle_id}/command/auto_conditioning_stop')["response"]

tesla_api = TeslaAPI()

#gets vehicle info the first time the GUI is opened
def initialize_vehicle_info():
    vehicle = tesla_api.get_vehicle()
    if vehicle:
        if vehicle["state"] != "offline":
            tesla_api.wake_up(vehicle["id"])
            vehicle_data = tesla_api.get_vehicle_data(vehicle["id"])

            vehicle_label.configure(text=f"Vehicle: {vehicle['display_name']}")
            battery_label.configure(text=f"Battery Level: {vehicle_data['charge_state']['battery_level']}%")
            charging_label.configure(text=f"Charging: {vehicle_data['charge_state']['charging_state']}")
            status_label.configure(text=f"Vehicle Status: {vehicle['state']}")

            if vehicle["state"] == "offline":
                status_label.configure(fg="red")
            else:
                status_label.configure(fg="green")
        else:
            set_offline_info()
    else:
        set_offline_info()

#if car is offline, this info will show in GUI
def set_offline_info():
    vehicle_label.configure(text="Vehicle: - (Offline)")
    battery_label.configure(text="Battery Level: -")
    charging_label.configure(text="Charging: -")
    status_label.configure(text="Vehicle Status: -")
    status_label.configure(fg="red")

#this is for the Refresh Data Button
def update_vehicle_info():
    try:
        initialize_vehicle_info()
        message_label.configure(text="Data refresh successful", fg="green")
    except Exception as e:
        message_label.configure(text=f"Error refreshing data: {str(e)}", fg="red")

def start_climate():
    vehicle = tesla_api.get_vehicle()
    
    if vehicle and vehicle["state"] != "offline":
        result = tesla_api.start_climate(vehicle["id"])
        if result["result"]:
            message_label.configure(text="Climate started", fg="green")
        else:
            message_label.configure(text=result["reason"], fg="red")
    else:
        message_label.configure(text="Cannot start climate (Vehicle offline)", fg="red")

def stop_climate():
    vehicle = tesla_api.get_vehicle()
    
    if vehicle and vehicle["state"] != "offline":
        result = tesla_api.stop_climate(vehicle["id"])
        if result["result"]:
            message_label.configure(text="Climate stopped", fg="red")
        else:
            message_label.configure(text=result["reason"], fg="red")
    else:
        message_label.configure(text="Cannot stop climate (Vehicle offline)", fg="red")

def close_app():
    root.destroy()

#create GUI window
root = tk.Tk()
root.title("Tesla Vehicle Info")
root.geometry("250x300")

vehicle_label = tk.Label(root, text="Vehicle: - (Offline)")
vehicle_label.pack(pady=10)

battery_label = tk.Label(root, text="Battery Level: -")
battery_label.pack(pady=5)

charging_label = tk.Label(root, text="Charging: -")
charging_label.pack(pady=5)

status_label = tk.Label(root, text="Vehicle Status: -")
status_label.pack(pady=5)

message_label = tk.Label(root, text="", fg="green")
message_label.pack(pady=5)

refresh_button = tk.Button(root, text="Refresh Data", command=update_vehicle_info)
refresh_button.pack(pady=10)

climate_frame = tk.Frame(root)
climate_frame.pack(pady=10)

start_climate_button = tk.Button(climate_frame, text="Start Climate", command=start_climate)
start_climate_button.pack(side=tk.LEFT)

stop_climate_button = tk.Button(climate_frame, text="Stop Climate", command=stop_climate)
stop_climate_button.pack(side=tk.LEFT, padx=5)

close_button = tk.Button(root, text="Close", command=close_app)
close_button.pack(pady=0)

initialize_vehicle_info()

#run the GUI event loop
root.mainloop()
