# Cahier de réalisation — Assistant gratuit de transcription et compte rendu de réunion

## 1. Objectif du projet

Créer une application web gratuite permettant à une personne de :

1. téléverser un fichier audio de réunion ;
2. obtenir une transcription en français ;
3. générer un compte rendu clair ;
4. extraire les décisions, actions, responsables et échéances ;
5. exporter le résultat en Markdown, texte WhatsApp, `.txt`, `.docx` ou `.pdf` ;
6. héberger l’application gratuitement, idéalement sur Hugging Face Spaces.

Le projet doit être pensé pour un contexte où les moyens financiers sont limités, avec un usage principalement mobile et WhatsApp.

---

## 2. Positionnement technique recommandé

Même si le développeur principal connaît .NET, il ne faut pas se limiter à .NET pour ce projet.

Pour ce besoin précis, le meilleur choix pour le MVP est :

```text
Python + Gradio + faster-whisper + FFmpeg + résumé algorithmique + Gemini optionnel + Hugging Face Spaces Docker
```

Pourquoi ce choix :

- Python est l’écosystème le plus simple pour la transcription audio et les modèles IA.
- Gradio permet de créer rapidement une interface web utilisable sur mobile.
- faster-whisper permet d’exécuter Whisper sur CPU avec de meilleures performances que l’implémentation Python originale.
- FFmpeg permet de convertir presque tous les formats audio.
- Hugging Face Spaces permet un hébergement gratuit adapté aux applications IA.
- Gemini API peut être ajouté comme amélioration optionnelle, mais l’application doit fonctionner sans clé API.

.NET pourra être envisagé plus tard pour une version enterprise ou intégrée à un système existant, mais pour le MVP gratuit, Python est le choix le plus pertinent.

---

## 3. Besoin utilisateur

L’utilisateur participe à des réunions et souhaite prendre rapidement des notes sans avoir à tout écrire manuellement.

Cas d’usage principal :

- Avant ou pendant la réunion, il enregistre l’audio avec son téléphone.
- Après la réunion, il téléverse le fichier audio dans l’application.
- L’application produit automatiquement :
  - la transcription complète ;
  - un résumé court ;
  - un compte rendu structuré ;
  - les décisions prises ;
  - les actions à faire ;
  - les points en suspens ;
  - une version courte prête à partager sur WhatsApp.

---

## 4. Contraintes importantes

### 4.1 Gratuité

La solution doit fonctionner sans abonnement payant.

Le choix recommandé est :

- **Hébergement principal : Hugging Face Spaces gratuit**
- **Transcription : faster-whisper**
- **Conversion audio : FFmpeg**
- **Résumé :**
  - mode gratuit sans API : résumé algorithmique simple ;
  - mode amélioré optionnel : Gemini API avec clé gratuite, si disponible.

Il ne faut pas dépendre uniquement d’une API payante.

### 4.2 Usage mobile

L’interface doit être simple sur téléphone :

- bouton d’import audio ;
- bouton de transcription ;
- bouton de génération du compte rendu ;
- bouton copier le texte WhatsApp ;
- boutons de téléchargement.

### 4.3 Connexion Internet limitée

L’application doit :

- accepter des fichiers compressés `.m4a`, `.mp3`, `.ogg`, `.wav`, `.webm` ;
- convertir l’audio en format léger avant transcription ;
- limiter la taille maximale par défaut ;
- afficher une progression ou au moins des messages d’état.

### 4.4 Confidentialité

L’application traite potentiellement des réunions sensibles.

Exigences minimales :

- supprimer les fichiers audio temporaires après traitement ;
- ne pas conserver les fichiers par défaut ;
- ne pas publier de transcription ;
- afficher un avertissement indiquant qu’il faut obtenir le consentement des participants avant d’enregistrer.

---

## 5. Architecture recommandée pour le MVP

