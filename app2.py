from flask import Flask, render_template, request, redirect, url_for,session, flash
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

app2 = Flask(__name__)
app2.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///registered_todos.db'
app2.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
app2.secret_key = '123'
db = SQLAlchemy(app2)
app2.app_context().push()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    todos = db.relationship('Todo', backref='user', lazy=True)

class Todo(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    title=db.Column(db.String(200), nullable=False)
    desc=db.Column(db.String(500), nullable=False)
    time=db.Column(db.DateTime, default=datetime.utcnow())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


@app2.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        new_user = User(email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app2.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app2.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email, password=password).first()
        
        if user:
            session['user_id']=user.id
            return redirect(url_for('todo'))
        else:
            flash('Login failed. Please check your email and password.', 'danger')
    return render_template('login.html')

@app2.route('/todo', methods=['GET', 'POST'])
def todo():
    user_id=session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    if request.method=='POST':
        title=request.form['title']
        desc=request.form['desc']
        todo=Todo(title=title, desc=desc,user_id=user_id)
        db.session.add(todo)
        db.session.commit()
    
    user=User.query.get(user_id)
    todos=user.todos
    return render_template('first.html',todos=todos,allTodo=todos)

@app2.route('/update/<int:id>' ,methods=['GET','POST'])
def update(id):
    if(request.method=='POST'):
        title=request.form['title']
        desc=request.form['desc']
        todo=Todo.query.filter_by(id=id).first()
        todo.title=title
        todo.desc=desc
        db.session.add(todo)
        db.session.commit()
        return redirect(url_for("todo"))
    todo=Todo.query.filter_by(id=id).first()    
    return render_template('update.html',todo=todo)

@app2.route('/delete/<int:id>')
def delete(id):
    todo=Todo.query.filter_by(id=id).first()
    db.session.delete(todo)
    db.session.commit()
    return redirect(url_for('todo'))


if __name__ =="__main__":
    db.create_all()
    app2.run(debug=True)
