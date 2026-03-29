from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')

# ─── Auth Routes ───────────────────────────────────────────────
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login')
def login():
    return render_template('auth/login.html')

@app.route('/register')
def register():
    return render_template('auth/register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ─── Main Pages ────────────────────────────────────────────────
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard/home.html')

@app.route('/auto-ficha')
def auto_ficha():
    return render_template('sections/auto_ficha.html')

@app.route('/loja')
def loja():
    return render_template('sections/loja.html')

@app.route('/npcs')
def npcs():
    return render_template('sections/npcs.html')

@app.route('/mapas')
def mapas():
    return render_template('sections/mapas.html')

# ─── API Routes ────────────────────────────────────────────────
@app.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.get_json()
    # Firebase auth handled on frontend
    return jsonify({'status': 'ok'})

@app.route('/api/auth/register', methods=['POST'])
def api_register():
    data = request.get_json()
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=True)
