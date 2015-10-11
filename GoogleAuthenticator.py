from flask import Flask, request, render_template, request, g, redirect, url_for
import sqlite3
import base64
from qrcode import QRCode
import otpauth
from otpauth import OtpAuth
import os
import urllib

# Configuration
DATABASE = 'google_authenticator.db'

# Google Authenticator secret and code depend on label and issuer variables
GALabel = 'label'
GAIssuer = 'DT'



app = Flask(__name__)
app.config.from_object(__name__)

def getQRCodeGoogleUrl(secret_uri):
	# secret_uri needs to be encoded per Google Authenticator
	return 'https://chart.googleapis.com/chart?chs=200x200&chld=M|0&cht=qr&chl=' + urllib.quote(secret_uri)
	return '<a href="https://chart.googleapis.com/chart?chs=200x200&chld=M|0&cht=qr&chl=' + urllib.quote(secret_uri) + '">Click here for QR code.</a>'

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
	
	if request.method == 'POST':

		print 'Username: ', request.form['Username']
		print 'Password: ', request.form['Password']
		print 'Google Auth Code: ', request.form['GoogleAuth']

		# Connect to database and query for user&password
		db = sqlite3.connect('google_authenticator.db')
		cursor = db.cursor()
		cursor.execute('SELECT GOOGLEAUTH FROM USERS WHERE USER=\'' + request.form['Username'] + '\' AND PASSWORD=\'' + request.form['Password'] + '\';')
		secret = cursor.fetchone()
		db.close()
		
		# Query returns None if user&password don't exist
		if secret is None:
			return "Unsuccesful login attempt."

		# Verify google authentication code with secret from database
		else:
			# Generate the otpauth protocal string.
			secret = secret[0]
			print 'Secret: ', secret
			auth = OtpAuth(secret)
			secret_uri = auth.to_uri('totp', GALabel, GAIssuer)	# algorithm type, label, issuer

			# Generate TOTP code given code uri
			code = auth.totp() # Generate time based code
			print 'Code Uri: ', secret_uri
			print 'Valid Google Auth Code: ', code

			# Compare code provided by user with valid code
			if auth.valid_totp(int(request.form['GoogleAuth'])):
				return "Successfully logged in!"
			else:
				print "Invalid Google Authenticator."
				return "Unsuccessful login attempt."
			
		return "Unsuccessful login attempt."
	return "Nothing to see here."


@app.route('/logout')
def logout():
	return redirect(url_for('/'))


@app.route('/register', methods=['GET', 'POST'])
def register():

	if request.method == 'POST':
		print 'Username: ', request.form['Username']
		print 'Password: ', request.form['Password']

		# Connect to database
		db = sqlite3.connect('google_authenticator.db')
		cursor = db.cursor()

		# Create secret and add user to database
		secret = base64.b32encode(os.urandom(10)).decode('utf-8')
		query = 'INSERT INTO USERS (USER, PASSWORD, GOOGLEAUTH) VALUES (\"' + request.form['Username'] + '\",\"' + request.form['Password'] + '\",\"' + secret + '\");'
		cursor.execute(query)
		db.commit()
		db.close()

		# Create unique QR code given secret, label, and issuer
		auth = OtpAuth(secret)
		secret_uri = auth.to_uri('totp', GALabel, GAIssuer)
		qr = QRCode()
		qr.add_data(secret_uri)
		qr.make()
		img = qr.make_image()
		#img.show()	# Opens tmp QR code image
		print 'Secret: ', secret
		print 'Secret Uri: ', secret_uri

		# Display QR code in web browser
		return redirect(getQRCodeGoogleUrl(secret_uri))

	return "Nothing to see here."


if __name__ == '__main__':
	app.debug = True
	app.run()
