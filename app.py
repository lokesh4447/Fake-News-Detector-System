import numpy as np
import pandas as pd
from flask import Flask, render_template, request, flash, session, jsonify
from pymongo import MongoClient
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import load_model
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret123'


client = MongoClient('mongodb://localhost:27017/')
db = client['my_database']
users_collection = db['users']


OTP_LENGTH = 6

SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USERNAME = 'noreplynewsdetection@gmail.com'
SMTP_PASSWORD = 'scyb ntyo qgmq diwa'
SENDER_EMAIL = 'noreplynewsdetection@gmail.com'

otp_storage = {}



model = load_model('finalmodel.h5')

real_news = pd.read_csv('True.csv')
fake_news = pd.read_csv('Fake.csv')

data = pd.concat([real_news, fake_news], ignore_index=True)

data['content'] = data['title'] + " " + data['text']

tokenizer = Tokenizer(num_words=5000)
tokenizer.fit_on_texts(data['content'])


def validate_user(username, password):
    user = users_collection.find_one(
        {"email": username, "password": password}
    )
    return True if user else False


def generate_otp():
    return ''.join(random.choices(string.digits, k=OTP_LENGTH))


def send_otp_email(email, fullname, otp):

    msg = MIMEMultipart()

    msg['From'] = SENDER_EMAIL
    msg['To'] = email
    msg['Subject'] = "OTP Verification"

    body = f"""
Dear {fullname}

Your OTP is: {otp}
"""

    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(SENDER_EMAIL, email, msg.as_string())


@app.route('/send-otp', methods=['POST'])
def send_otp():

    data = request.json

    email = data.get('email')
    fullname = data.get('fullname')

    otp = generate_otp()

    otp_storage[email] = otp

    send_otp_email(email, fullname, otp)

    return jsonify({'success': True})


@app.route('/verify-otp', methods=['POST'])
def verify_otp():

    data = request.json

    email = data.get('email')
    otp = data.get('otp')

    if email in otp_storage and otp_storage[email] == otp:
        del otp_storage[email]
        return jsonify({'success': True})

    return jsonify({'success': False})


def predict_news(news):

    news_content = news['title'] + " " + news['text']

    sequence = tokenizer.texts_to_sequences([news_content])

    padded_sequence = pad_sequences(sequence, maxlen=200)

    prediction = model.predict(padded_sequence)

    print("Prediction:", prediction[0][0])

    if prediction[0][0] >= 0.5:
        return "Real News"
    else:
        return "Fake News"


@app.route('/')
def home():
    return render_template('landing.html')


@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        data = request.json

        username = data.get('username')
        password = data.get('password')

        if validate_user(username, password):

            session['username'] = username
            session['email'] = username

            return jsonify({'status': 'success'})

        return jsonify({'status': 'error'})

    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():

    if request.method == 'GET':
        return render_template('signup.html')

    if request.method == 'POST':

        data = request.json

        fullname = data.get('fullname')
        email = data.get('email')
        password = data.get('password')

        users_collection.insert_one({
            "fullname": fullname,
            "email": email,
            "password": password
        })

        return jsonify({'status': 'success'})


@app.route('/chat')
def chat():

    if 'username' in session:

        return render_template(
            'chatpage.html',
            username=session['username'],
            email=session['email']
        )

    return render_template('chatpage.html')


@app.route('/update')
def update():

    if 'username' in session:

        return render_template(
            'chatpage.html',
            username=session['username'],
            email=session['email']
        )

    return render_template('update.html')


@app.route('/logout')
def logout():

    session.clear()

    return render_template('landing.html')


@app.route('/predict', methods=['POST'])
def predict():

    data = request.json

    title = data.get('mytitle')
    text = data.get('mydes')

    if not title or not text:
        return jsonify({'status': 'error'})

    news_data = {
        "title": title,
        "text": text
    }

    result = predict_news(news_data)

    return jsonify({
        "status": "success",
        "result": result
    })


if __name__ == '__main__':
    app.run(debug=True)