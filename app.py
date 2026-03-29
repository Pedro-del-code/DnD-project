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
    import requests as req_lib

    api_key = os.environ.get('GROQ_API_KEY')
    if not api_key:
        return jsonify({'error': 'GROQ_API_KEY não configurada'}), 500

    data = request.get_json()
    prompt = data.get('prompt')
    if not prompt:
        return jsonify({'error': 'Prompt ausente'}), 400

    try:
        r = req_lib.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json={
                'model': 'llama-3.3-70b-versatile',
                'max_tokens': 1500,
                'messages': [{'role': 'user', 'content': prompt}]
            },
            timeout=30
        )
        r.raise_for_status()
        text = r.json()['choices'][0]['message']['content']
        return jsonify({'choices': [{'message': {'content': text}}]})
    except Exception as e:
        print(f"Groq error: {e}")
        return jsonify({'error': str(e)}), 500


# ─── Admin ────────────────────────────────────────────────────
import hashlib

ADMIN_EMAIL = 'legendofdnd.suporte@gmail.com'
ADMIN_SENHA_HASH = hashlib.sha256('legendmilionario'.encode()).hexdigest()

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logado'):
            return redirect('/admin')
        return f(*args, **kwargs)
    return decorated

@app.route('/admin')
def admin_login():
    if session.get('admin_logado'):
        return redirect('/admin/dashboard')
    return render_template('admin/login.html')

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    return render_template('admin/dashboard.html')

@app.route('/admin/api/login', methods=['POST'])
def admin_api_login():
    data = request.get_json()
    email = data.get('email', '').strip()
    senha = data.get('senha', '')
    senha_hash = hashlib.sha256(senha.encode()).hexdigest()
    if email == ADMIN_EMAIL and senha_hash == ADMIN_SENHA_HASH:
        session['admin_logado'] = True
        return jsonify({'ok': True})
    return jsonify({'ok': False}), 401

@app.route('/admin/api/logout', methods=['POST'])
def admin_api_logout():
    session.pop('admin_logado', None)
    return jsonify({'ok': True})

@app.route('/admin/api/usuarios')
@admin_required
def admin_api_usuarios():
    if not FIREBASE_ADMIN_ENABLED:
        return jsonify({'usuarios': []})
    docs = db.collection('usuarios').stream()
    usuarios = []
    for doc in docs:
        d = doc.to_dict()
        d['uid'] = doc.id
        usuarios.append(d)
    return jsonify({'usuarios': usuarios})

@app.route('/admin/api/toggle-acesso', methods=['POST'])
@admin_required
def admin_api_toggle():
    if not FIREBASE_ADMIN_ENABLED:
        return jsonify({'ok': False, 'error': 'Firebase não disponível'}), 500
    data = request.get_json()
    uid = data.get('uid')
    ficha_ativa = data.get('ficha_ativa', False)
    if not uid:
        return jsonify({'ok': False, 'error': 'UID ausente'}), 400
    db.collection('usuarios').document(uid).set({'ficha_ativa': ficha_ativa}, merge=True)
    return jsonify({'ok': True})

@app.route('/admin/api/adicionar-usuario', methods=['POST'])
@admin_required
def admin_api_adicionar():
    if not FIREBASE_ADMIN_ENABLED:
        return jsonify({'ok': False, 'error': 'Firebase não disponível'}), 500
    data = request.get_json()
    uid = data.get('uid', '').strip()
    if not uid:
        return jsonify({'ok': False, 'error': 'UID ausente'}), 400
    doc_data = {'ficha_ativa': data.get('ficha_ativa', False)}
    if data.get('nome'):  doc_data['nome']  = data['nome']
    if data.get('email'): doc_data['email'] = data['email']
    db.collection('usuarios').document(uid).set(doc_data, merge=True)
    return jsonify({'ok': True})
