import sqlite3
from flask import Flask, render_template

CAS = Flask(__name__)


@CAS.route('/')
def home_page():
    return render_template("HomePage.html")

@CAS.route('/AboutPage')
def about_page():
    return render_template("AboutPage.html")

@CAS.route('/ContactPage')
def contact_page():
    return render_template("ContactPage.html")

if __name__ == '__main__':
    CAS.debug = True
    CAS.run()
