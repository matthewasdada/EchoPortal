import os
from flask import Flask, request, render_template, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "secretkey_echoportal_mrbrooks"

UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "1234":
            session["user"] = username
            session["role"] = "admin"
            return redirect(url_for("dashboard"))
        else:  
            return render_template("login.html", error="Invalid username or password")
        
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user" in session:
        return render_template("dashboard.html", user=session["user"])
    else:
        return redirect(url_for("login"))

@app.route("/gallery")
def gallery():
    if "user" in session:
        files = os.listdir(app.config["UPLOAD_FOLDER"])

        images = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpe g'))]

        return render_template("gallery.html", images=images)
    else:
        return redirect(url_for("login"))
    
@app.route("/upload", methods=["GET", "POST"])
def upload():
    if "user" not in session:
        return redirect(url_for("login"))
    
    message = None

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



@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))



if __name__ == "__main__":
    app.run(debug=True)