```text
meeting-report-assistant/
│
├── app.py
├── requirements.txt
├── README.md
├── Dockerfile
├── .env.example
├── .gitignore
│
├── src/
│   ├── audio/
│   │   ├── __init__.py
│   │   ├── audio_converter.py
│   │   └── audio_validator.py
│   │
│   ├── transcription/
│   │   ├── __init__.py
│   │   ├── transcriber.py
│   │   └── whisper_transcriber.py
│   │
│   ├── summary/
│   │   ├── __init__.py
│   │   ├── summary_provider.py
│   │   ├── heuristic_summary_provider.py
│   │   └── gemini_summary_provider.py
│   │
│   ├── reports/
│   │   ├── __init__.py
│   │   ├── report_model.py
│   │   ├── markdown_report_generator.py
│   │   ├── whatsapp_report_generator.py
│   │   ├── text_exporter.py
│   │   ├── docx_exporter.py
│   │   └── pdf_exporter.py
│   │
│   └── shared/
│       ├── __init__.py
│       ├── settings.py
│       └── cleanup.py
│
└── tests/
    ├── test_audio_validator.py
    ├── test_heuristic_summary_provider.py
    └── test_report_generator.py
```

Principes :

- `app.py` ne doit contenir que l’interface Gradio et l’orchestration simple.
- La logique de conversion audio doit rester dans `src/audio`.
- La logique de transcription doit rester dans `src/transcription`.
- La logique de résumé doit rester dans `src/summary`.
- La logique de génération de fichiers doit rester dans `src/reports`.
- Les paramètres et le nettoyage doivent rester dans `src/shared`.

---

## 6. Interface utilisateur

Utiliser **Gradio**.

Interface minimale :

- titre : `Assistant Compte Rendu Réunion` ;
- avertissement sur le consentement ;
- champ upload audio ;
- choix de la langue : `auto`, `fr`, `en` ;
- choix du modèle Whisper : `tiny`, `base`, `small` ;
- choix du mode de résumé : `Automatique`, `Algorithmique`, `Gemini si configuré` ;
- bouton `Transcrire et générer le compte rendu` ;
- zone transcription ;
- zone compte rendu Markdown ;
- zone version WhatsApp ;
- fichiers téléchargeables : `.md`, `.txt`, optionnellement `.docx` et `.pdf`.

---

## 7. Transcription

Utiliser **faster-whisper**.

Configuration par défaut :

```python
model_size = "base"
compute_type = "int8"
device = "cpu"
```

Modèles proposés :

| Modèle | Qualité | Vitesse | Recommandation |
|---|---:|---:|---|
| tiny | faible | très rapide | tests rapides |
| base | correcte | rapide | valeur par défaut |
| small | meilleure | plus lente | si le serveur le supporte |
| medium | bonne | lente | pas recommandé sur hébergement gratuit |
| large | très bonne | très lente | pas recommandé en gratuit |

Pour le MVP gratuit, utiliser `base` par défaut.

---

## 8. Conversion audio

Utiliser **FFmpeg**.

Objectif :

- convertir n’importe quel fichier audio supporté vers un format compatible ;
- réduire la taille ;
- uniformiser l’échantillonnage.

Commande cible :

```bash
ffmpeg -y -i input_audio -ar 16000 -ac 1 output.wav
```

Explication :

- `-ar 16000` : fréquence adaptée à la transcription vocale ;
- `-ac 1` : mono ;
- `output.wav` : format simple pour Whisper.

---

## 9. Résumé et compte rendu

L’application doit supporter deux modes.

### 9.1 Mode A — Gratuit sans API

Implémenter un résumé algorithmique simple.

Ce mode doit fonctionner même sans clé API.

Il peut produire :

- résumé court basé sur les phrases les plus informatives ;
- liste de décisions détectées par mots-clés ;
- actions détectées par expressions comme :
  - `il faut` ;
  - `on doit` ;
  - `à faire` ;
  - `sera responsable` ;
  - `d’ici` ;
  - `avant le` ;
  - `prochaine étape`.

Ce mode ne sera pas aussi intelligent qu’un LLM, mais il rend la solution indépendante et gratuite.

### 9.2 Mode B — Optionnel avec Gemini API

Ajouter un fournisseur `GeminiSummaryProvider`.

Il doit être optionnel.

Si la variable d’environnement `GEMINI_API_KEY` est absente, l’application doit fonctionner avec le mode algorithmique.

