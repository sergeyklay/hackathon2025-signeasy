# Installation Guide

## Prerequisites

- Python >= 3.10, <4.0
- Node.js >= 20.0
- SQLite >= 3.36
- [Poetry](https://python-poetry.org/docs/#installation) >= 1.8
- npm >= 8.0

## Setting up the application

1. Clone the repository.
2. Install the Python dependencies using Poetry:
   ```bash
   poetry install --no-root
   ```
3. Install the Node.js dependencies using npm:
   ```bash
   npm install
   ```
4. Build the CSS file using Tailwind CSS:
   ```bash
   npx tailwindcss -i ./se/static/css/src.css -o ./se/static/css/style.css
   ```
5. Create a `.env` file by copying the `.env.example` file:
   ```bash
   cp .env.example .env
   ```
6. Generate a secret key for the Flask application:
   ```bash
   python -c 'import secrets; print(secrets.token_urlsafe(16))'
   ```
7. Update the `.env` file with the generated secret key.
8. Update the `.env` file with the [OpenAI API key](https://platform.openai.com/api-keys).
9. Create the SQLite database and apply the migrations:
   ```bash
   flask --app runner:app db init
   flask --app runner:app db upgrade
   ```

## Running the application

1. Run the following command to watch for changes in the CSS file:
   ```bash
   npx tailwindcss -i ./se/static/css/src.css -o ./se/static/css/style.css --watch
   ```
2. Next, _in a separate terminal_, run the following command to start the Flask server:
   ```bash
   flask --app runner:app run --debug
   ```
3. Open the following URL in your browser:
   ```
   http://127.0.0.1:5000
   ```
4. Enjoy!
