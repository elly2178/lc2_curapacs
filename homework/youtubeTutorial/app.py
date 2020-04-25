# gives you an outline of the entire application
from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# sets up the application
app = Flask(__name__)
# @ app.confog['...']: it tells you where the database is located
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
# initialize db
db = SQLAlchemy(app)


# creates the model
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # text column. it holds each task
    content = db.Column(db.String(200), nullable=False)
    # datetime.utcnow: it gives back the time of creation 
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Task %r>' % self.id

    # After the class is created, activate the db
    # in the terminal: python --> from app import db --> db.create_all() --> exit
    # this will create a db in the folder whre you are working

# add this AFTER THE Model was created to avoid typing in the terminal ..  
db.create_all()
# index route with the url
@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        # logic for adding a task
        task_content = request.form['content'] 
        # Todo object 
        new_task =Todo(content=task_content)

        try:
            #push to db
            db.session.add(new_task)
            db.session.commit()
            return redirect('/')
            # redirect to the index page
        
        except:
            # if the code above fails:
            return ' an issue adding your task'
        
    else:
        tasks = Todo.query.order_by(Todo.date_created).all()
        # use .first() is you want to get the latest one alway on top
        return render_template('index.html', tasks = tasks)
        # by tasks = tasks you pass the variable to the tamplate

@app.route('/delete/<int:id>')
def delete(id):
    task_to_delete = Todo.query.get_or_404(id)
    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect('/')
    except:
        return 'Problem in deleting the task'

@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    task = Todo.query.get_or_404(id)
    if request.method == 'POST':
        task.content = request.form['content']
        try:
            db.session.commit()
            return redirect('/')        
        except:
            return 'Update not possible'
    else:
        return render_template('/update.html', task = task)
# fi atenta la spatii dintre name si main 
if __name__ == "__main__":
    # listen on all interfaces on port 80
    app.run(debug = True,host='10.21.1.12',port=4242)