Prompt recommandé pour Gemini :

```text
Tu es un assistant professionnel de compte rendu de réunion.

À partir de la transcription ci-dessous, produis un compte rendu clair en français.

Contraintes :
- Corrige le français sans inventer d'information.
- Ne crée pas de décision ou d'action si elle n'est pas dans la transcription.
- Si une information est absente, écris "Non précisé".
- Structure la réponse avec les sections demandées.

Sections attendues :
1. Titre proposé de la réunion
2. Date, si mentionnée
3. Participants, si mentionnés
4. Résumé exécutif
5. Points discutés
6. Décisions prises
7. Actions à faire sous forme de tableau : Action | Responsable | Échéance | Statut
8. Points en suspens
9. Version courte prête à envoyer sur WhatsApp

Transcription :
{{TRANSCRIPTION}}
```

---

## 10. Modèle de données interne

Créer un modèle simple :

```python
from dataclasses import dataclass

@dataclass
class ActionItem:
    description: str
    responsible: str | None
    due_date: str | None
    status: str | None

@dataclass
class MeetingReport:
    title: str
    date: str | None
    participants: list[str]
    executive_summary: str
    discussed_points: list[str]
    decisions: list[str]
    action_items: list[ActionItem]
    pending_points: list[str]
    full_transcription: str
    whatsapp_summary: str
```

---

## 11. Structure du compte rendu généré

Le compte rendu Markdown doit suivre ce format :

```markdown
# Compte rendu de réunion

## Informations générales

- Date : Non précisée
- Participants : Non précisés
- Sujet : Non précisé

## Résumé exécutif

...

## Points discutés

1. ...
2. ...

## Décisions prises

1. ...
2. ...

## Actions à faire

| Action | Responsable | Échéance | Statut |
|---|---|---|---|
| ... | ... | ... | À faire |

## Points en suspens

1. ...
2. ...

## Transcription complète

...
```

---

## 12. Version WhatsApp

La version WhatsApp doit être courte et lisible :

```text
📝 Compte rendu de réunion

📌 Sujet :
...

✅ Résumé :
...

📍 Décisions :
1. ...
2. ...

📋 Actions :
- ... — Responsable : ... — Échéance : ...

❓ Points en suspens :
- ...
```

Elle doit éviter les longs paragraphes.

---

## 13. Fonctionnalités du MVP

### 13.1 Fonctionnalités obligatoires

- Upload d’un fichier audio.
- Validation du format.
- Validation de la taille maximale.
- Conversion audio via FFmpeg.
- Transcription avec faster-whisper.
- Génération d’un compte rendu structuré.
- Génération d’une version WhatsApp.
- Export `.md`.
- Export `.txt`.
- Suppression des fichiers temporaires.
- Interface mobile simple.

### 13.2 Fonctionnalités importantes mais optionnelles

- Export `.docx`.
- Export `.pdf`.
- Choix du modèle Whisper.
- Choix du mode résumé : algorithmique ou Gemini.
- Historique local temporaire.
- Découpage automatique des longues réunions.
- Détection approximative des locuteurs.
- Recherche dans la transcription.
- Support multilingue français / anglais.

### 13.3 Fonctionnalités à ne pas faire dans le MVP

- Bot WhatsApp officiel.
- Connexion automatique à Zoom/Teams/Google Meet.
- Transcription en direct complète.
- Authentification complexe.
- Stockage long terme des réunions.
- Gestion multi-utilisateurs avancée.

Ces fonctionnalités peuvent être ajoutées plus tard.

---

## 14. Flux utilisateur cible

```text
1. L’utilisateur ouvre l’application web.
2. Il lit l’avertissement de consentement.
3. Il téléverse un fichier audio.
4. Il choisit la langue ou laisse "auto".
5. Il clique sur "Transcrire et générer le compte rendu".
6. L’application affiche :
   - statut de conversion ;
   - statut de transcription ;
   - statut de génération du compte rendu.
7. L’utilisateur obtient :
   - transcription complète ;
   - compte rendu ;
   - version WhatsApp.
8. Il copie le texte ou télécharge un fichier.
9. Les fichiers temporaires sont supprimés.
```

