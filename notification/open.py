import requests
import time
import json

access_token = 'kylJ79z/+H//BQ23BS6rQ6Va92J5O8k2ywYi97Wq5+d+mVALe+oAawI/gpTAspBI7GmdtTlbSts45wOxcAnefmJgoNvSoBk0TshynspV/RPhgLhESXEEIthFRVwXZAnNHa15foM/pbEiA8Vmh17bxQdB04t89/1O/w1cDnyilFU='
line_url = 'https://api.line.me/v2/bot/message/push'
recipient_id = 'Ua23af0b4456d7f9e268a23c50e0e5df0'
server_url = 'http://locker.jobintosh.me/loadData'
fetch_interval = 10  
previous_data = None

try:
    while True:
        
        response = requests.get(server_url)
        if response.status_code == 200:
            server_data = response.json()

            if 'response' in server_data and isinstance(server_data['response'], list) and server_data['response']:
                scan_data = server_data['response'][0]  

                if len(scan_data) >= 5:
                    
                    if server_data != previous_data:
                        previous_data = server_data
                        flex_message = {
                            "type": "flex",
                            "altText": "your locker open!",
                            "contents": {
                                "type": "bubble",
                                "hero": {
                                    "type": "image",
                                    "url": "https://cdn-icons-png.flaticon.com/512/6360/6360268.png",
                                    "size": "full",
                                    "aspectRatio": "20:13"
                                },
                                "body": {
                                    "type": "box",
                                    "layout": "vertical",
                                    "contents": [
                                        {
                                            "type": "text",
                                            "text": "⚠️ Locker Open ⚠️",
                                            "weight": "bold",
                                            "size": "xl"
                                        },
                                        {
                                            "type": "text",
                                            "text": f"🧑🏻‍💻: {scan_data[2]}",
                                            "wrap": True
                                        },
                                        {
                                            "type": "text",
                                            "text": f"🧳: {scan_data[3]}",
                                            "wrap": True
                                        },
                                        {
                                            "type": "text",
                                            "text": f"⏱️: {scan_data[4]}",
                                            "wrap": True
                                        }
                                    ]
                                }
                            }
                        }

                        message_data = {
                            "to": recipient_id,
                            "messages": [flex_message]
                        }

                        headers = {
                            "Content-Type": "application/json",
                            "Authorization": "Bearer " + access_token
                        }

                        line_response = requests.post(line_url, json=message_data, headers=headers)

                        
                        if line_response.status_code == 200:
                            print("Flex Message sent successfully.")
                        else:
                            print("Error sending Flex Message:", line_response.status_code)
                    else:
                        print("No new data. Skipping message send.")
                else:
                    print("Not enough elements in scan_data.")
            else:
                print("Invalid or empty 'response' in JSON data from the server.")
        else:
            print(f"Error fetching data from server. Status code: {response.status_code}")
        time.sleep(fetch_interval)
except KeyboardInterrupt:
    print("Program stopped by user.")
except Exception as e:
    print("An error occurred:", str(e))
