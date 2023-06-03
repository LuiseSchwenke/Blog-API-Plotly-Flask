from flask import Flask, abort, render_template, g, redirect, url_for, request, flash, send_from_directory
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, PasswordField
from wtforms.validators import DataRequired, URL
from bs4 import BeautifulSoup
import requests
from datetime import date, datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from functools import wraps

from geopy.geocoders import Nominatim
import arrow
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly
import plotly.graph_objects as go
from tabulate import tabulate
import chart_studio.tools as tls

import pycountry
import plotly.express as px

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'

Bootstrap(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fullelassurfam.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

response = requests.get("https://www.worldsurfleague.com/athletes/rankings")
yc_response = response.text
soup = BeautifulSoup(yc_response, "html.parser")

response_two = requests.get("https://www.worldsurfleague.com/events?all=1&year=2023")
response_two = response_two.text
soup_two = BeautifulSoup(response_two, "html.parser")


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id != 2:
            return abort(403)
        return f(*args, **kwargs)

    return decorated_function


with app.app_context():
    class BlogPost(db.Model):
        __tablename__ = "blog_posts"
        id = db.Column(db.Integer, primary_key=True)
        author_id = db.Column(db.Integer, db.ForeignKey('users.id'))

        name_beach = db.Column(db.String(250), nullable=False)
        city = db.Column(db.String(250), nullable=False)
        country = db.Column(db.String(250), nullable=False)
        continent = db.Column(db.String(250), nullable=False)
        maps_url = db.Column(db.String(250), nullable=False)
        access = db.Column(db.String(250), nullable=False)
        clima = db.Column(db.String(250), nullable=False)
        wave_quality = db.Column(db.Text, nullable=False)
        infos = db.Column(db.Text, nullable=False)
        img_url = db.Column(db.String(250), nullable=False)
        author = relationship("User", back_populates="posts")
        date = db.Column(db.String(250), nullable=False)
        comments = relationship("Comment", back_populates="parent_post")


    class User(UserMixin, db.Model):
        __tablename__ = 'users'
        id = db.Column(db.Integer, primary_key=True)
        password = db.Column(db.String(100))
        name = db.Column(db.String(1000))
        posts = relationship("BlogPost", back_populates="author")
        comments = relationship("Comment", back_populates="comment_author")


    class Comment(db.Model):
        __tablename__ = 'comments'
        id = db.Column(db.Integer, primary_key=True)
        text = db.Column(db.Text, nullable=False)
        author_id = db.Column(db.Integer, db.ForeignKey('users.id'))

        comment_author = relationship("User", back_populates="comments")
        post_id = db.Column(db.Integer, db.ForeignKey('blog_posts.id'))
        parent_post = relationship("BlogPost", back_populates="comments")


    db.create_all()


class RegisterForm(FlaskForm):
    name = StringField("Create a Name", validators=[DataRequired()])
    password = PasswordField("Create a Password", validators=[DataRequired()])
    submit = SubmitField("Register")


class LoginForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


@app.route('/', methods=['GET', 'POST'])
def home():
    post = BlogPost.query.get(1)
    url_of_img_one = post.img_url
    beach_name_one = post.name_beach
    country_one = post.country
    clima_one = post.clima

    post = BlogPost.query.get(2)
    url_of_img_two = post.img_url
    beach_name_two = post.name_beach
    country_two = post.country
    clima_two = post.clima

    # post_id_three = 3
    # post = BlogPost.query.get(post_id_three)
    # url_of_img_three = post.img_url
    # beach_name_one = post.name_beach
    # country_one = post.country
    # clima_one = post.clima
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(name=form.name.data).first():
            flash("This name already exists, please choose a different one")
            return redirect(url_for("home"))
        else:
            hash_and_salted_pw = generate_password_hash(request.form.get("password"),
                                                        method="pbkdf2:sha256",
                                                        salt_length=8)
            new_user = User(
                password=hash_and_salted_pw,
                name=form.name.data,
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            flash('You were successfully registered')
            return redirect(url_for('home'))
    formtwo = LoginForm()
    if request.method == 'POST':
        name = request.formtwo.get("name")
        password = request.formtwo.get("password")
        user = User.query.filter_by(name=name).first()
        if not user:
            flash("Sorry, please sign in first, your profile hasn't been created yet")
            return redirect(url_for("home"))
        elif not check_password_hash(user.password, password):
            flash("Wrong Password")
            return redirect(url_for("home"))
        else:
            login_user(user)
            return redirect(url_for("home"))
    return render_template("index.html", form=form, formtwo=formtwo, current_user=current_user, first_img=url_of_img_one,
                           second_img=url_of_img_two,
                           first_beach=beach_name_one, second_beach=beach_name_two,
                           county_one=country_one, country_two=country_two, clima_one=clima_one, clima_two=clima_two)


@app.route('/about')
def about():
    return render_template("about.html")


@app.route('/lifestyle')
def lifestyle():
    return render_template("lifestyle.html")


@app.route('/news', methods=['GET', 'POST'])
def news():
    date_today = date.today()
    today = date_today.strftime("%d/%m/%Y")
    all_ranks = [title.getText() for title in soup.find_all(name="span", class_="athlete-rank")]
    all_names = [title.getText() for title in soup.find_all(name="a", class_="athlete-name")]
    all_countries = [title.getText() for title in soup.find_all(name="span", class_="athlete-country-name")]
    all_points = [title.getText() for title in soup.find_all(name="span", class_="athlete-points")]
    all_data = {
        'ranks': all_ranks,
        'names': all_names,
        'countries': all_countries,
        'points': all_points,
    }

    data_one = [elem for elem in all_data.values()]

    all_infos = [title.getText() for title in soup_two.find_all(name="span", class_="event-status")]
    date_range = [info.getText() for info in soup_two.find_all(name="td", class_="event-date-range")]
    events = [info.getText() for info in soup_two.find_all(name="a", class_="event-schedule-details__event-name")]
    location = [info.getText() for info in soup_two.find_all(name="span", class_="event-schedule-details__location")]
    tour = [info.getText() for info in soup_two.find_all(name="span", class_="event-tour-details__tour-name")]

    data_dict = {
        'dates': [],
        'event_name': [],
        'location': [],
        'tour': [],
    }
    list = []
    for index, info in enumerate(all_infos):
        if info == "Upcoming" or info == "Tentative":
            for num, info_date in enumerate(date_range):
                info = info_date
                if index == num:
                    data_dict["dates"] = info
            for num, info_event in enumerate(events):
                info_event = info_event
                if index == num:
                    data_dict["event_name"] = info_event
            for num, info_loc in enumerate(location):
                info_loc = info_loc
                if index == num:
                    data_dict["location"] = info_loc
            for num, info_tour in enumerate(tour):
                info_tour = info_tour
                if index == num:
                    data_dict["tour"] = info_tour

            data = [elem for elem in data_dict.values()]
            list.append(data)

    return render_template("news.html", data=data_one, tours=list, today=today)


@app.route('/flat_days')
def flat_days():
    return render_template("flat_days.html")


@app.route('/best_spots', methods=['GET', 'POST'])
def best_spots():
    DBcountries = []
    countries={}
    posts = BlogPost.query.all()
    for post in posts:
        country = post.country
        DBcountries.append(country)
    try:
        for country in pycountry.countries:
            countries[country.name] = country.alpha_2
        codes = [countries.get(country, 'Unknown code') for country in DBcountries]
        print(codes)

        # ------- for blog: countries + count number of blog posts countries to make that count the colorscale
        world_map = px.choropleth(codes,
                                  locations=codes,
                                  color='blue',
                                  color_continuous_scale=px.colors.sequential.matter,

                                  )

        world_map.write_image(file='static/images/worldmap.png', format='png')

    except:
        flash("Something went wrong")

    API_KEY = "AIzaSyBi8kM7dFLb10AxhKxgneOOM-XA0RQWzI4"

    return render_template("best_spots.html", all_posts=posts, api=API_KEY, current_user=current_user)












class SpotForm(FlaskForm):
    name_beach = StringField("Name of the Beach", validators=[DataRequired()])
    city = StringField("City in wich the beach is located", validators=[DataRequired()])
    country = StringField("Country", validators=[DataRequired()])
    continent = StringField("Continent", validators=[DataRequired()])
    access = StringField("Access to the beach", validators=[DataRequired()])
    clima = StringField("Vibe at the spot", validators=[DataRequired()])
    wave_quality = StringField("Quality of the waves...", validators=[DataRequired()])
    img_url = StringField("Image URL of the Spot", validators=[DataRequired(), URL()])
    maps_url = StringField("Maps URL of the Spot", validators=[DataRequired(), URL()])
    infos = StringField("Any further Infos...", validators=[DataRequired()])
    submit = SubmitField("Add The Spot")


@app.route('/new_spot', methods=['GET', 'POST'])
@admin_only
def new_spot():
    try:
        form = SpotForm()
        if form.validate_on_submit():
            with app.app_context():
                new_post = BlogPost(
                    name_beach=form.name_beach.data,
                    city=form.city.data,
                    country=form.country.data,
                    continent=form.continent.data,
                    access=form.access.data,
                    clima=form.clima.data,
                    wave_quality=form.wave_quality.data,
                    infos=form.infos.data,
                    img_url=form.img_url.data,
                    maps_url=form.maps_url.data,
                    author=current_user,
                    date=date.today()
                )
            db.session.add(new_post)
            db.session.commit()
            return redirect(url_for("best_spots"))
        return render_template("new_spot.html", form=form)
    except:
        flash("Log in first, to contribute a new Surfspot to the blog.")
        redirect(url_for("best_spots"))


@app.route("/edit_post/<post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = SpotForm(
        city=post.city,
        country=post.country,
        continent=post.continent,
        access=post.access,
        clima=post.clima,
        wave_quality=post.wave_quality,
        infos=post.infos,
        img_url=post.img_url,
        maps_url=post.maps_url,
        author=current_user,
        date=date.today()
    )

    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.author = edit_form.author.data
        post.img_url = edit_form.img_url.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for('best_spots', post_id=post.id))

    return render_template("new_spot.html", form=edit_form, is_edit=True, current_user=current_user)


@app.route("/delete/<int:post_id>", methods=['GET', 'POST'])
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('best_spots'))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


