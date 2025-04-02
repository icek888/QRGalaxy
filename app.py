from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session, jsonify
from flask_dance.contrib.google import make_google_blueprint, google
from werkzeug.utils import secure_filename
from models import Session, QRCodeEntry, User
from qrcodegen_canvas import generate_qr_with_canvas
from PIL import Image
import os
import uuid

app = Flask(__name__)
app.secret_key = 'hotloads-super-secret-key'
UPLOAD_FOLDER = 'static/qr_codes'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

QR_STYLES = {
    "square": {},
    "dots": {"module_type": "dots"},
    "rounded": {"module_type": "rounded"},
    "classy": {"module_type": "classy"},
    "classy-rounded": {"module_type": "classy-rounded"},
    "extra-rounded": {"module_type": "extra-rounded"},
}

google_bp = make_google_blueprint(
    client_id=os.getenv("CLIENT_ID"),
    client_secret=os.getenv("CLIENT_SECRET"),
    scope=["profile", "email"],
    redirect_url="/login/google/authorized"
)
app.register_blueprint(google_bp, url_prefix="/login")

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form.get('url')
        style = request.form.get('style', 'square')
        fill_color = request.form.get('fill_color', '#000000')
        back_color = request.form.get('back_color', '#ffffff')
        eye_frame_color = request.form.get('eye_frame_color', fill_color)
        eye_ball_color = request.form.get('eye_ball_color', fill_color)
        logo_file = request.files.get('logo')

        filename = f"{uuid.uuid4().hex}.png"
        filepath = os.path.join(UPLOAD_FOLDER, filename)

        generate_qr_with_canvas(
            url=url,
            path=filepath,
            style=style,
            fill_color=fill_color,
            back_color=back_color,
            eye_frame_color=eye_frame_color,
            eye_ball_color=eye_ball_color,
            logo_file=logo_file
        )

        db = Session()
        user_id = session.get("user_id")
        qr_entry = QRCodeEntry(url=url, filename=filename, user_id=user_id)
        db.add(qr_entry)
        db.commit()
        qr_id = qr_entry.id
        db.close()

        return redirect(url_for('result', qr_id=qr_id))

    return render_template('index.html', styles=QR_STYLES)

@app.route('/result/<int:qr_id>')
def result(qr_id):
    db = Session()
    qr = db.query(QRCodeEntry).get(qr_id)
    db.close()
    if not qr:
        return "QR-код не найден", 404
    return render_template('result.html', filename=qr.filename, qr_id=qr.id)

@app.route('/qr/<int:qr_id>')
def qr_redirect(qr_id):
    db = Session()
    qr = db.query(QRCodeEntry).get(qr_id)
    db.close()
    if not qr:
        return "QR-код не найден", 404
    return redirect(url_for('result', qr_id=qr.id))

@app.route('/profile')
def profile():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    db = Session()
    user = db.query(User).get(user_id)

    qr_codes = []
    if user:
        qr_codes = db.query(QRCodeEntry).filter_by(user_id=user.id).order_by(QRCodeEntry.created_at.desc()).all()
    db.close()

    if not user:
        return "Пользователь не найден", 404

    return render_template('profile.html', user=user, qr_codes=qr_codes)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        db = Session()
        existing_user = db.query(User).filter_by(email=email).first()
        if existing_user:
            db.close()
            return "Такой пользователь уже существует. <a href='/login'>Войти?</a>"

        user = User(username=username, email=email, password=password)
        db.add(user)
        db.commit()

        session["logged_in"] = True
        session["user_id"] = user.id
        session["user_email"] = user.email
        session["user_name"] = user.username
        db.close()

        return redirect(url_for("profile"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        session['logged_in'] = True
        session['user_email'] = email
        session['user_name'] = email.split("@")[0].capitalize()
        return redirect(url_for("profile"))
    return render_template("login.html")

@app.route("/login/google/authorized")
def google_authorized():
    if not google.authorized:
        return redirect(url_for("google.login"))
    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        return "Ошибка авторизации через Google"
    user_info = resp.json()
    session['logged_in'] = True
    session['user_email'] = user_info['email']
    session['user_name'] = user_info.get('name', 'Пользователь')
    return redirect(url_for("profile"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
