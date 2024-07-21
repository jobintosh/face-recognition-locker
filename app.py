import base64
import uuid
from flask import Flask, render_template, request, session, redirect, url_for, Response, jsonify, flash
import mysql.connector
import cv2
from PIL import Image
import numpy as np
import os
import time
from datetime import date
import logging
import hashlib
import smtplib
from email.mime.text import MIMEText
import random
import string
import cv2
from datetime import datetime,timedelta
import stripe


stripe.api_key = 'sk_test_51NutLPBGGzOWH6WKvYHArctigy1hgkbnJKYslyXf4qDpm6gsbD1H7vA3YFVisTrkJIpve1DiV9yruIZ5QZ8dc4KS00dh18YMQB'
YOUR_DOMAIN = 'https://locker.jobintosh.me/'


logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

handler = logging.FileHandler('error.log')
handler.setLevel(logging.ERROR)

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)

app = Flask(__name__)
app.secret_key = 'jobintosh'

application = app

cnt = 0
pause_cnt = 0
justscanned = False

MYSQL_HOST = os.getenv('MYSQL_HOST', 'face-db')

def connect_to_database():
    while True:
        try:
            mydb = mysql.connector.connect(
                host="face-db",
                user="root",
                passwd="facelockerprojectpassword1234@#",
                database="face_recognition"
            )
            print("Connected to the database successfully!")
            return mydb
        except mysql.connector.Error as err:
            print(f"Failed to connect to the database: {err}")
            print("Retrying in 5 seconds...")
            time.sleep(5) 

mydb = connect_to_database()
mycursor = mydb.cursor()

current_directory = os.getcwd()
print("Current working directory:", current_directory)

CASCADE_CLASSIF_PATH = "resources/haarcascade_frontalface_default.xml"

FACE_CLASSIF_PATH = "classifier.xml"

IMAGE_TRAIN_COUNT = 100


class RecognizeResult:
    label: str
    confidence: float
    image: any


class SaveResult(RecognizeResult):
    save_path: str
    x: int
    y: int
    h: int
    w: int

# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Generate dataset >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

face_classifier = cv2.CascadeClassifier(CASCADE_CLASSIF_PATH)


# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Train Classifier >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def find_face(img_path):
    face_cascade = cv2.CascadeClassifier(CASCADE_CLASSIF_PATH)

    img = cv2.imread(img_path)
    if img is None:
        return []

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_classifier.detectMultiScale(
        gray,
        # scaleFactor=(1.05),
        minNeighbors=(3),
        minSize=(30, 30),
        # maxSize=(100, 100)
    )
    return faces


def face_cropped(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_classifier.detectMultiScale(
        gray
        # scaleFactor=(1.05),
        # minNeighbors=(1),
        # minSize=(30, 30),
        # maxSize=(100, 100)
    )

    if len(faces) < 1:
        return None
    elif len(faces) == 1:
        (x, y, w, h) = faces[0]
        cropped_face = img[y:y + h, x:x + w]
        return cropped_face
    else:
        cropped_faces = [img[y:y + h, x:x + w] for (x, y, w, h) in faces]
        return cropped_faces

@app.route('/train_classifier/<nbr>')
def train_classifier(nbr):
    dataset_dir = "/dataset"

    path = [os.path.join(dataset_dir, f) for f in os.listdir(dataset_dir)]
    faces = []
    ids = []

    for image in path:
        img = Image.open(image).convert('L')
        imageNp = np.array(img, 'uint8')
        id = int(os.path.split(image)[1].split(".")[1])

        faces.append(imageNp)
        ids.append(id)
    ids = np.array(ids)

    clf = cv2.face.LBPHFaceRecognizer_create()
    clf.train(faces, ids)
    clf.write("classifier.xml")

    return redirect('/')



def save_image_base64(image_base64, folder_path):
    unique_filename = str(uuid.uuid4()) + ".jpeg"
    image_path = os.path.join(folder_path, unique_filename)

    with open(image_path, "wb") as img_file:
        img_data = base64.b64decode(image_base64)
        img_file.write(img_data)

    return unique_filename


def label_img(img, label, confidence, x, y, w, h):
    cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)

    label_text = f"{label} ({confidence:.2f})"
    cv2.putText(
        img,
        label_text,
        (x, y - 10),
        cv2.FONT_HERSHEY_SIMPLEX, 0.5,
        (0, 255, 0),
        2,
    )


