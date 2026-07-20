import os
from flask import Flask, request, render_template, redirect, url_for, session, send_from_directory

from datetime import datetime, timedelta

recent_login = []


users = {
    "admin": {
        "password": "1234",
        "role": "admin"
    }
}

app = Flask(__name__)
app.secret_key = "secretkey_echoportal_mrbrooks"

UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/home")
def home():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in users and users[username]["password"] == password:
            session["user"] = username
            session["role"] = users[username]["role"]

            recent_login.append({
                "username": username,
                "time": datetime.now()
            })

            return redirect(url_for("dashboard"))
        else:  
            return render_template("login.html", error="Invalid username or password")
        
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in users:
            return render_template("signup.html", error="Username already exists.")
        
        users[username] = {
            "password": password,
            "role": "user"
        }

        return redirect(url_for("login"))
    
    return render_template("signup.html")

@app.route("/dashboard")
def dashboard():
    if "user" in session:
        return render_template("dashboard.html", user=session["user"])
    else:
        return redirect(url_for("login"))

@app.route("/download/<filename>")
def download(filename):
    if "user" not in session:
        return redirect(url_for("login"))
    
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)
    
@app.route("/upload", methods=["GET", "POST"])
def upload():
    if "user" not in session:
        return redirect(url_for("login"))
    
    message = None

    if session.get("role") != "admin":
        return "Access denied: Admins only", 403

    if request.method == "POST":
        if "file" not in request.files:
            message = "No file part"
        else:
            file = request.files["file"]

            if file.filename == "":
                message = "No file was selected"

            elif not allowed_file(file.filename):
                message = "Invalid file type (only the following: .jpg, .jpeg, .png)"
                
            else:
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
                file.save(filepath)
                message = "Upload was successful!"

    return render_template("upload.html", message=message)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/services")
def services():
    return render_template("services.html")

@app.route("/faq")
def faq():
    return render_template("faq.html")

@app.route("/testimonials")
def testimonials():
    return render_template("testimonials.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/services/sunday")
def services_sunday():
    return render_template("sunday.html")

@app.route("/services/conferences")
def services_conferences():
    return render_template("conferences.html")

@app.route("/services/youth")
def services_youth():
    return render_template("youth.html")

@app.route("/services/baptisms")
def services_baptisms():
    return render_template("baptisms.html")

@app.route("/services/community")
def services_events():
    return render_template("events.html")

@app.route("/intro")
def intro():
    return render_template("intro.html")

@app.route("/")
def index():
    return redirect("/intro")

@app.route("/admin/recent-logins")
def admin_recent_logins():
    if "role" not in session or session["role"] != "admin":
        return "Access denied", 403

    cutoff = datetime.now() - timedelta(hours=1)
    active_logins = [entry for entry in recent_login if entry["time"] > cutoff]

    return render_template("admin_recent.html", logins=active_logins)

@app.route("/gallery")
def gallery():
    return render_template("gallery.html")

@app.route("/gallery/<event_name>")
def gallery_event(event_name):
    base_path = os.path.join("static", "images", "gallery", event_name)

    if not os.path.exists(base_path):
        return "Event not found", 404

    images = [
        f for f in os.listdir(base_path)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ]

    return render_template("gallery_event.html",
                           event_name=event_name,
                           images=images)




@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)