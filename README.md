# ⚔ The Legend of D&D

Site RPG/D&D com estilo medieval dark. Flask + Firebase + Firestore.

## Estrutura

```
legend-dnd/
├── app.py                          # Flask app principal
├── requirements.txt
├── render.yaml                     # Config deploy Render
├── .env.example
├── static/
│   ├── js/
│   │   └── firebase-config.js     # ← Configure aqui
│   └── images/
│       ├── logo.png               # ← Adicione sua logo
│       └── dragon-bg.jpg          # ← Adicione o fundo com dragão
└── templates/
    ├── base.html                  # Template base (estilos globais)
    ├── nav.html                   # Navbar
    ├── auth/
    │   ├── login.html
    │   └── register.html
    ├── dashboard/
    │   └── home.html
    └── sections/
        ├── auto_ficha.html        # Gerador de fichas com IA
        ├── npcs.html              # Banco de NPCs/Bosses
        ├── mapas.html             # Mapas
        └── loja.html              # Loja de fichas
```

## Setup Local

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Criar .env
cp .env.example .env
# Edite .env com sua SECRET_KEY

# 3. Configurar Firebase
# Edite static/js/firebase-config.js com seus dados do Firebase Console

# 4. Adicionar imagens
# static/images/logo.png       → sua logo (The legend of D&D)
# static/images/dragon-bg.jpg  → foto do dragão de fundo

# 5. Rodar
python app.py
```

## Deploy Render

1. Push para GitHub
2. Conecte no Render como Web Service
3. Build: `pip install -r requirements.txt`
4. Start: `gunicorn app:app`
5. Adicione variável `SECRET_KEY`

## Firebase Setup

1. Criar projeto no Firebase Console
2. Ativar Authentication (Email/Password + Google)
3. Criar Firestore database
4. Regras Firestore sugeridas:
```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /fichas/{doc} {
      allow read, write: if request.auth.uid == resource.data.uid;
      allow create: if request.auth != null;
    }
    match /npcs/{doc} {
      allow read: if true;
      allow write: if request.auth != null;
    }
    match /mapas/{doc} {
      allow read: if true;
      allow write: if request.auth != null;
    }
  }
}
```

## Seções

| Rota | Descrição |
|------|-----------|
| `/login` | Login com email ou Google |
| `/register` | Criar conta |
| `/dashboard` | Home com stats |
| `/auto-ficha` | Gerador de fichas com Claude AI |
| `/npcs` | Banco de NPCs/Bosses/Monstros |
| `/mapas` | Mapas de masmorras e regiões |
| `/loja` | Loja de conteúdo da comunidade |
