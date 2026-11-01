"""Blogly: Flask web application (application factory + blueprints)."""
import hmac
import secrets
from datetime import datetime
from pathlib import Path

from flask import Flask, abort, render_template, request, session

import auth
import db
import posts

BASE = Path(__file__).parent


def load_secret_key():
    """Read the secret from a local file, creating it on first run (never hard-code it)."""
    f = BASE / "secret.key"
    if not f.exists():
        f.write_text(secrets.token_hex(32))
    return f.read_text().strip()


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(SECRET_KEY=load_secret_key(), DATABASE=str(BASE / "blog.db"),
                      SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
                      MAX_CONTENT_LENGTH=64 * 1024)
    if test_config:
        app.config.update(test_config)
    db.init_app(app)
    app.register_blueprint(auth.bp)
    app.register_blueprint(posts.bp)

    @app.before_request
    def csrf_protect():                              # every POST must carry the session's token
        if request.method == "POST":
            token = session.get("csrf", "")
            if not token or not hmac.compare_digest(token, request.form.get("csrf_token", "")):
                abort(400)

    def csrf_token():
        session.setdefault("csrf", secrets.token_hex(16))
        return session["csrf"]
    app.jinja_env.globals["csrf_token"] = csrf_token

    @app.template_filter("fmt")
    def fmt(value):
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S").strftime("%d %b %Y")

    @app.template_filter("readtime")
    def readtime(text):
        return max(1, len(text.split()) // 200)

    messages = {400: "Bad request. Refresh the page and try again.", 403: "You are not allowed to do that.",
                404: "We could not find that page.", 413: "That request is too large."}
    for code, msg in messages.items():
        app.register_error_handler(code, lambda e, c=code, m=msg: (render_template("error.html", code=c, message=m), c))
    return app


app = create_app()
if __name__ == "__main__":
    app.run(debug=True)
