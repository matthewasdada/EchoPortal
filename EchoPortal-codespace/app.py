import os
from flask import Flask, request, render_template, request, redirect, url_for

app = Flask(__name__)
app.secret_key = "secretkey"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == "admin" and password == "1234":
            return redirect(url_for("home"))
        else:
            return "Invalid login"
        
    return render_template("login.html")

if __name__ == "__main__":
    app.run(debug=True)