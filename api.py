from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

import os
DB_NAME = "/tmp/parking.db" if os.environ.get('VERCEL_URL') else "parking.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS cars (id INTEGER PRIMARY KEY AUTOINCREMENT, licensePlate TEXT, brand TEXT, model TEXT, color TEXT, inParking BOOLEAN DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS parking_lots (id INTEGER PRIMARY KEY AUTOINCREMENT, tag TEXT, occupied BOOLEAN DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS parkings (id INTEGER PRIMARY KEY AUTOINCREMENT, carId INTEGER, parkingLotId INTEGER, startTime TEXT, endTime TEXT, rate REAL, duration REAL, total REAL, date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY AUTOINCREMENT, parkingId INTEGER, paid BOOLEAN DEFAULT 0)''')
    conn.commit()
    conn.close()

init_db()

# --- Dashboard ---
@app.route('/dashboard/total-cars')
def total_cars():
    return str(get_db().execute("SELECT count(*) FROM cars").fetchone()[0])

@app.route('/dashboard/total-active-parkings')
def total_active_parkings():
    return str(get_db().execute("SELECT count(*) FROM parkings WHERE endTime IS NULL").fetchone()[0])

@app.route('/dashboard/total-parking-lots')
def total_parking_lots():
    return str(get_db().execute("SELECT count(*) FROM parking_lots").fetchone()[0])

@app.route('/dashboard/total-unoccupied-parking-lots')
def total_unoccupied_parking_lots():
    return str(get_db().execute("SELECT count(*) FROM parking_lots WHERE occupied = 0").fetchone()[0])

@app.route('/dashboard/total-paid-payments-value-today')
def total_paid_payments():
    today = datetime.now().strftime('%Y-%m-%d')
    res = get_db().execute("SELECT sum(total) FROM parkings JOIN payments ON parkings.id = payments.parkingId WHERE payments.paid = 1 AND parkings.date = ?", (today,)).fetchone()[0]
    return str(round(res, 2) if res else 0)

@app.route('/dashboard/total-pending-payments')
def total_pending():
    return str(get_db().execute("SELECT count(*) FROM payments WHERE paid = 0").fetchone()[0])

@app.route('/dashboard/total-parkings-today')
def total_parkings_today():
    today = datetime.now().strftime('%Y-%m-%d')
    return str(get_db().execute("SELECT count(*) FROM parkings WHERE date = ?", (today,)).fetchone()[0])

# --- Parking Lots ---
@app.route('/parkingLots', methods=['GET', 'POST'])
def parking_lots():
    if request.method == 'GET':
        lots = get_db().execute("SELECT * FROM parking_lots").fetchall()
        return jsonify([dict(l) for l in lots])
    elif request.method == 'POST':
        data = request.json
        conn = get_db()
        conn.execute("INSERT INTO parking_lots (tag, occupied) VALUES (?, 0)", (data.get('tag'),))
        conn.commit()
        return jsonify({"status": "success"})

@app.route('/parkingLots/unoccupied')
def unoccupied_lots():
    lots = get_db().execute("SELECT * FROM parking_lots WHERE occupied = 0").fetchall()
    return jsonify([dict(l) for l in lots])

@app.route('/parkingLots/occupied')
def occupied_lots():
    lots = get_db().execute("SELECT * FROM parking_lots WHERE occupied = 1").fetchall()
    return jsonify([dict(l) for l in lots])

