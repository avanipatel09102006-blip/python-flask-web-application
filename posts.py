"""Posts blueprint: feed, search, detail, CRUD, comments, author profile."""
from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from auth import login_required
from db import get_db, now

bp = Blueprint("posts", __name__)
PER_PAGE = 5
BASE_SQL = """SELECT p.*, u.username,
              (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.id) AS n_comments
              FROM posts p JOIN users u ON u.id = p.author_id"""


def paged(where="", args=()):
    page = max(1, request.args.get("page", 1, type=int))
    db = get_db()
    total = db.execute(f"SELECT COUNT(*) FROM posts p JOIN users u ON u.id = p.author_id {where}", args).fetchone()[0]
    rows = db.execute(f"{BASE_SQL} {where} ORDER BY p.created_at DESC, p.id DESC LIMIT ? OFFSET ?",
                      (*args, PER_PAGE, (page - 1) * PER_PAGE)).fetchall()
    return rows, page, max(1, -(-total // PER_PAGE)), total


@bp.route("/")
def index():
    q = request.args.get("q", "").strip()
    where, args = ("WHERE p.title LIKE ? OR p.body LIKE ?", (f"%{q}%", f"%{q}%")) if q else ("", ())
    rows, page, pages, total = paged(where, args)
    return render_template("index.html", posts=rows, page=page, pages=pages, total=total, q=q)


@bp.route("/u/<username>")
def profile(username):
    user = get_db().execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    if not user:
        abort(404)
    rows, page, pages, total = paged("WHERE p.author_id = ?", (user["id"],))
    return render_template("profile.html", profile=user, posts=rows, page=page, pages=pages, total=total)


def get_post(post_id, own=False):
    post = get_db().execute(f"{BASE_SQL} WHERE p.id = ?", (post_id,)).fetchone()
    if post is None:
        abort(404)
    if own and post["author_id"] != g.user["id"]:
        abort(403)
    return post


def read_form():
    title, body = request.form.get("title", "").strip(), request.form.get("body", "").strip()
    if not title or len(title) > 100:
        return None, None, "Title is required (max 100 characters)."
    if not body or len(body) > 5000:
        return None, None, "Content is required (max 5000 characters)."
    return title, body, None


@bp.route("/post/<int:post_id>")
def detail(post_id):
    post = get_post(post_id)
    comments = get_db().execute("""SELECT c.*, u.username FROM comments c JOIN users u ON u.id = c.author_id
                                   WHERE c.post_id = ? ORDER BY c.id""", (post_id,)).fetchall()
    return render_template("post.html", post=post, comments=comments)


@bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        title, body, error = read_form()
        if error:
            flash(error, "error")
        else:
            db, t = get_db(), now()
            pid = db.execute("INSERT INTO posts (author_id, title, body, created_at, updated_at) VALUES (?,?,?,?,?)",
                             (g.user["id"], title, body, t, t)).lastrowid
            db.commit()
            flash("Post published.", "success")
            return redirect(url_for("posts.detail", post_id=pid))
    return render_template("post_form.html", post=None)


@bp.route("/post/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
def edit(post_id):
    post = get_post(post_id, own=True)
    if request.method == "POST":
        title, body, error = read_form()
        if error:
            flash(error, "error")
        else:
            db = get_db()
            db.execute("UPDATE posts SET title=?, body=?, updated_at=? WHERE id=?", (title, body, now(), post_id))
            db.commit()
            flash("Post updated.", "success")
            return redirect(url_for("posts.detail", post_id=post_id))
    return render_template("post_form.html", post=post)


@bp.post("/post/<int:post_id>/delete")
@login_required
def delete(post_id):
    get_post(post_id, own=True)
    db = get_db()
    db.execute("DELETE FROM posts WHERE id=?", (post_id,))
    db.commit()
    flash("Post deleted.", "info")
    return redirect(url_for("posts.index"))


@bp.post("/post/<int:post_id>/comment")
@login_required
def comment(post_id):
    get_post(post_id)
    body = request.form.get("body", "").strip()
    if not body or len(body) > 500:
        flash("Comment must be 1-500 characters.", "error")
    else:
        db = get_db()
        db.execute("INSERT INTO comments (post_id, author_id, body, created_at) VALUES (?,?,?,?)", (post_id, g.user["id"], body, now()))
        db.commit()
        flash("Comment added.", "success")
    return redirect(url_for("posts.detail", post_id=post_id) + "#comments")


@bp.post("/comment/<int:comment_id>/delete")
@login_required
def delete_comment(comment_id):
    db = get_db()
    c = db.execute("""SELECT c.*, p.author_id AS post_author FROM comments c JOIN posts p ON p.id = c.post_id
                      WHERE c.id = ?""", (comment_id,)).fetchone()
    if c is None:
        abort(404)
    if g.user["id"] not in (c["author_id"], c["post_author"]):
        abort(403)
    db.execute("DELETE FROM comments WHERE id=?", (comment_id,))
    db.commit()
    flash("Comment removed.", "info")
    return redirect(url_for("posts.detail", post_id=c["post_id"]) + "#comments")
