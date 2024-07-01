import os
import re
import requests
from flask import Flask, request, jsonify

os.environ['LINE_ACCESS_TOKEN'] = 'dzUf1jjhFzz0Kw1E1+JEEkHyEhwlj5xV/0yANUaePva4Q3j3yCulbuvlopsDewOMu1F7XvnC+vMcqLVTFKVeNY0LwK3FEKj+q0nbjCQ/FPM2k9Shg+cxkNjr1Bkw6xpKBemIXx2p3H7rlMo7IDgeEAdB04t89/1O/w1cDnyilFU='
os.environ['GOOGLE_MAPS_API_KEY'] = 'AIzaSyCLHqOCUkTxCGxNiEnIVsUeDIRQgpZplFQ'

app = Flask(__name__)

# 獲取環境變量中的API密鑰和Token
LINE_ACCESS_TOKEN = os.getenv('LINE_ACCESS_TOKEN')
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

# LINE Messaging API
LINE_API_URL = 'https://api.line.me/v2/bot/message/reply'

# Google Maps API
GOOGLE_MAPS_DIRECTIONS_URL = 'https://maps.googleapis.com/maps/api/directions/json'

def extract_addresses(text):
    # 提取地址的正則表達式，假設地址格式為 "從 [出發地地址] 到 [目的地地址]"
    match = re.match(r'從 (.+) 到 (.+)', text)
    if match:
        return match.group(1), match.group(2)
    return None, None

def get_travel_time(origin, destination):
    params = {
        'origin': origin,
        'destination': destination,
        'key': GOOGLE_MAPS_API_KEY
    }
    response = requests.get(GOOGLE_MAPS_DIRECTIONS_URL, params=params)
    data = response.json()
    if data['status'] == 'OK':
        duration = data['routes'][0]['legs'][0]['duration']['text']
        return duration
    print('Error with Google Maps API response:', data)
    return None

def reply_to_line(reply_token, message):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LINE_ACCESS_TOKEN}'
    }
    data = {
        'replyToken': reply_token,
        'messages': [{'type': 'text', 'text': message}]
    }
    response = requests.post(LINE_API_URL, headers=headers, json=data)
    print('LINE API response:', response.json())

@app.route('/webhook', methods=['POST'])
def webhook():
    body = request.get_json()
    print('Received request:', body)  # 调试信息
    if isinstance(body, dict) and 'events' in body:
        for event in body['events']:
            print('Event:', event)  # 调试信息
            if isinstance(event, dict) and 'type' in event and 'message' in event:
                if event['type'] == 'message' and event['message']['type'] == 'text':
                    text = event['message']['text']
                    reply_token = event['replyToken']
                    print('Processing message:', text)

                    origin, destination = extract_addresses(text)
                    if origin and destination:
                        travel_time = get_travel_time(origin, destination)
                        if travel_time:
                            reply_message = f'從 {origin} 到 {destination} 的預計行程時間是 {travel_time}。'
                        else:
                            reply_message = '抱歉，我無法計算行程時間。'
                    else:
                        reply_message = '抱歉，我無法從你的訊息中提取地址。請使用 "從 [出發地地址] 到 [目的地地址]" 的格式。'

                    reply_to_line(reply_token, reply_message)
                else:
                    print('Message type is not text')
            else:
                print('Invalid event structure')
    else:
        print('Invalid body structure')
    
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(port=5000, debug=True)  # 开启调试模式