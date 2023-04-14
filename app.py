from flask import Flask, jsonify, request
import json
import requests
from datetime import datetime, timedelta
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["1000 per day", "50 per hour"]
)

train_data=[]

@app.route('/',methods=["GET"])
def hello():
  return jsonify({'Hello': 'world!'})


@app.route('/trains',methods=["GET"])
@limiter.limit("10 per minute")
def get_trains():
  global train_data

  if not train_data:
    access_token=get_auth()
    headers={'Authorization': access_token['token_type']+' '+access_token['access_token']}
    railway_resp=requests.get('http://localhost:3000/trains',headers=headers)
    train_data = railway_resp.json()

  filtered_trains = []
  for train in train_data:
    delay_time=timedelta(minutes=train['delayedBy'])
    departure_time = datetime.now().replace(hour=train['departureTime']['Hours'],minute=train['departureTime']['Minutes'],second=train['departureTime']['Seconds'])
    if departure_time + delay_time > datetime.now() + timedelta(minutes=30):
      filtered_trains.append(train)
  filtered_trains.sort(key=lambda x: (x['price']['AC'],-x['seatsAvailable']['AC'], -int(datetime.now().replace(hour=x['departureTime']['Hours']),minute=x['departureTime']['Minutes'],second=x['departureTime']['Seconds']) + timedelta(minutes=x['delayedBy'])),reverse=True)

  response_data = []
  for train in filtered_trains:
    response_data.append({
      'trainName': train['trainName'],
      'trainNumber': train['trainNumber'],
      'priceAC': train['price']['AC'],
      'priceSleeper': train['price']['sleeper'],
      'seatsAvailableAC': train['seatsAvailable']['AC'],
      'seatsAvailableSleeper': train['seatsAvailable']['sleeper'],
      'departureTime': train['departureTime'],
      'delayedBy': train['delayedBy']
    })
  return jsonify(response_data)

def get_auth():
  company_key={
    "companyName": "something",
    "clientID": "d0d68eb0-ccc4-4e3d-9a75-6ce35183893a",
    "clientSecret": "afyBclEaQEiGBYXq"
  }
  response=requests.post('http://localhost:3000/auth',json=company_key)
  return response.json()


if __name__=="__main__":
  app.run(host='0.0.0.0',port=8080)