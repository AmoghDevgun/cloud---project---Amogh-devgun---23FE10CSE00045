import os
import sqlite3

from flask import Flask, g, jsonify, request

DEFAULT_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "students.db")


def create_app(database=None):
    app = Flask(__name__)
    app.config["DATABASE"] = database or os.environ.get("DATABASE", DEFAULT_DB)

    def get_db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"])
            g.db.row_factory = sqlite3.Row
            g.db.execute("PRAGMA foreign_keys = ON")
        return g.db

    @app.teardown_appcontext
    def close_db(_error=None):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    def init_db():
        db = get_db()
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                course TEXT NOT NULL,
                year INTEGER NOT NULL
            )
            """
        )
        db.commit()

    @app.get("/health")
    def health():
        return jsonify(status="ok", service="student-management-system")

    @app.get("/students")
    def list_students():
        rows = get_db().execute("SELECT * FROM students ORDER BY id").fetchall()
        return jsonify([dict(row) for row in rows])

    @app.get("/students/<int:student_id>")
    def get_student(student_id):
        row = get_db().execute(
            "SELECT * FROM students WHERE id = ?", (student_id,)
        ).fetchone()
        if row is None:
            return jsonify(error="Student not found"), 404
        return jsonify(dict(row))

    @app.post("/students")
    def create_student():
        data = request.get_json(silent=True) or {}
        error = validate(data)
        if error:
            return jsonify(error=error), 400
        db = get_db()
        try:
            cursor = db.execute(
                "INSERT INTO students (name, email, course, year) VALUES (?, ?, ?, ?)",
                (data["name"], data["email"], data["course"], data["year"]),
            )
            db.commit()
        except sqlite3.IntegrityError:
            return jsonify(error="Email already exists"), 409
        return jsonify(id=cursor.lastrowid, **data), 201

    @app.put("/students/<int:student_id>")
    def update_student(student_id):
        data = request.get_json(silent=True) or {}
        error = validate(data)
        if error:
            return jsonify(error=error), 400
        db = get_db()
        cursor = db.execute(
            "UPDATE students SET name = ?, email = ?, course = ?, year = ? WHERE id = ?",
            (data["name"], data["email"], data["course"], data["year"], student_id),
        )
        db.commit()
        if cursor.rowcount == 0:
            return jsonify(error="Student not found"), 404
        return jsonify(id=student_id, **data)

    @app.delete("/students/<int:student_id>")
    def delete_student(student_id):
        db = get_db()
        cursor = db.execute("DELETE FROM students WHERE id = ?", (student_id,))
        db.commit()
        if cursor.rowcount == 0:
            return jsonify(error="Student not found"), 404
        return jsonify(message="Student deleted")

    with app.app_context():
        init_db()

    return app


def validate(data):
    for field in ("name", "email", "course", "year"):
        if field not in data or data[field] in ("", None):
            return f"'{field}' is required"
    if "@" not in str(data["email"]):
        return "'email' must be a valid email address"
    if not isinstance(data["year"], int) or not 1 <= data["year"] <= 6:
        return "'year' must be an integer between 1 and 6"
    return None


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
