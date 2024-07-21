import pymysql
from linebot import LineBotApi
from linebot.models import FlexSendMessage
from datetime import datetime, timedelta
import time  

db_host = "YOURIP"
db_port = 3306
db_user = "root"
db_password = "facelockerprojectpassword1234@
db_name = "flask_db"
line_channel_access_token = "kylJ79z/+H//BQ23BS6rQ6Va92J5O8k2ywYi97Wq5+d+mVALe+oAawI/gpTAspBI7GmdtTlbSts45wOxcAnefmJgoNvSoBk0TshynspV/RPhgLhESXEEIthFRVwXZAnNHa15foM/pbEiA8Vmh17bxQdB04t89/1O/w1cDnyilFU="
line_user_id = "Ua23af0b4456d7f9e268a23c50e0e5df0"  

check_interval = 20

while True:
    try:
        print("Checking for updates...")
        
        connection = pymysql.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name,
        )

        cursor = connection.cursor()
        cursor.execute("SELECT MAX(created_at) FROM relay_status")
        result = cursor.fetchone()

        if result and result[0] is not None:
            latest_created_at = result[0]
            
            current_time = datetime.now()

            
            time_difference = current_time - latest_created_at

            
            if time_difference.total_seconds() < 60:
                print("Sending Locker Open Alert...")
                
                flex_message = {
                    "type": "flex",
                    "altText": "Flex Message",
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
                                    "text": "Your door locker is still open. Please check!",
                                    "wrap": True
                                }
                            ]
                        }
                    }
                }

                line_bot_api = LineBotApi(line_channel_access_token)
                line_bot_api.push_message(line_user_id, FlexSendMessage(alt_text="Locker Open Alert", contents=flex_message["contents"]))
                print("Locker Open Alert sent!")
        cursor.close()
        connection.close()
        print("Waiting for the next check...")

    except Exception as e:
        print(f"An error occurred: {str(e)}")
    time.sleep(check_interval)