---

## 15. Exigences non fonctionnelles

### Performance

- Un audio de 10 minutes doit pouvoir être traité sans crash.
- Un audio de 30 minutes doit être accepté, mais peut prendre du temps.
- Les fichiers très longs doivent être refusés ou découpés.

### Robustesse

- Si FFmpeg échoue, afficher un message clair.
- Si la transcription échoue, afficher un message clair.
- Si Gemini n’est pas configuré, utiliser le résumé algorithmique.
- Si l’export PDF échoue, permettre au moins l’export Markdown et texte.

### Sécurité

- Ne jamais exposer les variables d’environnement.
- Ne jamais afficher les clés API.
- Supprimer les fichiers temporaires après traitement.
- Ne pas accepter de fichiers exécutables.

### Accessibilité

- Interface claire.
- Texte lisible sur mobile.
- Boutons explicites.
- État de traitement visible.

---

## 16. Déploiement Hugging Face Spaces

### 16.1 `requirements.txt`

```txt
gradio
faster-whisper
ffmpeg-python
python-docx
reportlab
pydantic
python-dotenv
google-generativeai
pytest
```

`google-generativeai` est optionnel fonctionnellement, mais peut être installé pour permettre le mode Gemini.

### 16.2 `Dockerfile`

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["python", "app.py"]
```

### 16.3 `README.md` pour Hugging Face

```markdown
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

# Assistant Compte Rendu Réunion

Application gratuite pour transcrire un audio de réunion et générer un compte rendu structuré.
```

### 16.4 Étapes de déploiement

1. Créer un compte Hugging Face.
2. Créer un nouveau Space.
3. Choisir `Docker` comme SDK.
4. Créer un dépôt Git local.
5. Ajouter les fichiers du projet.
6. Pousser le code vers le dépôt du Space.
7. Attendre le build.
8. Tester l’application.
9. Configurer `GEMINI_API_KEY` dans les secrets du Space si le mode Gemini est voulu.

---

## 17. Exemple d’orchestration attendue dans `app.py`

L’IA qui développera le projet doit produire un code propre, mais l’idée générale est :

```python
import gradio as gr

from src.audio.audio_converter import convert_to_wav
from src.transcription.whisper_transcriber import WhisperTranscriber
from src.summary.heuristic_summary_provider import HeuristicSummaryProvider
from src.summary.gemini_summary_provider import GeminiSummaryProvider
from src.reports.markdown_report_generator import MarkdownReportGenerator
from src.reports.whatsapp_report_generator import WhatsAppReportGenerator
from src.shared.cleanup import cleanup_files
from src.shared.settings import Settings

settings = Settings.load()

transcriber = WhisperTranscriber(
    model_size=settings.whisper_model_size,
    device="cpu",
    compute_type="int8"
)

summary_provider = GeminiSummaryProvider(settings.gemini_api_key) \
    if settings.gemini_api_key else HeuristicSummaryProvider()

markdown_generator = MarkdownReportGenerator()
whatsapp_generator = WhatsAppReportGenerator()

def process_meeting(audio_file, language, whisper_model):
    temp_files = []

    try:
        wav_path = convert_to_wav(audio_file)
        temp_files.append(wav_path)

        transcription = transcriber.transcribe(
            audio_path=wav_path,
            language=None if language == "auto" else language,
            model_size=whisper_model
        )

        report = summary_provider.generate_report(transcription)

        markdown = markdown_generator.generate(report)
        whatsapp = whatsapp_generator.generate(report)

        return transcription, markdown, whatsapp

    finally:
        cleanup_files(temp_files)

