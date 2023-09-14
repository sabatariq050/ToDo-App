from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from random import randint

flask_app = Flask(__name__)
flask_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///registered_todos.db"
flask_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
flask_app.secret_key = "123"
db = SQLAlchemy(flask_app)
flask_app.app_context().push()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    todos = db.relationship("Todo", backref="user", lazy=True)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    desc = db.Column(db.String(500), nullable=False)
    time = db.Column(db.DateTime, default=datetime.utcnow())
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

class DeletedTodo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    desc = db.Column(db.String(500), nullable=False)
    time = db.Column(db.DateTime, default=datetime.utcnow())
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

class TodoHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    todo_id = db.Column(db.Integer, db.ForeignKey('todo.id'), nullable=False)
    title_previous = db.Column(db.String(200), nullable=False)
    desc_previous = db.Column(db.String(500), nullable=False)
    title_updated = db.Column(db.String(200), nullable=False)
    desc_updated = db.Column(db.String(500), nullable=False)
    time = db.Column(db.DateTime, default=datetime.utcnow())

users_session = []


@flask_app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("A user with this email already exists. Please log in or use a different email.", "danger")
            return redirect(url_for("register"))  # Redirect back to the registration page
        new_user = User(email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! You can now log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")


@flask_app.route("/logout")
def logout():
    session.pop("user_id")
    return redirect(url_for("login"))


@flask_app.route("/", methods=["GET", "POST"])
def login():
    if 'user_id' in session:
        # User is already authenticated, redirect to the 'todo' page
        return redirect(url_for('todo'))
    
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email, password=password).first()

        if user:
            session["user_id"] = user.id
            session["user_email"] = user.email
            users_session.append(user.id)

            return redirect(url_for("todo"))

        else:
            flash("Login failed. Please check your email and password.", "danger")
    return render_template("login.html")


@flask_app.route("/todo", methods=["GET", "POST"])
def todo():
    user_id = session.get("user_id")
    user_email = session.get("user_email")
    if not user_id:
        return redirect(url_for("login"))
    if request.method == "POST":
        title = request.form["title"]
        desc = request.form["desc"]
        todo = Todo(title=title, desc=desc, user_id=user_id)
        db.session.add(todo)
        db.session.commit()

    user = User.query.get(user_id)
    todos = user.todos
    return render_template(
        "first.html",
        todos=todos,
        allTodo=todos,
        user_email=user_email,
        users_session=users_session,
    )


@flask_app.route("/update/<int:id>", methods=["GET", "POST"])
def update(id):
    todo = Todo.query.get(id)
    if todo:
        if request.method == 'POST':
            title = request.form['title']
            desc = request.form['desc']
            
            # Create a record in TodoHistory to store the previous and updated data
            history_record = TodoHistory(
                todo_id=todo.id,
                title_previous=todo.title,
                desc_previous=todo.desc,
                title_updated=title,
                desc_updated=desc
            )
            db.session.add(history_record)
            
            # Update the original todo
            todo.title = title
            todo.desc = desc
            
            db.session.commit()
            
            return redirect(url_for('todo'))
    return render_template('update.html', todo=todo)


@flask_app.route("/delete/<int:id>")
def delete(id):
    todo = Todo.query.filter_by(id=id).first()
    if todo:
        # Create a new DeletedTodo record with the deleted todo's data
        deleted_todo = DeletedTodo(
            title=todo.title,
            desc=todo.desc,
            user_id=todo.user_id
        )
        db.session.add(deleted_todo)
        db.session.delete(todo)
        db.session.commit()
    return redirect(url_for("todo"))


@flask_app.route("/switch_profile", methods=["POST"])
def switch_profile():
    selected_user_id = int(request.form["selected_user"])
    session["user_id"] = selected_user_id

    # Redirect to the 'todo' page with the selected user's profile
    return redirect(url_for("todo"))


if __name__ == "__main__":
    db.create_all()
    flask_app.run(debug=True)
