from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField, IntegerField, URLField
from wtforms.validators import DataRequired
import requests


movie_db_api_key = '1fc7b54e53db59ca1c615dbccf8e07cc'

api_url = "https://api.themoviedb.org/3/search/movie"
api_id_url = "https://api.themoviedb.org/3/movie"


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///top10-movies.db'
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
Bootstrap(app)


class EditForm(FlaskForm):
    rating = FloatField('Your Rating out of 10', validators=[DataRequired()])
    review = StringField('Your Review', validators=[DataRequired()])
    submit = SubmitField('Done')


class NewMovie(FlaskForm):
    new_movie = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField('Add Movie')


class Movies(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(40), unique=True, nullable=False)
    year = db.Column(db.Integer, unique=True, nullable=False)
    description = db.Column(db.String(280), unique=True, nullable=False)
    rating = db.Column(db.Float, nullable=False)
    ranking = db.Column(db.Integer)
    review = db.Column(db.String(50), nullable=False)
    img_url = db.Column(db.String(150), nullable=False)


db.create_all()

# movie_entry = Movies(title="Phone Booth", year=2002, description="Publicist Stuart Shepard finds himself trapped "
#             "in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, "
#             "Stuart's negotiation with the caller leads to a jaw-dropping climax.", rating=7.3, ranking=10,
#                      review="My favourite character was the caller.",
#                      img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg")
#
# db.session.add(movie_entry)
# db.session.commit()
#
# movie=Movies.query.all()


@app.route("/")
def home():
    movies = Movies.query.order_by(Movies.rating.desc())
    n = 1
    for movie in movies:
        movie.ranking = n
        n += 1
        db.session.commit()
    return render_template("index.html", movies=Movies.query.order_by(Movies.rating.desc()))


# Option1: Extracting the parameter from the URL and passing it to the function below

# @app.route("/edit/<id_para>", methods=['GET', 'POST'])
# def edit(id_para):
#     form=EditForm()
#     movie_to_update = Movies.query.filter_by(id=id_para).first()
#     if form.validate_on_submit():
#         movie_to_update.rating = form.rating.data
#         movie_to_update.review = form.review.data
#         db.session.commit()
#         return redirect(url_for('home'))
#     return render_template('edit.html', form=form, movie=movie_to_update)


# Option2: Using the request.args.get() method to get the parameter passed while building the URL
@app.route("/edit", methods=['GET', 'POST'])
def edit():
    form=EditForm()
    movie_id=request.args.get('id')
    movie_to_update = Movies.query.filter_by(id=movie_id).first()
    if form.validate_on_submit():
        movie_to_update.rating = form.rating.data
        movie_to_update.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit.html', form=form, movie=movie_to_update)


# Option 2: Using the request.args.get() method to get the parameter passed while building the URL
@app.route("/delete", methods=['GET', 'POST'])
def delete():
    movie_id = request.args.get("id")
    movie_to_delete = Movies.query.filter_by(id=movie_id).first()
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/add', methods=['POST', 'GET'])
def add():
    form = NewMovie()

    if form.validate_on_submit():
        movie_to_add = form.new_movie.data

        movie_params = {
            'api_key': movie_db_api_key,
            'query': movie_to_add
        }

        response = requests.get(api_url, params=movie_params)
        return render_template('select.html', movies_dump=response.json())

    return render_template('add.html', form=form)


@app.route('/select', methods=['GET', 'POST'])
def select():
    selected_id = request.args.get('id')
    print(selected_id)

    movie_params = {
        'api_key': movie_db_api_key
    }

    api_id_url_final = f"{api_id_url}/{selected_id}"

    response = requests.get(api_id_url_final, params=movie_params)
    selected_movie = response.json()

    selected_title = selected_movie['title']
    selected_url = f"https://image.tmdb.org/t/p/w500{selected_movie['poster_path']}"
    selected_year = selected_movie['release_date']
    selected_description = selected_movie['overview']

    movie_entry = Movies(title=selected_title, year=selected_year, description=selected_description, rating=0, ranking=0,
                         review="None", img_url=selected_url)

    db.session.add(movie_entry)
    db.session.commit()

    movie_to_update = Movies.query.filter_by(title=selected_title).first()

    return redirect(url_for('edit', id=movie_to_update.id))


if __name__ == '__main__':
    app.run(debug=True)
