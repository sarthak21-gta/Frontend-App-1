import os
import requests
from flask import Flask, render_template, redirect, url_for, request, flash
from datetime import datetime

app = Flask(__name__)
app.secret_key = "parking_secret_key"

import os
import requests
import api

VERCEL_URL = os.environ.get('VERCEL_URL')
API_BASE = f"https://{VERCEL_URL}/api" if VERCEL_URL else "http://localhost:8080"

# --- MONKEY PATCH FOR VERCEL SSO / LOCAL DIRECT ROUTING ---
# To bypass Vercel SSO blocking our internal API HTTP requests and to speed things up,
# we route all requests to API_BASE directly to the api.py test_client.
api_client = api.app.test_client()

class FakeResponse:
    def __init__(self, res):
        self.text = res.get_data(as_text=True)
        self.status_code = res.status_code
    def json(self):
        import json
        try:
            return json.loads(self.text)
        except json.JSONDecodeError:
            return {}

def direct_api_request(method, url, **kwargs):
    if url.startswith(API_BASE):
        path = url.replace(API_BASE, "")
        if not path.startswith('/'):
            path = '/' + path
            
        if method == "GET":
            res = api_client.get(path, query_string=kwargs.get('params'))
        elif method == "POST":
            res = api_client.post(path, query_string=kwargs.get('params'), json=kwargs.get('json'))
        elif method == "PUT":
            res = api_client.put(path, query_string=kwargs.get('params'), json=kwargs.get('json'))
        elif method == "DELETE":
            res = api_client.delete(path, query_string=kwargs.get('params'))
        return FakeResponse(res)
    # Fallback to real requests for other URLs
    return getattr(requests, method.lower())(url, **kwargs)

# Override requests methods
requests.get = lambda url, **kwargs: direct_api_request("GET", url, **kwargs)
requests.post = lambda url, **kwargs: direct_api_request("POST", url, **kwargs)
requests.put = lambda url, **kwargs: direct_api_request("PUT", url, **kwargs)
requests.delete = lambda url, **kwargs: direct_api_request("DELETE", url, **kwargs)
# ---------------------------------------------------------
@app.route("/")
def return_index():
    return redirect(url_for('dashboard'))

@app.route("/parking-management")
def index():
    return redirect(url_for('dashboard'))

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/parking-management/dashboard")
def dashboard():
    try:
        totalCars = requests.get(f"{API_BASE}/dashboard/total-cars").json()
        totalActiveParkings = requests.get(f"{API_BASE}/dashboard/total-active-parkings").json()
        totalLots = requests.get(f"{API_BASE}/dashboard/total-parking-lots").json()
        totalUnoccupiedLots = requests.get(f"{API_BASE}/dashboard/total-unoccupied-parking-lots").json()
        totalPaidPaymentsToday = requests.get(f"{API_BASE}/dashboard/total-paid-payments-value-today").json()
        totalPendingPayments = requests.get(f"{API_BASE}/dashboard/total-pending-payments").json()
        totalParkingsToday = requests.get(f"{API_BASE}/dashboard/total-parkings-today").json()
        return render_template("dashboard.html", totalCars=totalCars, totalActiveParkings=totalActiveParkings,
                               totalLots=totalLots, totalUnoccupiedLots=totalUnoccupiedLots,
                               totalPaidPaymentsToday=totalPaidPaymentsToday, totalPendingPayments=totalPendingPayments,
                               totalParkingsToday=totalParkingsToday)
    except Exception as e:
        return f"Error connecting to Spring API on {API_BASE}: {str(e)}", 500

# ------------------ PARKING LOTS ---------------------
@app.route("/parking-management/parking-lots/filter/<int:filter_type>", methods=["GET", "POST"])
def parkingLots(filter_type):
    match filter_type:
        case 1:
            req = requests.get(f"{API_BASE}/parkingLots").json()
        case 2:
            req = requests.get(f"{API_BASE}/parkingLots/unoccupied").json()
        case 3:
            req = requests.get(f"{API_BASE}/parkingLots/occupied").json()
    return render_template("parkingLots.html", parkingLots=req)

@app.route("/parking-management/parking-lots/create", methods=["GET", "POST"])
def createParkingLot():
    if request.method == "GET":
        return render_template("createParkingLot.html")
    if request.method == "POST":
        tag = request.form.get("tag")
        data = {"tag": tag}
        requests.post(f"{API_BASE}/parkingLots", json=data)
        return redirect(url_for("parkingLots", filter_type=1))
    
@app.route("/parking-management/parking-lots/delete/<int:id>", methods=["GET", "POST"])
def deleteParkingLot(id):
    requests.delete(f"{API_BASE}/parkingLots/{id}")
    return redirect(url_for("parkingLots", filter_type=1))

@app.route("/parking-management/parking-lots/edit/<int:id>", methods=["GET", "POST"])
def editParkingLot(id):
    if request.method == "GET":
        parkingLot = requests.get(f"{API_BASE}/parkingLots/{id}").json()
        return render_template("editParkingLot.html", parkingLot=parkingLot)
    if request.method == "POST":
        data = {"tag": request.form.get("tag")}
        requests.put(f"{API_BASE}/parkingLots/{id}", json=data)
        return redirect(url_for("parkingLots", filter_type=1))

