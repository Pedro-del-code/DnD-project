from flask import Flask, render_template, request, jsonify, redirect, url_for, session, make_response
from functools import wraps
import os
import json

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')

# ─── Firebase Admin Setup ──────────────────────────────────────
try:
    import firebase_admin
    from firebase_admin import credentials, auth as fb_auth, firestore

    if not firebase_admin._apps:
        cred_json = os.environ.get('FIREBASE_CREDENTIALS_JSON')
        if cred_json:
            # Produção: lê da variável de ambiente do Render
            cred = credentials.Certificate(json.loads(cred_json))
        else:
            # Local: lê do arquivo
            cred = credentials.Certificate('serviceAccountKey.json')
        firebase_admin.initialize_app(cred)

    db = firestore.client()
    FIREBASE_ADMIN_ENABLED = True
    print("✅ Firebase Admin SDK iniciado com sucesso")
except Exception as e:
    FIREBASE_ADMIN_ENABLED = False
    print(f"⚠️  Firebase Admin SDK não disponível: {e}")
    print("   Coloque serviceAccountKey.json na raiz do projeto para habilitar verificação de token no servidor.")

# ─── Auth Decorator ────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not FIREBASE_ADMIN_ENABLED:
            return f(*args, **kwargs)
        token = request.cookies.get('fb_token')
        if not token:
            return redirect(url_for('login'))
        try:
            fb_auth.verify_id_token(token)
        except Exception:
            resp = make_response(redirect(url_for('login')))
            resp.delete_cookie('fb_token')
            return resp
        return f(*args, **kwargs)
    return decorated

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
    resp = make_response(redirect(url_for('login')))
    resp.delete_cookie('fb_token')
    return resp

# ─── Main Pages (protegidas) ───────────────────────────────────
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard/home.html')

@app.route('/auto-ficha')
@login_required
def auto_ficha():
    return render_template('sections/auto_ficha.html')

@app.route('/loja')
@login_required
def loja():
    return render_template('sections/loja.html')

@app.route('/npcs')
@login_required
def npcs():
    return render_template('sections/npcs.html')

@app.route('/mapas')
@login_required
def mapas():
    return render_template('sections/mapas.html')

# ─── API Routes ────────────────────────────────────────────────
@app.route('/api/auth/session', methods=['POST'])
def api_set_session():
    """Recebe o ID token do frontend e salva num cookie HttpOnly."""
    data = request.get_json()
    token = data.get('token') if data else None
    if not token:
        return jsonify({'status': 'error', 'msg': 'Token ausente'}), 400

    if FIREBASE_ADMIN_ENABLED:
        try:
            fb_auth.verify_id_token(token)
        except Exception as e:
            return jsonify({'status': 'error', 'msg': str(e)}), 401

    resp = make_response(jsonify({'status': 'ok'}))
    resp.set_cookie('fb_token', token, httponly=True, secure=False, samesite='Lax', max_age=3600)
    return resp

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    return jsonify({'status': 'ok'})

@app.route('/api/auth/register', methods=['POST'])
def api_register():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=True)


# ─── Groq API Proxy ───────────────────────────────────────────
@app.route('/api/gerar-ficha', methods=['POST'])
def api_gerar_ficha():
    import urllib.request
    import json as pyjson

    api_key = os.environ.get('GROQ_API_KEY')
    if not api_key:
        return jsonify({'error': 'GROQ_API_KEY não configurada'}), 500

    data = request.get_json()
    prompt = data.get('prompt')
    if not prompt:
        return jsonify({'error': 'Prompt ausente'}), 400

    payload = pyjson.dumps({
        'model': 'llama-3.3-70b-versatile',
        'max_tokens': 1500,
        'messages': [{'role': 'user', 'content': prompt}]
    }).encode('utf-8')

    req = urllib.request.Request(
        'https://api.groq.com/openai/v1/chat/completions',
        data=payload,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        },
        method='POST'
    )

    try:
        with urllib.request.urlopen(req) as resp:
            result = pyjson.loads(resp.read())
            # Retorna no formato que o frontend espera
            text = result['choices'][0]['message']['content']
            return jsonify({'content': [{'type': 'text', 'text': text}]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
