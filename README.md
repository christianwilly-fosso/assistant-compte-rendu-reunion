---
title: Assistant Compte Rendu Reunion
emoji: 📝
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# 📝 Assistant Compte Rendu Réunion

Application web gratuite qui transcrit un audio de réunion et génère automatiquement
un compte rendu structuré (résumé, décisions, actions, points en suspens), prêt à
être partagé en **PDF**, **Word**, **texte** ou **Markdown**, ainsi qu'une
version courte optimisée pour **WhatsApp**.

L'application fonctionne **sans aucune clé API**. Une clé Groq ou Gemini facultative
peut être configurée pour améliorer la qualité et la vitesse.

## ✨ Fonctionnalités

- Upload de fichier audio (`.m4a`, `.mp3`, `.ogg`, `.wav`, `.webm`, `.flac`, `.aac`).
- Conversion audio automatique vers WAV mono 16 kHz via FFmpeg.
- **Transcription** : 3 moteurs disponibles (auto-sélectionnés selon la configuration)
  - 🚀 **Groq Whisper Large V3** — cloud, ~50× plus rapide, meilleure qualité (si `GROQ_API_KEY`).
  - 💻 **faster-whisper local** — CPU, modèles `tiny`, `base`, `small` (par défaut, sans API).
- **Résumé** : 3 modes disponibles
  - 🧠 **Groq Llama 3.3 70B** — gratuit, qualité élevée (si `GROQ_API_KEY`).
  - 🤖 **Gemini** — alternative cloud (si `GEMINI_API_KEY`).
  - 🔧 **Heuristique** — regex/scoring TF, fonctionne hors-ligne.
- Export PDF, DOCX, TXT, Markdown.
- Version courte prête à partager sur WhatsApp.
- Interface mobile-friendly.
- Suppression automatique des fichiers temporaires.

## 🚀 Démarrage local

### Linux / macOS

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

### Windows (PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

L'application est ensuite disponible sur <http://localhost:7860>.

> ℹ️ FFmpeg doit être installé sur la machine (`apt install ffmpeg`, `brew install ffmpeg`, ou [ffmpeg.org](https://ffmpeg.org/) sous Windows).

## 🐳 Démarrage Docker

```bash
docker build -t meeting-report-assistant .
docker run -p 7860:7860 meeting-report-assistant
```

## ☁️ Déploiement Hugging Face Spaces

1. Créer un compte sur <https://huggingface.co/>.
2. Créer un nouveau **Space** avec **SDK = Docker**.
3. Pousser ce dépôt vers le remote du Space.
4. (Optionnel mais recommandé) Ajouter le secret `GROQ_API_KEY` dans les paramètres du Space pour activer la transcription rapide + le résumé IA. Obtention gratuite : <https://console.groq.com/keys>.
5. (Optionnel) Alternative : `GEMINI_API_KEY` pour utiliser Gemini comme moteur de résumé.

Le `README.md` (ce fichier) contient déjà les métadonnées YAML attendues par Hugging Face Spaces.

## 🔐 Variables d'environnement

Voir [`.env.example`](.env.example). Toutes les variables sont optionnelles.

| Variable | Défaut | Rôle |
|---|---|---|
| `WHISPER_MODEL_SIZE` | `base` | `tiny`, `base`, `small`. |
| `WHISPER_DEVICE` | `cpu` | Device d'inférence. |
| `WHISPER_COMPUTE_TYPE` | `int8` | Précision de calcul. |
| `MAX_AUDIO_SIZE_MB` | `100` | Taille maximale du fichier uploadé. |
| `SUMMARY_MODE` | `auto` | `auto`, `heuristic`, `groq`, `gemini`. |
| `GROQ_API_KEY` | _vide_ | Active Groq (transcription + résumé) si renseignée. |
| `GROQ_CHAT_MODEL` | `llama-3.3-70b-versatile` | Modèle Groq pour le résumé. |
| `GROQ_WHISPER_MODEL` | `whisper-large-v3` | Modèle Groq pour la transcription. |
| `GEMINI_API_KEY` | _vide_ | Active Gemini si renseignée. |
| `GEMINI_MODEL` | `gemini-1.5-flash` | Modèle Gemini utilisé. |

## 🧪 Tests

```bash
pytest
```

## 🛡️ Confidentialité

- Aucun audio n'est conservé après traitement.
- Les fichiers WAV intermédiaires sont supprimés systématiquement.
- L'application affiche un avertissement de consentement à chaque ouverture.

## 📄 Licence

MIT.