# ------------------ CARS ---------------------
@app.route("/parking-management/cars")
def cars():
    req = requests.get(f"{API_BASE}/cars").json()
    return render_template("cars.html", cars=req)

@app.route("/parking-management/cars/create", methods=["GET", "POST"])
def createCar():
    if request.method == "GET":
        return render_template("createCar.html")
    if request.method == "POST":
        data = {"licensePlate": request.form.get("licensePlate"), "brand": request.form.get("brand"), "model": request.form.get("model"), "color": request.form.get("color")}
        requests.post(f"{API_BASE}/cars", json=data)
        return redirect(url_for("cars"))
    
@app.route("/parking-management/cars/delete/<int:id>", methods=["GET", "POST"])
def deleteCar(id):
    requests.delete(f"{API_BASE}/cars/{id}")
    return redirect(url_for("cars"))

@app.route("/parking-management/cars/edit/<int:id>", methods=["GET", "POST"])
def editCar(id):
    if request.method == "GET":
        car = requests.get(f"{API_BASE}/cars/{id}").json()
        return render_template("editCar.html", car=car)
    if request.method == "POST":
        data = {"licensePlate": request.form.get("licensePlate"), "brand": request.form.get("brand"), "model": request.form.get("model"), "color": request.form.get("color")}
        requests.put(f"{API_BASE}/cars/{id}", json=data)
        return redirect(url_for("cars"))
    
@app.route("/parking-management/cars/parkings/<int:id>/filter/<int:filter_type>", methods=["GET"])
def carParkings(id, filter_type):
    if request.method == "GET":
        match filter_type:
            case 1:
                parkings = requests.get(f"{API_BASE}/parkings/search?carId={id}").json()
            case 2:
                parkings = requests.get(f"{API_BASE}/parkings/going?carId={id}").json()
            case 3:
                parkings = requests.get(f"{API_BASE}/parkings/ended?carId={id}").json()
        car = requests.get(f"{API_BASE}/cars/{id}").json()
        return render_template("carParkings.html", parkings=parkings, car=car)

# ------------------ PARKINGS ---------------------
@app.route("/parking-management/parkings/filter/<int:filter_type>")
def parkings(filter_type):
    match filter_type:
        case 1:
            req = requests.get(f"{API_BASE}/parkings").json()
        case 2:
            req = requests.get(f"{API_BASE}/parkings/going").json()
        case 3:
            req = requests.get(f"{API_BASE}/parkings/ended").json()
    return render_template("parkings.html", parkings=req)

@app.route("/parking-management/parkings/create", methods=["GET", "POST"])
def createParking():
    if request.method == "GET":
        cars_req = requests.get(f"{API_BASE}/cars/inParkingFalse").json()
        parkingLots = requests.get(f"{API_BASE}/parkingLots/unoccupied").json()
        return render_template("createParking.html", cars=cars_req, parkingLots=parkingLots)
    if request.method == "POST":
        url = f"{API_BASE}/parkings/insert?carId={{carId}}&parkingLotId={{parkingLotId}}"
        data = {"startTime": request.form.get("startTime"), "rate": request.form.get("rate")}
        carId = request.form["carId"]
        parkingLotId = request.form["parkingLotId"]
        url = url.format(carId=carId, parkingLotId=parkingLotId)
        requests.post(url, json=data)
        return redirect(url_for("parkings", filter_type=1))
    
@app.route("/parking-management/parkings/delete/<int:id>", methods=["GET", "POST"])
def deleteParking(id):
    requests.delete(f"{API_BASE}/parkings/{id}")
    return redirect(url_for("parkings", filter_type=1))
    
@app.route("/parking-management/parkings/end/<int:id>")
def endParking(id):
    time = datetime.now().strftime('%H:%M')
    requests.get(f"{API_BASE}/parkings/end/{id}?endTime={time}")
    return redirect(url_for("parkings", filter_type=1))

@app.route("/parking-management/parkings/generate-payment/<int:id>")
def generatePayment(id):
    data = {}
    requests.post(f"{API_BASE}/payments/insert?parkingId={id}", json=data)
    return redirect(url_for("payments", filter_type=1))
    
# ------------------ PAYMENTS ---------------------
@app.route("/parking-management/payments/filter/<int:filter_type>")
def payments(filter_type):
    match filter_type:
        case 1:
            req = requests.get(f"{API_BASE}/payments").json()
        case 2:
            req = requests.get(f"{API_BASE}/payments/paid").json()
        case 3:
            req = requests.get(f"{API_BASE}/payments/pending").json()        
    return render_template("payments.html", payments=req)

@app.route("/parking-management/payments/end/<int:id>")
def endPayment(id):
    requests.get(f"{API_BASE}/payments/end/{id}")
    return redirect(url_for("payments", filter_type=1))

@app.route("/parking-management/payments/delete/<int:id>")
def deletePayment(id):
    requests.delete(f"{API_BASE}/payments/{id}")
    return redirect(url_for("payments", filter_type=1))

if __name__ == "__main__":
    app.run(debug=True, port=5001)