with gr.Blocks(title="Assistant Compte Rendu Réunion") as demo:
    gr.Markdown("# 📝 Assistant Compte Rendu Réunion")
    gr.Markdown(
        "Importez un audio de réunion pour générer une transcription et un compte rendu. "
        "Assurez-vous d’avoir le consentement des participants avant d’enregistrer."
    )

    audio = gr.Audio(type="filepath", label="Fichier audio")
    language = gr.Dropdown(
        choices=["auto", "fr", "en"],
        value="auto",
        label="Langue"
    )
    whisper_model = gr.Dropdown(
        choices=["tiny", "base", "small"],
        value="base",
        label="Modèle Whisper"
    )

    submit = gr.Button("Transcrire et générer le compte rendu")

    transcription_output = gr.Textbox(label="Transcription complète", lines=12)
    markdown_output = gr.Textbox(label="Compte rendu Markdown", lines=12)
    whatsapp_output = gr.Textbox(label="Version WhatsApp", lines=8)

    submit.click(
        fn=process_meeting,
        inputs=[audio, language, whisper_model],
        outputs=[transcription_output, markdown_output, whatsapp_output]
    )

demo.launch(server_name="0.0.0.0", server_port=7860)
```

L’IA peut améliorer ce code, mais elle doit garder la simplicité.

---

## 18. Tests à prévoir

### Tests unitaires

Créer des tests pour :

- validation des formats audio ;
- génération du résumé algorithmique ;
- génération Markdown ;
- génération WhatsApp ;
- suppression des fichiers temporaires ;
- comportement sans clé Gemini.

### Tests manuels

Tester avec :

- audio court de 30 secondes ;
- audio français de 5 minutes ;
- audio avec bruit ;
- audio bilingue français/anglais ;
- fichier non supporté ;
- fichier trop lourd ;
- absence de clé Gemini ;
- présence de clé Gemini.

---

## 19. Améliorations futures

### Version 2

- Authentification simple.
- Historique des réunions.
- Export `.docx` et `.pdf` plus professionnel.
- Modèles de compte rendu personnalisables.
- Découpage intelligent des longues réunions.
- Détection des locuteurs avec pyannote ou autre solution, si gratuit et acceptable.
- Correction automatique de la ponctuation.
- Recherche dans les anciennes réunions.

### Version 3

- Application mobile PWA.
- Mode hors ligne partiel.
- Installation locale sur ordinateur.
- Partage direct WhatsApp.
- Bot WhatsApp officiel si un budget existe.
- Déploiement sur serveur personnel ou mini-PC.
- Version .NET si besoin d’intégration avec un écosystème existant.

---

## 20. Prompt complet à fournir à Claude Code ou une autre IA de développement

Copier-coller le prompt suivant dans Claude Code.

```text
Tu es un développeur senior full-stack et IA.

Je veux que tu construises une application web gratuite appelée "Assistant Compte Rendu Réunion".

Contexte :
L’application doit aider une personne à transcrire des réunions et générer automatiquement des comptes rendus. Le contexte économique est limité, donc la solution doit fonctionner gratuitement autant que possible. L’application sera hébergée gratuitement sur Hugging Face Spaces.

Choix technologique imposé pour le MVP :
- Python 3.11
- Gradio pour l’interface web
- faster-whisper pour la transcription
- FFmpeg pour la conversion audio
- Docker pour le déploiement Hugging Face Spaces
- Résumé algorithmique par défaut, sans API obligatoire
- Gemini API optionnelle si la variable GEMINI_API_KEY est configurée

Objectifs :
1. Permettre l’upload d’un fichier audio.
2. Convertir l’audio en WAV mono 16 kHz avec FFmpeg.
3. Transcrire l’audio avec faster-whisper sur CPU.
4. Générer un compte rendu structuré en français.
5. Générer une version courte prête à envoyer sur WhatsApp.
6. Exporter le résultat en Markdown et TXT.
7. Prévoir optionnellement DOCX et PDF.
8. Supprimer les fichiers temporaires après traitement.
9. Prévoir une interface simple et utilisable sur mobile.
10. Prévoir le déploiement gratuit sur Hugging Face Spaces avec Docker.

Architecture attendue :
- app.py
- requirements.txt
- Dockerfile
- README.md
- src/audio/audio_converter.py
- src/audio/audio_validator.py
- src/transcription/transcriber.py
- src/transcription/whisper_transcriber.py
- src/summary/summary_provider.py
- src/summary/heuristic_summary_provider.py
- src/summary/gemini_summary_provider.py
- src/reports/report_model.py
- src/reports/markdown_report_generator.py
- src/reports/whatsapp_report_generator.py
- src/reports/text_exporter.py
- src/reports/docx_exporter.py
- src/reports/pdf_exporter.py
- src/shared/settings.py
- src/shared/cleanup.py
- tests/