def recognize_face_from_img_path(img_path):
    img = cv2.imread(img_path)
    faces = find_face(img_path)

    if len(faces) == 0:
        print("No faces detected in the image.")
        return None

    output_image_path = 'people.jpeg'
    recognizer = cv2.face_LBPHFaceRecognizer.create()
    recognizer.read("classifier.xml")
    recognized_faces = []

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    for (x, y, w, h) in faces:
        face_roi = gray[y:y+h, x:x+w]
        label, confidence = recognizer.predict(face_roi)

        recognized_faces.append({
            'bbox': (x, y, w, h),
            'label': label,  
            'confidence': confidence 
        })

    for face in recognized_faces:
        x, y, w, h = face['bbox']
        label = face['label']
        confidence = face['confidence']

        if label == -1:
            label = "UNKNOWN"

        print(f"Face: {label}, Confidence: {confidence}")
        label_img(img, label, confidence, x, y, w, h)

    cv2.imwrite(output_image_path, img)
    print(f"Image with recognized faces saved as {output_image_path}")

    result = RecognizeResult()
    result.label = recognized_faces[0]['label']
    result.confidence = recognized_faces[0]['confidence']

    _, image_data = cv2.imencode('.jpg', img)
    result.image = image_data

    return result


def generate_dataset_v2(person_id, img_path):
    faces = find_face(img_path)

    if len(faces) == 0:
        return None

    (x, y, w, h) = faces[0]

    img = cv2.imread(img_path)

    # Crop the detected face from the image
    face_cropped_img = img[y:y+h, x:x+w]

    if face_cropped_img is None:
        return None

    face = cv2.resize(face_cropped_img, (200, 200))
    face = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)

    face_cropped_dir = os.path.join("facecrop", str(person_id))
    os.makedirs(face_cropped_dir, exist_ok=True)

    filename = os.path.basename(img_path)

    save_path = os.path.join(face_cropped_dir, filename)
    cv2.imwrite(save_path, face)

    result = SaveResult()
    result.image = face
    result.label = person_id
    result.save_path = save_path
    result.x = x
    result.y = y
    result.h = h
    result.w = w

    return result
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Train Classifier >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< ROUTEING >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
from datetime import datetime

