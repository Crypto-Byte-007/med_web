from flask import Flask, request, make_response
import sqlite3, os, jwt, requests

app = Flask(__name__)
SECRET = "weaksecret"

# ----------------------------
# helper
# ----------------------------
def flag_popup(flag):
    return f"""
<!DOCTYPE html>
<html>
<body>
<script>
alert({flag!r});
</script>
<h3>✔ Challenge completed</h3>
</body>
</html>
"""

# ----------------------------
# DB
# ----------------------------
def init_db():
    if not os.path.exists("users.db"):
        con = sqlite3.connect("users.db")
        c = con.cursor()
        c.execute("CREATE TABLE users(username text,password text)")
        c.execute("INSERT INTO users VALUES('admin','supersecret')")
        c.execute("INSERT INTO users VALUES('employee','pass123')")
        con.commit()
        con.close()

init_db()

# =====================================================
# HOME
# =====================================================
@app.route("/")
def home():
    return """
<h1>Medium Web CTF Lab</h1>

<ul>
<li><a href="/ch9">9. Employee Portal</a></li>
<li><a href="/ch10">10. Media Upload Center</a></li>
<li><a href="/ch11">11. Partner Dashboard</a></li>
<li><a href="/ch12">12. Network Diagnostic</a></li>
<li><a href="/ch13">13. Feedback Generator</a></li>
<li><a href="/ch14">14. Image Preview Service</a></li>
<li><a href="/ch15">15. Profile Settings</a></li>
</ul>
"""

# =====================================================
# 9. SQLi
# =====================================================
@app.route("/ch9")
def ch9():
    return """
<h2>Employee Portal</h2>
<p><b>Clue:</b> The backend trusts your input too much.</p>
<a href="/employee-login">Go to login</a>
"""

@app.route("/employee-login", methods=["GET","POST"])
def employee_login():
    if request.method == "GET":
        return """
<form method=post>
Username <input name=u><br>
Password <input name=p><br>
<button>Login</button>
</form>
"""

    u = request.form["u"]
    p = request.form["p"]

    con = sqlite3.connect("users.db")
    cur = con.cursor()

    q = f"SELECT * FROM users WHERE username='{u}' AND password='{p}'"
    r = cur.execute(q).fetchone()

    if r:
        return flag_popup("NULLCTF{MED_SQLI}")

    return "Invalid credentials"

# =====================================================
# 10. File upload bypass
# =====================================================
@app.route("/ch10")
def ch10():
    return """
<h2>Media Upload Center</h2>
<p><b>Clue:</b> Validation only checks filename.</p>
<a href="/media-upload">Upload</a>
"""

@app.route("/media-upload", methods=["GET","POST"])
def media_upload():
    if request.method == "GET":
        return """
<form method=post enctype=multipart/form-data>
<input type=file name=file>
<button>Upload</button>
</form>
"""

    f = request.files["file"]
    os.makedirs("uploads", exist_ok=True)
    f.save("uploads/" + f.filename)

    if f.filename.endswith(".py") or f.filename.endswith(".php"):
        return flag_popup("NULLCTF{MED_UPLOAD}")

    return "Uploaded"

# =====================================================
# 11. Weak JWT
# =====================================================
@app.route("/ch11")
def ch11():
    return """
<h2>Partner Dashboard</h2>
<p><b>Clue:</b> Token based authentication.</p>
<a href="/partner-login">Get token</a>
"""

@app.route("/partner-login")
def partner_login():
    token = jwt.encode({"user":"guest"}, SECRET, algorithm="HS256")
    r = make_response("<a href='/partner-dashboard'>Open dashboard</a>")
    r.set_cookie("token", token)
    return r

@app.route("/partner-dashboard")
def partner_dashboard():
    token = request.cookies.get("token")

    data = jwt.decode(token, SECRET, algorithms=["HS256"])

    if data.get("user") == "admin":
        return flag_popup("NULLCTF{MED_JWT}")

    return "Welcome partner"

# =====================================================
# 12. Command Injection
# =====================================================
@app.route("/ch12")
def ch12():
    return """
<h2>Network Diagnostic</h2>
<a href="/diagnostic">Open tool</a>
"""

@app.route("/diagnostic")
def diagnostic():
    host = request.args.get("host")

    if not host:
        return """
<form>
Host: <input name=host>
<button>Check</button>
</form>
"""

    os.system("ping -c 1 " + host)

    if ";" in host or "cat" in host:
        return flag_popup("NULLCTF{MED_CMD}")

    return "Request sent"

# =====================================================
# 13. SSTI
# =====================================================
@app.route("/ch13")
def ch13():
    return """
<h2>Feedback Generator</h2>
<a href="/preview">Open preview</a>
"""

@app.route("/preview")
def preview():
    msg = request.args.get("msg","Thank you!")
    template = f"<h3>Preview</h3><p>{msg}</p>"
    return app.jinja_env.from_string(template).render()

# =====================================================
# 14. SSRF
# =====================================================
@app.route("/ch14")
def ch14():
    return """
<h2>Image Preview Service</h2>
<a href="/preview-image">Open service</a>
"""

@app.route("/preview-image")
def preview_image():
    url = request.args.get("url")

    if not url:
        return """
<form>
Image URL: <input name=url size=40>
<button>Preview</button>
</form>
"""

    if "127.0.0.1" in url or "localhost" in url:
        return flag_popup("NULLCTF{MED_SSRF}")

    r = requests.get(url, timeout=3)
    return r.text[:300]

# =====================================================
# 15. CSRF + missing auth
# =====================================================
email_store = {"email":"user@site.local"}

@app.route("/ch15")
def ch15():
    return """
<h2>Profile Settings</h2>
<a href="/profile">Open profile</a>
"""

@app.route("/profile")
def profile():
    return f"""
Current email: {email_store['email']}
<form method=post action="/update-email">
<input name=email>
<button>Update</button>
</form>
"""

@app.route("/update-email", methods=["POST"])
def update_email():
    email_store["email"] = request.form["email"]

    if email_store["email"] == "admin@company.com":
        return flag_popup("NULLCTF{MED_CSRF}")

    return "Email updated"

# =====================================================
# RUN (Railway / local safe)
# =====================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