@app.route('/parkingLots/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def parking_lot(id):
    conn = get_db()
    if request.method == 'GET':
        lot = conn.execute("SELECT * FROM parking_lots WHERE id = ?", (id,)).fetchone()
        return jsonify(dict(lot) if lot else {})
    elif request.method == 'PUT':
        data = request.json
        conn.execute("UPDATE parking_lots SET tag = ? WHERE id = ?", (data.get('tag'), id))
        conn.commit()
        return jsonify({"status": "success"})
    elif request.method == 'DELETE':
        conn.execute("DELETE FROM parking_lots WHERE id = ?", (id,))
        conn.commit()
        return jsonify({"status": "success"})

# --- Cars ---
@app.route('/cars', methods=['GET', 'POST'])
def cars():
    if request.method == 'GET':
        cars = get_db().execute("SELECT * FROM cars").fetchall()
        return jsonify([dict(c) for c in cars])
    elif request.method == 'POST':
        data = request.json
        conn = get_db()
        conn.execute("INSERT INTO cars (licensePlate, brand, model, color) VALUES (?, ?, ?, ?)", 
                     (data.get('licensePlate'), data.get('brand'), data.get('model'), data.get('color')))
        conn.commit()
        return jsonify({"status": "success"})

@app.route('/cars/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def car(id):
    conn = get_db()
    if request.method == 'GET':
        car = conn.execute("SELECT * FROM cars WHERE id = ?", (id,)).fetchone()
        return jsonify(dict(car) if car else {})
    elif request.method == 'PUT':
        data = request.json
        conn.execute("UPDATE cars SET licensePlate = ?, brand = ?, model = ?, color = ? WHERE id = ?", 
                     (data.get('licensePlate'), data.get('brand'), data.get('model'), data.get('color'), id))
        conn.commit()
        return jsonify({"status": "success"})
    elif request.method == 'DELETE':
        conn.execute("DELETE FROM cars WHERE id = ?", (id,))
        conn.commit()
        return jsonify({"status": "success"})

@app.route('/cars/inParkingFalse')
def cars_in_parking_false():
    cars = get_db().execute("SELECT * FROM cars WHERE inParking = 0").fetchall()
    return jsonify([dict(c) for c in cars])

def format_parkings(rows):
    conn = get_db()
    result = []
    for r in rows:
        p = dict(r)
        # Fetch car
        car = conn.execute("SELECT * FROM cars WHERE id = ?", (p['carId'],)).fetchone()
        p['car'] = dict(car) if car else {"licensePlate": "Unknown"}
        # Fetch lot
        lot = conn.execute("SELECT * FROM parking_lots WHERE id = ?", (p['parkingLotId'],)).fetchone()
        p['parkingLot'] = dict(lot) if lot else {"tag": "Unknown"}
        # Fetch payment
        payment = conn.execute("SELECT * FROM payments WHERE parkingId = ?", (p['id'],)).fetchone()
        p['paymentGenerated'] = True if payment else False
        p['ended'] = True if p['endTime'] else False
        result.append(p)
    return result

# --- Parkings ---
@app.route('/parkings', methods=['GET'])
def parkings():
    parkings = get_db().execute("SELECT * FROM parkings").fetchall()
    return jsonify(format_parkings(parkings))

@app.route('/parkings/going', methods=['GET'])
def parkings_going():
    carId = request.args.get('carId')
    query = "SELECT * FROM parkings WHERE endTime IS NULL"
    params = ()
    if carId:
        query += " AND carId = ?"
        params = (carId,)
    parkings = get_db().execute(query, params).fetchall()
    return jsonify(format_parkings(parkings))

@app.route('/parkings/ended', methods=['GET'])
def parkings_ended():
    carId = request.args.get('carId')
    query = "SELECT * FROM parkings WHERE endTime IS NOT NULL"
    params = ()
    if carId:
        query += " AND carId = ?"
        params = (carId,)
    parkings = get_db().execute(query, params).fetchall()
    return jsonify(format_parkings(parkings))

@app.route('/parkings/search', methods=['GET'])
def parkings_search():
    carId = request.args.get('carId')
    parkings = get_db().execute("SELECT * FROM parkings WHERE carId = ?", (carId,)).fetchall()
    return jsonify(format_parkings(parkings))

@app.route('/parkings/insert', methods=['POST'])
def parkings_insert():
    carId = request.args.get('carId')
    parkingLotId = request.args.get('parkingLotId')
    data = request.json
    today = datetime.now().strftime('%Y-%m-%d')
    conn = get_db()
    conn.execute("INSERT INTO parkings (carId, parkingLotId, startTime, rate, date) VALUES (?, ?, ?, ?, ?)", 
                 (carId, parkingLotId, data.get('startTime'), data.get('rate'), today))
    conn.execute("UPDATE cars SET inParking = 1 WHERE id = ?", (carId,))
    conn.execute("UPDATE parking_lots SET occupied = 1 WHERE id = ?", (parkingLotId,))
    conn.commit()
    return jsonify({"status": "success"})

@app.route('/parkings/<int:id>', methods=['DELETE'])
def delete_parking(id):
    conn = get_db()
    conn.execute("DELETE FROM parkings WHERE id = ?", (id,))
    conn.commit()
    return jsonify({"status": "success"})

@app.route('/parkings/end/<int:id>', methods=['GET'])
def end_parking(id):
    endTime = request.args.get('endTime')
    conn = get_db()
    # Find parking
    parking = conn.execute("SELECT * FROM parkings WHERE id = ?", (id,)).fetchone()
    if parking:
        # Calculate simple total for mock
        try:
            start_dt = datetime.strptime(parking['startTime'], '%H:%M')
            end_dt = datetime.strptime(endTime, '%H:%M')
            duration = round((end_dt - start_dt).total_seconds() / 3600, 2)
            if duration < 0:
                duration += 24 # Handle crossing midnight
            total = round(duration * parking['rate'], 2)
        except:
            duration = 1
            total = parking['rate']
            
        conn.execute("UPDATE parkings SET endTime = ?, duration = ?, total = ? WHERE id = ?", (endTime, duration, total, id))
        conn.execute("UPDATE cars SET inParking = 0 WHERE id = ?", (parking['carId'],))
        conn.execute("UPDATE parking_lots SET occupied = 0 WHERE id = ?", (parking['parkingLotId'],))
        conn.commit()
    return jsonify({"status": "success"})

# --- Payments ---
def format_payments(rows):
    conn = get_db()
    result = []
    for r in rows:
        pay = dict(r)
        parking = conn.execute("SELECT * FROM parkings WHERE id = ?", (pay['parkingId'],)).fetchone()
        if parking:
            p_dict = dict(parking)
            car = conn.execute("SELECT * FROM cars WHERE id = ?", (p_dict['carId'],)).fetchone()
            p_dict['car'] = dict(car) if car else {"licensePlate": "Unknown"}
            pay['parking'] = p_dict
            pay['date'] = p_dict['date']
            pay['total'] = p_dict['total']
        else:
            pay['parking'] = {"car": {"licensePlate": "Unknown"}}
            pay['date'] = "Unknown"
            pay['total'] = 0
        result.append(pay)
    return result

@app.route('/payments', methods=['GET'])
def payments_list():
    payments = get_db().execute("SELECT * FROM payments").fetchall()
    return jsonify(format_payments(payments))

@app.route('/payments/paid', methods=['GET'])
def payments_paid():
    payments = get_db().execute("SELECT * FROM payments WHERE paid = 1").fetchall()
    return jsonify(format_payments(payments))

@app.route('/payments/pending', methods=['GET'])
def payments_pending():
    payments = get_db().execute("SELECT * FROM payments WHERE paid = 0").fetchall()
    return jsonify(format_payments(payments))

@app.route('/payments/insert', methods=['POST'])
def payments_insert():
    parkingId = request.args.get('parkingId')
    conn = get_db()
    conn.execute("INSERT INTO payments (parkingId, paid) VALUES (?, 0)", (parkingId,))
    conn.commit()
    return jsonify({"status": "success"})

@app.route('/payments/end/<int:id>', methods=['GET'])
def payments_end(id):
    conn = get_db()
    conn.execute("UPDATE payments SET paid = 1 WHERE id = ?", (id,))
    conn.commit()
    return jsonify({"status": "success"})

@app.route('/payments/<int:id>', methods=['DELETE'])
def delete_payment(id):
    conn = get_db()
    conn.execute("DELETE FROM payments WHERE id = ?", (id,))
    conn.commit()
    return jsonify({"status": "success"})

from werkzeug.middleware.dispatcher import DispatcherMiddleware
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    '/api': app.wsgi_app
})

if __name__ == '__main__':
    app.run(port=8080)
