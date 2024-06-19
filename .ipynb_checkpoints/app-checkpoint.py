import io
from flask import Flask, request, render_template, redirect, url_for, jsonify, send_file
import sqlite3
import os
from werkzeug.utils import secure_filename
from models.query_model import process_query, process_file

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            process_file(file_path)
            return redirect(url_for('index'))
    return render_template('upload.html')
    
@app.route('/query', methods=['POST'])
def query():
    user_query = request.form.get('query')
    result = process_query(user_query)
    return jsonify(result)

def query_db(query, args=(), one=False):
    conn = sqlite3.connect('weather.db')
    c = conn.cursor()
    c.execute(query,args)
    rv = c.fetchall()
    conn.close()
    return (rv[0] if rv else None) if one else rv

@app.route('/histogram', methods=['GET'])
def histogram():
    data_point = request.args.get('data_point')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not data_point or not start_date or not end_date:
        return jsonify({"error": "Please provide data_point, start_date, and end_date"}), 400

    query = f"SELECT {data_point} FROM weather WHERE date BETWEEN ? AND ?"
    data = query_db(query, [start_date, end_date])
    data_values = [row[0] for row in data if row[0] is not None]

    plt.figure(figsize=(10, 6))
    plt.hist(data_values, bins=10, edgecolor='black')
    plt.title(f'Histogram of {data_point}')
    plt.xlabel(data_point)
    plt.ylabel('Frequency')
    
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()
    
    return send_file(img, mimetype='image/png')



@app.route('/api/weather', methods=['GET'])
def get_weather_data():
    data_point = request.args.get('data_point')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if not data_point or not start_date or not end_date:
        return jsonify({"error": "Please provide the data_point, start_date, and end_date"}), 400

    query = f"SELECT date, {data_point} FROM weather WHERE date BETWEEN ? AND ?"
    results = query_db(query, [start_date, end_date])

    return jsonify(results)

@app.route('/api/weather', methods=['POST'])
def add_weather_data():
    data = request.json
    query = '''
        INSERT OR REPLACE INTO weather (date, weather_code, temperature_max, temperature_min, precipitation_sum, wind_speed_max, precipitation_probability_max)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    '''
    args = [
        data.get('date'),
        data.get('weather_code'),
        data.get('temperature_max'),
        data.get('temperature_min'),
        data.get('precipitation_sum'),
        data.get('wind_speed_max'),
        data.get('precipitation_probability_max')
    ]
    
    conn = sqlite3.connect('weather.db')
    c = conn.cursor()
    c.execute(query,args)
    conn.commit()
    conn.close()
    return jsonify({"message": "Data added successfully"}), 201

@app.route('/api/weather', methods=['PUT'])
def update_weather_data():
    data = request.json
    date = data.get('date')
    data_point = data.get('data_point')
    value = data.get('value')
    
    if not date or not data_point or not value:
        return jsonify({"error": "Please provide date, data_point, and value"}), 400

    query = f"UPDATE weather SET {data_point} = ? WHERE date = ?"
    conn = sqlite3.connect('weather.db')
    c = conn.cursor()
    c.execute(query, [value, date])
    conn.commit()
    conn.close()
    return jsonify({"message": "Data updated successfully"}), 200

@app.route('/api/weather', methods=['DELETE'])
def delete_weather_data():
    date = request.json.get('date')
    
    if not date:
        return jsonify({"error": "Please provide date"}), 400

    query = "DELETE FROM weather WHERE date = ?"
    conn = sqlite3.connect('weather.db')
    c = conn.cursor()
    c.execute(query, [date])
    conn.commit()
    conn.close()
    return jsonify({"message": "Data deleted successfully"}), 200



if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
