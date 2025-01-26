from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os

app = Flask(__name__)

# Konfigurasi
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'database.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'

# Inisialisasi database dan modul tambahan
db = SQLAlchemy(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # 'admin' atau 'user'
    email = db.Column(db.String(150))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))

class Pesanan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100))
    email = db.Column(db.String(100))
    tanggal = db.Column(db.String(100))
    jumlah = db.Column(db.Integer)
    produk = db.Column(db.String(100))
    harga = db.Column(db.Float)
    total_harga = db.Column(db.Float)
    pesan = db.Column(db.String(200))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
@login_required
def home():
    if current_user.role == "admin":
        message = "Selamat datang di Dashboard Admin!"
    else:
        message = "Selamat datang di Halaman Pembeli!"
    return render_template("index.html", message=message)

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/product")
def product():
    return render_template("product-list.html")

@app.route("/product_detail")
def product_detail():
    return render_template("product-detail.html")

@app.route("/cart")
def cart():
    return render_template("cart.html")

@app.route("/checkout")
def checkout():
    return render_template("checkout.html")

@app.route("/wishlist")
def wishlist():
    return render_template("wishlist.html")

@app.route("/my_account")
@login_required
def my_account():
    return render_template("my-account.html", user=current_user)

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
        
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        user = User.query.filter_by(username=username).first()
        
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash("Login berhasil!", "success")
            next_page = request.args.get("next")
            return redirect(next_page) if next_page else redirect(url_for("home"))
        else:
            flash("Login gagal! Periksa username dan password.", "danger")
            
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        phone = request.form.get("phone")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        
        # Validasi input
        if User.query.filter_by(username=username).first():
            flash("Username sudah digunakan!", "danger")
            return redirect(url_for("register"))
            
        if password != confirm_password:
            flash("Password tidak cocok!", "danger") 
            return redirect(url_for("register"))
            
        # Buat user baru
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        new_user = User(
            username=username,
            email=email,
            phone=phone, 
            password=hashed_password,
            role="user"
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash("Registrasi berhasil! Silakan login.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            db.session.rollback()
            flash("Terjadi kesalahan saat mendaftar. Silakan coba lagi.", "danger")
            
    return render_template("login.html")

@app.route("/update_account", methods=["POST"])
@login_required
def update_account():
    if request.method == "POST":
        current_user.username = request.form.get("username")
        current_user.email = request.form.get("email")
        current_user.phone = request.form.get("phone")
        current_user.address = request.form.get("address")
        
        db.session.commit()
        flash("Profil berhasil diperbarui!", "success")
        
    return redirect(url_for("my_account"))

@app.route("/change_password", methods=["POST"]) 
@login_required
def change_password():
    if request.method == "POST":
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")
        
        if not bcrypt.check_password_hash(current_user.password, current_password):
            flash("Password saat ini salah!", "danger")
            return redirect(url_for("my_account"))
            
        if new_password != confirm_password:
            flash("Password baru tidak cocok!", "danger")
            return redirect(url_for("my_account"))
            
        hashed_password = bcrypt.generate_password_hash(new_password).decode("utf-8")
        current_user.password = hashed_password
        db.session.commit()
        
        flash("Password berhasil diubah!", "success")
        
    return redirect(url_for("my_account"))

@app.route("/admin")
@login_required
def admin_dashboard():
    if current_user.role != "admin":
        return redirect(url_for("home"))
    return render_template("admin_dashboard.html")

@app.route("/user")
@login_required
def user_dashboard():
    if current_user.role != "user":
        return redirect(url_for("home"))
    return render_template("user_dashboard.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/reservation", methods=["GET", "POST"])
def reservation():
    if request.method == "POST":
        nama = request.form["nama"]
        email = request.form["email"]
        tanggal = request.form["tanggal"]
        jumlah = int(request.form["jumlah"])
        produk = request.form["produk"]
        harga = float(request.form["harga"])
        total_harga = float(request.form["Totalharga"])
        pesan = request.form.get("pesan", "")

        pesanan_baru = Pesanan(
            nama=nama,
            email=email,
            tanggal=tanggal,
            jumlah=jumlah,
            produk=produk,
            harga=harga,
            total_harga=total_harga,
            pesan=pesan,
        )
        db.session.add(pesanan_baru)
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("reservation.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

@app.route("/terms")
def terms():
    return render_template("terms.html")

@app.route("/payment_policy")
def payment_policy():
    return render_template("payment-policy.html")

@app.route("/shipping_policy") 
def shipping_policy():
    return render_template("shipping-policy.html")

@app.route("/return_policy")
def return_policy():
    return render_template("return-policy.html")

@app.route("/product_list")
def product_list():
    # Logika untuk daftar produk terbaru
    return render_template("product-list.html")

if __name__ == "__main__":
    with app.app_context():
        try:
            db.create_all()
            # Tambahkan admin jika belum ada
            if not User.query.filter_by(username="admin").first():
                hashed_password = bcrypt.generate_password_hash("admin123").decode("utf-8")
                admin_user = User(username="admin", password=hashed_password, role="admin")
                db.session.add(admin_user)
                db.session.commit()
        except Exception as e:
            print(f"Error initializing database: {e}")
    
    app.run(debug=True)