Exigences de qualité :
- Code propre, simple, maintenable.
- Séparation claire des responsabilités.
- Pas de logique lourde directement dans l’interface Gradio.
- Gestion claire des erreurs.
- Messages d’erreur compréhensibles pour un utilisateur non technique.
- Pas de dépendance obligatoire à une API payante.
- Pas de stockage permanent des audios.
- Variables d’environnement pour les clés API.
- Tests unitaires pour les parties non UI.

Contraintes de performance :
- Modèle Whisper par défaut : base
- Device : CPU
- compute_type : int8
- Supporter tiny, base et small.
- Refuser ou avertir pour les fichiers trop longs.
- Nettoyer les fichiers temporaires.

Sorties attendues :
- Transcription complète
- Compte rendu Markdown
- Version WhatsApp
- Fichier Markdown téléchargeable
- Fichier TXT téléchargeable
- Option DOCX/PDF si raisonnable

Format du compte rendu :
# Compte rendu de réunion

## Informations générales
- Date :
- Participants :
- Sujet :

## Résumé exécutif

## Points discutés

## Décisions prises

## Actions à faire
| Action | Responsable | Échéance | Statut |

## Points en suspens

## Transcription complète

Version WhatsApp :
📝 Compte rendu de réunion
📌 Sujet :
✅ Résumé :
📍 Décisions :
📋 Actions :
❓ Points en suspens :

Important :
Commence par créer toute la structure du projet. Ensuite implémente les fichiers. Ensuite ajoute le Dockerfile et le README compatible Hugging Face Spaces. Ensuite ajoute les tests. Finalement donne les commandes exactes pour exécuter localement et déployer sur Hugging Face Spaces.
```

---

## 21. Définition de terminé

Le projet est considéré terminé lorsque :

- l’application démarre localement avec `python app.py` ;
- l’application démarre avec Docker ;
- l’upload audio fonctionne ;
- la conversion FFmpeg fonctionne ;
- la transcription fonctionne avec le modèle `base` ;
- un compte rendu Markdown est généré ;
- une version WhatsApp est générée ;
- les fichiers temporaires sont supprimés ;
- l’application fonctionne sans clé Gemini ;
- l’application utilise Gemini si `GEMINI_API_KEY` est configurée ;
- le dépôt peut être poussé sur Hugging Face Spaces ;
- le Space démarre et affiche l’interface.

---

## 22. Commandes locales attendues

### Installation locale

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Sous Windows PowerShell :

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

### Docker local

```bash
docker build -t meeting-report-assistant .
docker run -p 7860:7860 meeting-report-assistant
```

L’application doit être disponible sur :

```text
http://localhost:7860
```

---

## 23. Sources techniques utiles

Ces sources permettent de valider les choix techniques au moment du développement :

- Hugging Face Spaces : https://huggingface.co/docs/hub/en/spaces-overview
- Hugging Face Spaces GPU / hardware : https://huggingface.co/docs/hub/en/spaces-gpus
- faster-whisper : https://github.com/SYSTRAN/faster-whisper
- whisper.cpp : https://github.com/ggml-org/whisper.cpp
- Gemini API pricing / free tier : https://ai.google.dev/gemini-api/docs/pricing
- Cloudflare Pages limits : https://developers.cloudflare.com/pages/platform/limits/
- Render free plan : https://render.com/docs/free

---

## 24. Décision finale recommandée

La solution la plus pertinente est :

```text
Python + Gradio + faster-whisper + FFmpeg + résumé algorithmique + Gemini optionnel + Hugging Face Spaces Docker
```

Cette combinaison répond le mieux aux besoins :

- gratuite ;
- rapide à développer ;
- adaptée à l’IA audio ;
- accessible depuis un téléphone ;
- hébergeable gratuitement ;
- indépendante d’un abonnement payant ;
- extensible plus tard vers WhatsApp, PWA, stockage, authentification ou version locale.
