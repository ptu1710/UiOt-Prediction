import time
import requests
import urllib3
import joblib
import numpy as np
import tensorflow as tf

from datetime import datetime
from threading import Thread

USERNAME = "ixxc"
PASSWORD = "sGHNuQVWvIi2Cd53XTrBMA9RmsMTqive"

model = tf.keras.models.load_model("./models/VN_ECA_Attention.h5")
encoder = joblib.load("./models/encoder_vn.joblib")
scaler = joblib.load("./models/scaler_vn.joblib")

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_token():
    session = requests.Session()
    session.auth = (USERNAME, PASSWORD)
    session.verify = False
    session.headers.update({"Content-Type": "application/x-www-form-urlencoded"})

    try:
        response = session.post(
            "https://ixxc.id.vn/auth/realms/master/protocol/openid-connect/token",
            data={"grant_type": "client_credentials", "client_id": "ixxc"},
        )
    except requests.exceptions.RequestException as e:
        print(f"(0) Request failed with error: {e}")
        return None

    if response.status_code == 200:
        token = response.json().get("access_token")
        return token
    else:
        print(f"(0) Request failed with status code: {response.status_code}")
        return None


def get_data(token):
    session = requests.Session()
    session.verify = False
    session.headers.update(
        {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    )
    response = session.get("https://ixxc.id.vn/api/master/asset/6VmbkvsqpS4518ZXnD7aJu")

    if response.status_code == 200:
        data = response.json()
        return parse_data(data, token)
    else:
        print(f"(1) Request failed with status code: {response.status_code}")
        return None


def get_direction(degree):
    directions = [
        ("N", 0, 11.25),
        ("NNE", 11.25, 33.75),
        ("NE", 33.75, 56.25),
        ("ENE", 56.25, 78.75),
        ("E", 78.75, 101.25),
        ("ESE", 101.25, 123.75),
        ("SE", 123.75, 146.25),
        ("SSE", 146.25, 168.75),
        ("S", 168.75, 191.25),
        ("SSW", 191.25, 213.75),
        ("SW", 213.75, 236.25),
        ("WSW", 236.25, 258.75),
        ("W", 258.75, 281.25),
        ("WNW", 281.25, 303.75),
        ("NW", 303.75, 326.25),
        ("NNW", 326.25, 348.75),
        ("N", 348.75, 360),
    ]

    # Find the corresponding direction
    for direction, start, end in directions:
        if start <= degree < end:
            return direction


def parse_data(data, token):
    attributes = data.get("attributes", {})

    month = datetime.now().month
    province = 13

    # Extract and validate each attribute
    max_temp = get_max_temp(token)
    min_temp = get_min_temp(token)
    wind = attributes.get("windSpeed", {}).get("value")
    rain = attributes.get("rainfall", {}).get("value")
    humidity = attributes.get("humidity", {}).get("value")
    pressure = attributes.get("pressure", {}).get("value")

    # Handle None values and ensure they are of the correct type
    max_temp = float(max_temp) if max_temp is not None else 0.0
    min_temp = float(min_temp) if min_temp is not None else 0.0
    wind = float(wind) if wind is not None else 0.0
    rain = float(rain) if rain is not None else 0.0
    humidity = float(humidity) if humidity is not None else 0.0
    pressure = float(pressure) if pressure is not None else 0.0

    wind_direction_value = attributes.get("windDirection", {}).get("value")

    if wind_direction_value is None:
        wind_direction_value = 0
    else:
        wind_direction_value = int(wind_direction_value)

    wind_d = encoder.transform([get_direction(wind_direction_value)])[0]

    # Determine rain_today
    rain_today = 1 if rain >= 1 else 0

    data = np.array(
        [
            [
                month,
                province,
                max_temp,
                min_temp,
                wind,
                wind_d,
                rain,
                humidity,
                pressure,
                rain_today,
            ]
        ]
    )

    print("\n===>>> DATA: " + str(data) + "\n")

    return data


def get_max_temp(token):
    session = requests.Session()
    session.verify = False
    session.headers.update(
        {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    )

    # Get 00:00 this day in milliseconds
    today = datetime.now()
    today = today.replace(hour=0, minute=0, second=0, microsecond=0)
    today = int(today.timestamp() * 1000)

    # Get 23:59 this day in milliseconds
    tomorrow = datetime.now()
    tomorrow = tomorrow.replace(hour=23, minute=59, second=59, microsecond=0)
    tomorrow = int(tomorrow.timestamp() * 1000)

    # Set json body
    body = {
        "fromTimestamp": today,
        "toTimestamp": tomorrow,
        "type": "lttb",
        "amountOfPoints": 10,
    }

    response = session.post(
        "https://ixxc.id.vn/api/master/asset/datapoint/6VmbkvsqpS4518ZXnD7aJu/maxTemperature",
        json=body
    )

    if response.status_code == 200:
        data = response.json()
        value = max([point["y"] for point in data])
        return value
    else:
        print(f"(1) Request failed with status code: {response.status_code}")
        return 0

def get_min_temp(token):
    session = requests.Session()
    session.verify = False
    session.headers.update(
        {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    )

    # Get 00:00 this day in milliseconds
    today = datetime.now()
    today = today.replace(hour=0, minute=0, second=0, microsecond=0)
    today = int(today.timestamp() * 1000)

    # Get 23:59 this day in milliseconds
    tomorrow = datetime.now()
    tomorrow = tomorrow.replace(hour=23, minute=59, second=59, microsecond=0)
    tomorrow = int(tomorrow.timestamp() * 1000)

    # Set json body
    body = {
        "fromTimestamp": today,
        "toTimestamp": tomorrow,
        "type": "lttb",
        "amountOfPoints": 10,
    }

    response = session.post(
        "https://ixxc.id.vn/api/master/asset/datapoint/6VmbkvsqpS4518ZXnD7aJu/minTemperature",
        json=body
    )

    if response.status_code == 200:
        data = response.json()
        value = min([point["y"] for point in data])
        return value
    else:
        print(f"(1) Request failed with status code: {response.status_code}")
        return 0

def put_data(token, data):
    session = requests.Session()
    session.verify = False
    session.headers.update(
        {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    )
    response = session.put(
        "https://ixxc.id.vn/api/master/asset/3bPcjYOCowRm94FK9UNm1i/attribute/rainTomorrow",
        json=data,
    )

    if response.status_code == 200:
        print(f"===>>> PUSH DATA SUCCESSFULLY: {response.json()}")
    else:
        print(f"(2) Request failed with status code: {response.status_code}")


def predict(data):
    input_data = scaler.transform(data)
    prediction = model.predict(input_data)

    return str(prediction[0][0][0] * 100)


def do_prediction():

    token = get_token()
    print("*** Starting prediction with session token: " + token[:10] + "... ***\n")

    if not token:
        print("Failed to get session token, waiting to next prediction...")
        return False

    result = predict(get_data(token))
    print("\n===>>> PREDCITION: " + result + "%\n")

    put_data(token, result)

    print("\n--- TASK COMPLETED, WAITING FOR NEXT PREDICTION ---")
    print("--- *** --- *** --- *** --- *** --- *** --- *** ---\n")

    return True


def main():
    print(
        "\n===>>> STARTING SERVICE AT: "
        + datetime.now().strftime("%Y-%m-%d %H:%M:%S\n")
    )
    do_prediction()
    exit()


if __name__ == "__main__":
    main()
