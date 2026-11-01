# Blogly: Flask Web Application

    pip install -r requirements.txt
    python app.py
Open http://127.0.0.1:5000   (demo login: demo / demo123)

Flask concepts demonstrated
- Application factory (`create_app`) and Blueprints (`auth`, `posts`)
- Jinja2 template inheritance, macros, custom filters, flash messages, error pages
- Sessions + password hashing, `login_required` decorator, author-only edit/delete (403)
- CSRF token on every POST, parameterised SQL, safe `next` redirect, request size limit
- SQLite with foreign keys, cascade deletes, search and pagination

Structure: app.py, auth.py, posts.py, db.py, schema.sql, templates/, static/