@app.route('/')
def home():
    if 'user_id' in session:
        mycursor.execute(
            "SELECT personnel_id, full_name, locker_no, active, added FROM personnel_data")
        data = mycursor.fetchall()
        username = session['username']
        
        formatted_data = []
        for row in data:
            row = list(row)
            row[4] = row[4].strftime('%d/%m/%Y')
            formatted_data.append(row)

        return render_template('index.html', data=formatted_data, username=username)
    else:
        return redirect(url_for('login'))

    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_or_email = request.form['username_or_email']
        password = request.form['password']
        

        cursor = mydb.cursor()
        cursor.execute("SELECT id, username, email, password_hash FROM users WHERE username=%s OR email=%s",
                       (username_or_email, username_or_email))
        user = cursor.fetchone()

        if user:
            user_id, db_username, db_email, db_password_hash = user

            input_password_hash = hashlib.sha256(password.encode()).hexdigest()
            if input_password_hash == db_password_hash:
                session['user_id'] = user_id
                session['username'] = db_username
                flash('Login successful!', 'success')
                return redirect(url_for('home'))
            else:
                flash('Incorrect password. Please try again.', 'error')
        else:
            flash('Login failed. Please check your credentials.', 'error')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        email = request.form['email']
        phonenumber = request.form['phonenumber']
        password_confirm = request.form['password_confirm']

        if password != password_confirm:
            flash('Passwords do not match. Please try again.', 'error')
        else:
            cursor = mydb.cursor()
            cursor.execute(
                "SELECT id FROM users WHERE username=%s", (username,))
            existing_user = cursor.fetchone()

            if existing_user:
                flash(
                    'Username already in use. Please choose a different username.', 'error')
            else:
                password_hash = hashlib.sha256(password.encode()).hexdigest()

                cursor.execute("INSERT INTO users (username, password_hash, firstname, lastname, email, phonenumber) VALUES (%s, %s, %s, %s, %s, %s)",
                               (username, password_hash, firstname, lastname, email, phonenumber))
                mydb.commit()

                flash('Registration successful. You can now log in.', 'success')
                return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']

        cursor = mydb.cursor()
        cursor.execute(
            "SELECT id, username FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()

        if user:
            temp_password = ''.join(random.choices(
                string.ascii_letters + string.digits, k=12))
            hashed_temp_password = hashlib.sha256(
                temp_password.encode()).hexdigest()

            cursor.execute(
                "UPDATE users SET password_hash=%s WHERE id=%s", (hashed_temp_password, user[0]))
            mydb.commit()

            send_password_reset_email(email, temp_password)

            flash(
                'An email with instructions to reset your password has been sent.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Email address not found. Please try again.', 'error')

    return render_template('forgot_password.html')


def send_password_reset_email(email, temp_password):
    msg = MIMEText(f'Your temporary password is: {temp_password}')
    msg['Subject'] = 'Password Reset'
    msg['From'] = 'YOUREMAIL'
    msg['To'] = email

    try:
        smtp_server = smtplib.SMTP('smtp.gmail.com', 587)
        smtp_server.starttls()
        smtp_server.login('YOUREMAIL', 'YOURPASSWORD')
        smtp_server.sendmail('YOUREMAIL',
                             [email], msg.as_string())
        smtp_server.quit()
    except Exception as e:
        print(f'Error sending email: {str(e)}')


@app.route('/index')
def index():
    if 'user_id' in session:
        db_connection = get_database_connection()
        if db_connection:
            mycursor = db_connection.cursor()
            mycursor.execute(
                "select personnel_id, full_name, locker_no, active, added from personnel_data")
            data = mycursor.fetchall()
            username = session['username']
            return render_template('index.html', data=data, username=username)
        else:
            return 'Database connection lost. Please try again later.'
    else:
        return 'You are not logged in. <a href="/login">Login</a>'

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    if request.method == 'GET' or request.method == 'POST':
        session.pop('user_id', None)
        flash('Logout successful.', 'success')
        return redirect(url_for('login'))
    else:
        return 'Method Not Allowed', 405
    

@app.route('/addprsn')
def addprsn():
    if 'user_id' in session:
        mycursor.execute("select ifnull(max(personnel_id) + 1, 101) from personnel_data")
        row = mycursor.fetchone()
        nbr = row[0]

        mycursor.execute("SELECT DISTINCT locker_no FROM personnel_data")
        existing_lockers = [row[0] for row in mycursor.fetchall()]

        all_lockers = [
            "LOCKER-01", "LOCKER-02", "LOCKER-03", "LOCKER-04", "LOCKER-05",
            "LOCKER-06", "LOCKER-07", "LOCKER-08", "LOCKER-09", "LOCKER-10"
        ]

        available_lockers = [locker for locker in all_lockers if locker not in existing_lockers]

        return render_template('addprsn.html', newnbr=int(nbr), available_lockers=available_lockers)
    else:
        return 'You are not logged in. <a href="/login">Login</a>'


@app.route('/addprsn_submit', methods=['POST'])
def addprsn_submit():
    prsnbr = request.form.get('txtnbr')
    prsname = request.form.get('txtname')
    prsskill = request.form.get('optskill')

    mycursor.execute("""INSERT INTO `personnel_data` (`personnel_id`, `full_name`, `locker_no`) VALUES
                    ('{}', '{}', '{}')""".format(prsnbr, prsname, prsskill))
    mydb.commit()

    return redirect(url_for('vfdataset_page', prs=prsnbr))


@app.route('/vfdataset_page/<prs>')
def vfdataset_page(prs):
    return render_template('gendataset.html', prs=prs)


@app.route('/video_feed')
def video_feed():
    return Response(face_recognition(), mimetype='multipart/x-mixed-replace; boundary=frame')


def has_active_subscription(user_id):
    cur = mydb.cursor()
    cur.execute("SELECT COUNT(*) FROM subscriptions WHERE user_id = %s AND end_date >= CURDATE()", (user_id,))
    count = cur.fetchone()[0]
    return count > 0

@app.route('/fr_page')
def fr_page():
    if 'user_id' in session:
        user_id = session['user_id']

        if has_active_subscription(user_id):
            mycursor.execute("SELECT a.accs_id, a.accs_prsn, b.full_name, b.locker_no, a.accs_added "
                             "FROM activity_log a "
                             "LEFT JOIN personnel_data b ON a.accs_prsn = b.personnel_id "
                             "WHERE a.accs_date = CURDATE() "
                             "ORDER BY a.accs_id DESC")
            data = mycursor.fetchall()
            print("Data from fr_page:")
            for row in data:
                print(row)

            return render_template('fr_page.html', data=data)
        else:
            return render_template('access_denied.html')
    else:
        return 'You are not logged in. <a href="/login">Login</a>'


@app.route('/countTodayScan')
def countTodayScan():
    try:
        mydb = connect_to_database()
        mycursor = mydb.cursor()

        mycursor.execute("select count(*) "
                         "from activity_log "
                         "where accs_date = curdate()")
        row = mycursor.fetchone()
        rowcount = row[0]
        # print("Row count from countTodayScan:", rowcount)
        return jsonify({'rowcount': rowcount})
    except Exception as e:
        logger.error(f"Error in countTodayScan: {str(e)}")
        return jsonify({'error': 'An error occurred'}), 500

@app.route('/loadData', methods=['GET', 'POST'])
def loadData():
    try:
        mydb = connect_to_database()
        mycursor = mydb.cursor()

        mycursor.execute("select a.accs_id, a.accs_prsn, b.full_name, b.locker_no, date_format(a.accs_added, '%H:%i:%s') "
                         "from activity_log a "
                         "left join personnel_data b on a.accs_prsn = b.personnel_id "
                         "where a.accs_date = curdate() "
                         "order by 1 desc")
        data = mycursor.fetchall()
        # print("Data from loadData:", data)
        return jsonify(response=data)
    except Exception as e:
        logger.error(f"Error in loadData: {str(e)}")
        return jsonify({'error': 'An error occurred'}), 500

    
@app.route('/edit/<int:person_id>', methods=['GET', 'POST'])
def edit(person_id):
    if 'user_id' in session:
        if request.method == 'POST':
            new_name = request.form['name']
            new_skill = request.form['locker']

            cur = mydb.cursor()
            cur.execute("UPDATE personnel_data SET full_name=%s, locker_no=%s WHERE personnel_id=%s",
                        (new_name, new_skill, person_id))
            mydb.commit()

            flash('Personnel data updated successfully!', 'success')
            return redirect(url_for('home'))

        cur = mydb.cursor()
        cur.execute(
            "SELECT full_name, locker_no FROM personnel_data WHERE personnel_id=%s", (person_id,))
        data = cur.fetchone()

        subscription_status = check_subscription_status(session.get('user_id'))

        return render_template('edit.html', data=data, person_id=person_id, subscription_status=subscription_status)
    else:
        return redirect(url_for('login'))

@app.route('/delete/<int:person_id>', methods=['GET', 'POST'])
def delete_person(person_id):
    if 'user_id' in session:
        if request.method == 'POST':
            cursor = mydb.cursor()
            cursor.execute(
                "DELETE FROM personnel_data WHERE personnel_id = %s", (person_id,))
            mydb.commit()
            cursor.close()

            flash('Personnel record deleted successfully!', 'success')
            return redirect(url_for('home'))

        return render_template('delete_confirmation.html', person_id=person_id)
    else:
        return redirect(url_for('login'))

@app.route('/upload/<int:person_id>', methods=['POST'])
def upload_image(person_id):
    try:
        data = request.json
        if 'image' in data:
            image_data_base64 = data['image']

            upload_dir_path = os.path.join("dataset", str(person_id))
            os.makedirs(upload_dir_path, exist_ok=True)

            facecrop_dir = os.path.join("facecrop", str(person_id))
            os.makedirs(facecrop_dir, exist_ok=True)

            image_count = len([f for f in os.listdir(facecrop_dir)])

            if image_count >= IMAGE_TRAIN_COUNT:

                return jsonify({"status": "done"})
            else:           
                filename = save_image_base64(
                    image_data_base64,
                    upload_dir_path
                )

                file_full_path = os.path.join(upload_dir_path, filename)

                save_result = generate_dataset_v2(person_id, file_full_path)
                if save_result is None:
                    return jsonify({"message": "face not found", "filename": filename}), 200

                imgread = cv2.imread(file_full_path)
                label_img(imgread, "detect", 1, save_result.x,
                          save_result.y, save_result.w, save_result.h)
                imgencode = cv2.imencode('.jpg', imgread)[1].tobytes()
                base64_image = base64.b64encode(imgencode).decode()

                return jsonify({
                    "message": "image saved successfully",
                    "filename": filename,
                    "image_count": image_count,
                    "image64": base64_image
                }), 200
        else:
            return jsonify({"error": "No image field in request"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/train/<person_id>')
def train_face(person_id):
    person_id = int(person_id)
    print(f"train start for person id: {person_id}")

    face_dir = os.path.join("facecrop", str(person_id))
    print(f"face train dir: {face_dir}")

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    is_old_classif_exists = os.path.exists("classifier.xml")
    if is_old_classif_exists is True:
        recognizer.read("classifier.xml")
        
    faces = []
    ids = []
    i = 0
    for image_path in os.listdir(face_dir):
        try:
            image_path = os.path.join(face_dir, image_path)

            img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            flattened_img = np.array(img, 'uint8')
            
            faces.append(flattened_img)
            ids.append(person_id)
        except Exception as e:
            print(f"cannot use image: {image_path}")
            print(e)
            print("")
        finally:
            i += 1
    faces = np.array(faces)
    ids = np.array(ids)
    print("cv2 train start:")
    if is_old_classif_exists is True:
        recognizer.update(faces, ids)
    else:
        recognizer.train(faces, ids)
        recognizer.write("classifier.xml")

    print(f"trained person id: {person_id}")
    return redirect('/')

@app.route('/recognize', methods=['POST'])
def recognize_v2():
    try:
        data = request.json
        if 'image' in data:
            image_data = data['image']
            folder_path = os.path.join("recognize")

            os.makedirs(folder_path, exist_ok=True)

            filename = save_image_base64(image_data, folder_path)

            image_full_path = os.path.join(folder_path, filename)

            result: RecognizeResult = recognize_face_from_img_path(
                image_full_path)

            if result is None:
                return jsonify({"message": "result not found"}), 400
            recognized_label = "UNKNOWN"

            print(f"confidence level: {result.confidence}")
            if result.confidence <= 20:
                recognized_label = "UNKNOWN"
                return jsonify({"message": "low confidence"}), 400
            recognized_label = result.label
            sql = "INSERT INTO activity_log (accs_date, accs_prsn, accs_added) VALUES (%s, %s, %s)"
            val = (datetime.today(), recognized_label, datetime.now())
            mycursor.execute(sql, val)
            mydb.commit()
            base64_image = base64.b64encode(result.image).decode()

            return jsonify({"message": "done", "label": recognized_label, "image64": base64_image})
        else:
            return jsonify({"error": "No image"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/edit_profile/<int:user_id>', methods=['GET', 'POST'])
def edit_profile(user_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if session['user_id'] != user_id:
        return "Unauthorized access"
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = mycursor.fetchone()

    if request.method == 'POST':
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        email = request.form['email']
        phonenumber = request.form['phonenumber']
        new_password = request.form['new_password']

        if new_password:
            hashed_password = hashlib.sha256(new_password.encode()).hexdigest()
            mycursor.execute("UPDATE users SET firstname = %s, lastname = %s, email = %s, phonenumber = %s, password_hash = %s WHERE id = %s",
                             (firstname, lastname, email, phonenumber, hashed_password, user_id))
        else:
            mycursor.execute("UPDATE users SET firstname = %s, lastname = %s, email = %s, phonenumber = %s WHERE id = %s",
                             (firstname, lastname, email, phonenumber, user_id))

        mydb.commit()
        mycursor.close()
        return redirect(url_for('index'))

    mycursor.close()
    return render_template('profile.html', user=user)


@app.route('/success', methods=['GET', 'POST'])
def success():
    user_id = session.get('user_id')

    if user_id is not None:
        try:
            mycursor.execute("SELECT firstname, lastname FROM users WHERE id = %s", (user_id,))
            user_data = mycursor.fetchone()

            if user_data:
                firstname, lastname = user_data
                subscription_name = f"{firstname} {lastname}"
                start_date = datetime.now().strftime('%Y-%m-%d')
                end_date = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
                mycursor.execute("INSERT INTO subscriptions (user_id, subscription_name, start_date, end_date) VALUES (%s, %s, %s, %s)",
                                (user_id, subscription_name, start_date, end_date))
                mydb.commit()

                return render_template('success.html')
            else:
                return "User not found."

        except Exception as e:
            return "An error occurred while inserting data: " + str(e)

    else:
        return redirect(url_for('login'))

@app.route('/cancel')
def cancel():
    return render_template('cancel.html')

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    'price': 'price_1NutemBGGzOWH6WKIywdDoNf',
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url=YOUR_DOMAIN + '/success',
            cancel_url=YOUR_DOMAIN + '/cancel',
        )
    except Exception as e:
        return str(e)

    return redirect(checkout_session.url, code=303)

@app.route('/webhook', methods=['POST'])
def webhook():
    event = None
    payload = request.data

    try:
        event = json.loads(payload)
    except:
        print('⚠️  Webhook error while parsing basic request.' + str(e))
        return jsonify(success=False)
    if endpoint_secret:
        sig_header = request.headers.get('stripe-signature')
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except stripe.error.SignatureVerificationError as e:
            print('⚠️  Webhook signature verification failed.' + str(e))
            return jsonify(success=False)

    if event and event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']  
        print('Payment for {} succeeded'.format(payment_intent['amount']))

    elif event['type'] == 'payment_method.attached':
        payment_method = event['data']['object'] 
    else:
        print('Unhandled event type {}'.format(event['type']))

    return jsonify(success=True)
    
@app.route('/logs')
def logs():
    if 'user_id' in session:
        mycursor.execute("select a.accs_id, a.accs_prsn, b.full_name, b.locker_no, a.accs_added "
                         "  from activity_log a "
                         "  left join personnel_data b on a.accs_prsn = b.personnel_id "
                         " order by 1 desc")
        data = mycursor.fetchall()
        print("Data from logs:", data)
        return render_template('logs.html', data=data)
    else:
        return 'You are not logged in. <a href="/login">Login</a>'


@app.route('/check', methods=['GET'])
def check():
    try:
        mydb = connect_to_database()
        mycursor = mydb.cursor()
        query = """
            SELECT p.locker_no
            FROM personnel_data p
            INNER JOIN activity_log a ON p.personnel_id = a.accs_prsn
            WHERE TIMESTAMPDIFF(SECOND, a.accs_added, NOW()) <= 8
            AND a.accs_id = (SELECT MAX(accs_id) FROM activity_log)
        """

        mycursor.execute(query)
        result = mycursor.fetchone()
        if result:
            response = {
                'status': 'True',
                'locker_no': result[0]
            }
        else:
            response = {
                'status': 'False'
            }

        return jsonify(response)

    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/subscription')
def check_subscription():
    user_id = session.get('user_id')

    if user_id is not None:
        query = "SELECT start_date, end_date FROM subscriptions WHERE user_id = %s"
        mycursor.execute(query, (user_id,))
        subscription = mycursor.fetchone()
        mycursor.fetchall()

        if subscription:
            start_date = subscription[0]  
            end_date = subscription[1]
            today = datetime.now().date()

            if start_date <= today <= end_date:
                days_left = (end_date - today).days

                return render_template('subscription.html', days_left=days_left)
            else:
                return "Subscription is not active."
        else:
            return "Subscription data not found"
    else:
        return "User not logged in"


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)