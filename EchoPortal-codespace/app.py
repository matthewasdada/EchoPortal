import os
import io
import zipfile

from flask import Flask, request, render_template, redirect, url_for, session, send_from_directory, send_file
from datetime import datetime, timedelta
from flask import g

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
                "time": datetime.now(),
                "active": True
            })


            return redirect(url_for("home"))
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

@app.route("/admin/users")
def admin_users():
    if session.get("role") != "admin":
        return "Access denied", 403

    active_users = {}
    last_login = {}

    for entry in recent_login:
        username = entry["username"]
        last_login[username] = entry["time"]
        active_users[username] = (datetime.now() - entry["time"] < timedelta(minutes=5))

    return render_template(
        "user_management.html",
        users=users,
        active_users=active_users,
        last_login=last_login
    )

@app.route("/admin/gallery")
def admin_gallery():
    if session.get("role") != "admin":
        return "Access denied", 403

    gallery_base = os.path.join(app.root_path, "static", "images", "gallery")
    folders = [
        f for f in os.listdir(gallery_base)
        if os.path.isdir(os.path.join(gallery_base, f))
    ]

    return render_template("admin_gallery.html", folders=folders)

@app.route("/admin/create-gallery", methods=["POST"])
def create_gallery():
    if session.get("role") != "admin":
        return "Access denied", 403

    new_folder = request.form.get("new_folder").strip().lower()
    new_folder = new_folder.replace(" ", "-")

    gallery_path = os.path.join(app.root_path, "static", "images", "gallery", new_folder)
    os.makedirs(gallery_path, exist_ok=True)

    return redirect("/admin/gallery")

@app.route("/admin/delete-gallery/<folder>", methods=["POST"])
def delete_gallery(folder):
    if session.get("role") != "admin":
        return "Access denied", 403

    gallery_path = os.path.join(app.root_path, "static", "images", "gallery", folder)

    if not os.path.exists(gallery_path):
        return "Folder not found", 404

    import shutil
    shutil.rmtree(gallery_path)

    return redirect("/admin/gallery")



@app.route("/admin/promote/<username>")
def promote_user(username):
    if session.get("role") != "admin":
        return "Access denied", 403

    if username in users:
        users[username]["role"] = "admin"

    return redirect("/admin/users")


@app.route("/admin/demote/<username>")
def demote_user(username):
    if session.get("role") != "admin":
        return "Access denied", 403

    if username in users:
        users[username]["role"] = "user"

    return redirect("/admin/users")

@app.before_request
def update_activity():
    if "user" in session:
        for entry in recent_login:
            if entry["username"] == session["user"]:
                entry["time"] = datetime.now()
                entry["active"] = True




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

    gallery_base = os.path.join(app.root_path, "static", "images", "gallery")
    folders = [f for f in os.listdir(gallery_base) 
            if os.path.isdir(os.path.join(gallery_base, f))
    ]

    if request.method == "POST":
        file = request.files.get("file")
        gallery_folder = request.form.get("gallery_folder")
        new_folder = request.form.get("new_gallery_folder", "").strip()

        if not file or file.filename == "":
            message = "No file was selected"
            return render_template("upload.html", message=message, folders=folders)

        if not allowed_file(file.filename):
            message = "Invalid file type (only the following: .jpg, .jpeg, .png)"
            return render_template("upload.html", message=message, folders=folders)

        if new_folder:
            new_folder = new_folder.replace(" ", "-").lower()
            gallery_folder = new_folder

        if not gallery_folder:
            message = "Please choose a gallery section or create a new one."
            return render_template("upload.html", message=message, folders=folders)
            
        save_path = os.path.join(app.root_path, "static", "images", "gallery", gallery_folder, file.filename)

        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        file.save(save_path)
        message = f"Upload was successful! Saved to '{gallery_folder}'."

    return render_template("upload.html", message=message, folders=folders)

def get_recent_logins():
    cutoff = datetime.now() - timedelta(hours=1)
    return [entry for entry in recent_login if entry["time"] > cutoff]


@app.route("/admin")
def admin_dashboard():
    if "user" not in session:
        return redirect("/login")

    upload_path = os.path.join("static", "uploads")
    total_uploads = len(os.listdir(upload_path)) if os.path.exists(upload_path) else 0

    try:
        recent_login_count = len(get_recent_logins()) 
    except:
        recent_login_count = 0

    return render_template(
        "admin_dashboard.html",
        total_uploads=total_uploads,
        recent_login_count=recent_login_count
    )


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
    session.clear()
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
    gallery_base = os.path.join(app.root_path, "static", "images", "gallery")
    folders = [f for f in os.listdir(gallery_base)
            if os.path.isdir(os.path.join(gallery_base, f))
    ]
    return render_template("gallery.html", folders=folders)


@app.route("/gallery/<event_name>")
def gallery_event(event_name):
    base_path = os.path.join(app.root_path, "static", "images", "gallery", event_name)

    if not os.path.exists(base_path):
        return "Event not found", 404

    images = [
        f for f in os.listdir(base_path)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ]

    return render_template("gallery_event.html",
                           event_name=event_name,
                           images=images)

@app.route("/download-selected", methods=["POST"])
def download_selected():
    if "user" not in session:
        return redirect("/login")

    selected = request.form.getlist("selected_images")

    if not selected:
        return "No images selected."
    
    event_name = selected[0].split("/")[0]

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for img_path in selected:
            full_path = os.path.join(app.root_path, "static", "images", "gallery", img_path)
            zip_file.write(full_path, arcname=os.path.basename(full_path))

    zip_buffer.seek(0)

    pretty_name = event_name.replace("-", " ").title()

    return send_file(zip_buffer, mimetype="application/zip", as_attachment=True, download_name=f"{pretty_name} Folder.zip")

                
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)