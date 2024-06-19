from flask import Flask, render_template, jsonify
import requests
import json

app = Flask(__name__)

# Replace with your Genesys Cloud credentials
client_id = 'Enter Ouath Client ID'
client_secret = 'Enter Ouaht client secret'
region = 'mypurecloud.com.au'  # Correct region for Sydney, Australia
queue_ids = ['QUEUEID One', 'QUEUEID Two','QUEUEID Three','QUEUEID Four','QUEUEID Five']  # Your queue IDs

def get_access_token():
    url = f'https://login.{region}/oauth/token'
    data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret
    }
    response = requests.post(url, data=data)
    response.raise_for_status()  # Raise an error for bad status codes
    return response.json().get('access_token')

def get_all_queues(access_token):
    url = f'https://api.{region}/api/v2/routing/queues'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    all_queues = []
    page_number = 1
    while True:
        params = {'pageSize': 100, 'pageNumber': page_number}
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # Raise an error for bad status codes
        data = response.json()
        all_queues.extend(data['entities'])
        if not data.get('nextUri'):
            break
        page_number += 1
    return all_queues

def get_queue_stats(access_token):
    url = f'https://api.{region}/api/v2/analytics/queues/observations/query'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    data = {
        "filter": {
            "type": "or",
            "predicates": [{"dimension": "queueId", "value": queue_id} for queue_id in queue_ids]
        },
        "metrics": ["oWaiting", "oInteracting", "oOnQueueUsers"]
    }
    print(json.dumps(data, indent=2))  # Print the request body for debugging
    response = requests.post(url, headers=headers, json=data)
    print(response.content)  # Print the response content for debugging
    response.raise_for_status()  # Raise an error for bad status codes
    return response.json()

@app.route('/')
def index():
    try:
        access_token = get_access_token()
        queue_stats = get_queue_stats(access_token)
        queues = get_all_queues(access_token)
        # Map queue ID to queue name
        queue_map = {queue['id']: queue['name'] for queue in queues}
        for result in queue_stats['results']:
            result['queueName'] = queue_map.get(result['group']['queueId'], 'Unknown')
        return render_template('index.html', stats=queue_stats)
    except Exception as e:
        return str(e)

@app.route('/api/stats')
def api_stats():
    try:
        access_token = get_access_token()
        queue_stats = get_queue_stats(access_token)
        queues = get_all_queues(access_token)
        # Map queue ID to queue name
        queue_map = {queue['id']: queue['name'] for queue in queues}
        for result in queue_stats['results']:
            result['queueName'] = queue_map.get(result['group']['queueId'], 'Unknown')
        return jsonify(queue_stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
