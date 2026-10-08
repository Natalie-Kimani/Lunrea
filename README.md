# Lunrea

Lunrea is a private memory and storytelling app — where every moment can have more than one story.

## Current build
- Flask + PostgreSQL backend
- JWT authentication
- 15-minute app-lock timeout
- Private 4–6 digit PIN for unlocking after the timeout (no password re-entry)
- Vertical desktop sidebar and responsive mobile navigation
- Lunrea logo integrated throughout the interface
- Dark/light appearance switch with the Lunrea dusk, lavender and champagne palette
- Memories, media uploads, camera flow, albums, chapters and collaborative chat
- CORS enabled for the Vite development frontend

## Run the backend
```bash
cd ~/Lunrea
source venv/bin/activate
pip install -r requirements.txt
flask --app run.py db upgrade
python3 run.py
```

## Run the frontend
```bash
cd ~/Lunrea/frontend
npm install
cp .env.example .env
npm run dev
```

Open `http://localhost:5173`.

## PIN behavior
The account password is still used for normal login. Once logged in, Lunrea asks the user to create a private 4–6 digit app PIN. When the 15-minute app session expires, Lunrea locks the app and asks for that PIN only. The user does not need to log in again unless they explicitly log out.

## Appearance
The selected light/dark mode is stored locally in the browser and restored on the next visit.

## Important
Do not commit `.env`, uploaded media, `venv`, or `node_modules` to Git.
