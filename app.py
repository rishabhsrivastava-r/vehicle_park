import os
from flask import Flask, render_template, session, flash, redirect, url_for
from models.dtabse_define_stuffs import db, create_default_admin
from controllers.admin_cont_stuffs import admin_blp
from controllers.user_cont_stuffs import user_bllp
from dotenv import load_dotenv


load_dotenv()
print("DB URI loaded:", os.getenv("DATABASE_URI"))


app = Flask(__name__) #initiliaze hota hai backend..app mera object hai 
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') #fetch from env..used for secrety
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI') #parkingdb changed
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db.init_app(app)


app.register_blueprint(admin_blp, url_prefix='/admin')
app.register_blueprint(user_bllp, url_prefix='/user')

@app.route('/')
def index():
    return render_template('homepage.html')

@app.route('/logout')
def logout():
    session.clear()  #clears token which is givven oonce logged in
    flash('Logged out successfully!', 'success') #success is color-green
    return redirect(url_for('index'))

with app.app_context(): #app start ho to yeh chle
    db.create_all()
    create_default_admin() #defined func

if __name__ == '__main__':
    app.run(debug=True) #gives a generic error if set to false