class FCForm(FlaskForm):
    name = StringField("Name of the beach or city", validators=[DataRequired()])
    submit = SubmitField("Search forecast")


@app.route('/forecast', methods=['GET', 'POST'])
def forecast():
    form = FCForm()
    if form.validate_on_submit():
        geolocator = Nominatim(user_agent="MyApp")
        API_KEY_RL = "722af78a-fd26-11ed-a654-0242ac130002-722af7f8-fd26-11ed-a654-0242ac130002"
        API_KEY_OIBR = "a2c8291e-ffd6-11ed-a654-0242ac130002-a2c829dc-ffd6-11ed-a654-0242ac130002"
        API_KEY_LSC = "4203370e-ffdb-11ed-a654-0242ac130002-420337ae-ffdb-11ed-a654-0242ac130002"

        location = geolocator.geocode(form.name.data)

        lat = location.latitude
        lon = location.longitude
        start = arrow.now().floor('day')
        end = arrow.now().ceil('day')
        try:
            response = requests.get('https://api.stormglass.io/v2/weather/point',
                                    params={
                                        'lat': lat,
                                        'lng': lon,
                                        'params': ','.join(
                                            ['windSpeed', 'windDirection', 'airTemperature', 'waterTemperature', 'seaLevel'
                                                , 'swellHeight', 'waveDirection', 'waveHeight', 'wavePeriod',
                                             'currentDirection', 'currentSpeed']),
                                        'start': start.to('UTC').timestamp(),
                                        'end': end.to('UTC').timestamp()

                                    },
                                    headers={'Authorization': API_KEY_LSC}
                                    )

            data = response.json()
            real_data = data['hours']

            data_output = []
            for hour in real_data:
                data_output.append({'time': hour['time'],
                                    'air_temp': hour['airTemperature']['noaa'],
                                    'water_temp': hour['waterTemperature']['noaa'],
                                    'current_dir': hour['currentDirection']['meto'],
                                    'current_speed': hour['currentSpeed']['meto'],
                                    'sea_lvl': hour['seaLevel']['meto'],
                                    'swell_height': hour['swellHeight']['meteo'],
                                    'wave_dir': hour['waveDirection']['meteo'],
                                    'wave_hei': hour['waveHeight']['meteo'],
                                    'wave_per': hour['wavePeriod']['meteo'],
                                    'wind_dir': hour['windDirection']['noaa'],
                                    'wind_speed ': hour['windSpeed']['noaa'],

                                    })

            new_df = pd.DataFrame(data_output)
            new_df.to_csv('new_file.csv')

            df = pd.read_csv('new_file.csv')
            df.time = pd.to_datetime(df.time)

            wave_height_dif = df.wave_hei - df.swell_height
            df['wave_height_dif'] = wave_height_dif

            df['hour'] = df['time'].dt.hour

            utc_dt = datetime.now(timezone.utc)
            local_time = utc_dt.astimezone().isoformat()
            hours = local_time.split('.')[0]
            today = datetime.strptime(hours, '%Y-%m-%dT%H:%M:%S').date()
            now = datetime.strptime(hours, '%Y-%m-%dT%H:%M:%S').hour

            fig = go.Figure(go.Bar(x=df.hour, y=df.swell_height, name='Swell height', text=df.swell_height,
                                   textangle=0, textfont_color="red",
                                   marker=dict(color=df.current_dir, colorscale='inferno')),
                            layout=go.Layout(height=800, width=1000))
            fig.add_trace(go.Bar(x=df.hour, y=wave_height_dif, name='Max wave height',
                                 text=df.wave_hei, textangle=0, textfont_color="blue",
                                 marker=dict(color=df.current_dir, colorscale='inferno', showscale=True)))
            fig.add_vline(x=now, line_width=1, line_color="red", name='current hour', annotation_text="current hour")

            fig.update_layout(
                title_text=f"Wave Heights on {today} at {location}",
                barmode='stack',
                yaxis={'title': 'Wave Height [m]'},
                xaxis={'type': 'category',
                       'title': 'Time [h]',
                       },
                title_font_size=30,
                yaxis_range=[0, 4],

            )
            fig.write_image(file='static/images/new_plot.png', format='png')
            water_temp = df["water_temp"].mean()
            air_temp_2 = df.loc[df['hour'] == 12, 'air_temp']
            return render_template("FCPlot.html", water_temp=water_temp, air_temp_2=air_temp_2)
        except KeyError:
            flash("Please choose a city, that is located on a beach.")

    return render_template("forecast.html", form=form)


if __name__ == "__main__":
    app.run(debug=True)
