#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
import re
import psycopg2
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from operator import itemgetter
from datetime import datetime
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)
# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Genre(db.Model):
    __tablename__ = 'genre'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())

venue_genre_table = db.Table('venue_genre_table',
    db.Column('genre_id', db.Integer, db.ForeignKey('genre.id'), primary_key=True),
    db.Column('venue_id', db.Integer, db.ForeignKey('venue.id'), primary_key=True)
)

artist_genre_table = db.Table('artist_genre_table',
    db.Column('genre_id', db.Integer, db.ForeignKey('genre.id'), primary_key=True),
    db.Column('artist_id', db.Integer, db.ForeignKey('artist.id'), primary_key=True)
)

class Venue(db.Model):
    __tablename__ = 'venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.relationship('Genre', secondary=venue_genre_table, backref=db.backref ('venues', lazy=True))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(120))
    shows =  db.relationship('Show', backref='venue', lazy=True)





    def __repr__(self):
        return f'<venue {self.id} {self.name}>'

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.relationship('Genre', secondary=artist_genre_table, backref=db.backref ('artists'))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean,default=False)
    seeking_description = db.Column(db.String(120))
    shows = db.relationship('Show', backref='artist', lazy=True)




    def __repr__(self):
        return f'<artist {self.id} {self.name}>'

class Show(db.Model): #New model for shows
    __tablename__= 'show'

    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'), nullable=False)


    def __repr__(self):
        return f'<show {self.id} {self.start_time} artist_id={artist_id} venue_id={venue_id}>'



#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    venues=Venue.query.all()
    data=[]

    cities_states = set()
    for venue in venues:
        cities_states.add((venue.city, venue.state))

    cities_states=list(cities_states)
    cities_states.sort(key=itemgetter(1,0))
    for loc in cities_states:
        venues_list=[]
        for venue in venues:
            if (venue.city == loc[0]) and (venue.state == loc[1]):
                venue_shows = Show.query.filter_by(venue_id=venue.id).all()

                venues_list.append({

                    "id": venue.id,
                    "name": venue.name,

                })
        data.append({

            "city" :loc[0],
            "state": loc[1],
            "venues": venues_list

        })

    return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_term = request.form.get('search_term', '').strip()

    venues=Venue.query.filter(Venue.name.ilike('%' + search_term + '%')).all()
    venue_list = []
    for venue in venues:
        venue_list.append({
            "id": venue.id,
            "name": venue.name

        })
    response ={
    "count": len(venues),
    "data": venue_list
    }
    return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

    venue=Venue.query.get(venue_id)

    if not venue:
        return redirect(url_for ('index'))

    else:
        genres=[ genre.name for genre in venue.genres] #list of venue Genres

        upcoming_shows=[]
        upcoming_shows_count=0
        past_shows=[]
        past_shows_count=0

        now=datetime.now()

        for show in venue.shows:
            if show.start_time > now:

                upcoming_shows_count += 1
                upcoming_shows.append({
                    "artist_id" : show.artist.id,
                    "artist_name" : show.artist.name,
                    "artist_image_link" : show.artist.image_link,
                    "start_time" : format_datetime(str(show.start_time))

            })
            if show.start_time < now:

                past_shows_count += 1
                past_shows.append({
                    "artist_id" : show.artist.id,
                    "artist_name" : show.artist.name,
                    "artist_image_link" : show.artist.image_link,
                    "start_time" : format_datetime(str(show.start_time))

            })
        data={

        "id": venue_id,
        "name": venue.name,
        "genres": genres,
        "city": venue.city,
        "address": venue.address,
        "state": venue.state,
        "phone": (venue.phone[:3] + '-' + venue.phone[3:6] + '-' + venue.phone[6:]),
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_venue": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": past_shows,
        "past_shows_count": past_shows_count,
        "upcoming_shows": upcoming_shows,
        "upcoming_shows_count": upcoming_shows_count
        }





    #data = list(filter(lambda d: d['id'] == venue_id
    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    form = VenueForm(request.form, meta={"csrf": False})

    name = form.name.data.strip()
    city = form.city.data.strip()
    state = form.state.data
    address = form.address.data.strip()
    phone = form.phone.data
    phone = re.sub('\D', '', phone)
    genres = form.genres.data
    seeking_talent = True if form.seeking_talent.data== 'Yes' else False
    seeking_description = form.seeking_description.data.strip()
    image_link = form.image_link.data.strip()
    website = form.website.data.strip()
    facebook_link = form.facebook_link.data.strip()

    if not form.validate():
        flash(form.errors)
        return redirect(url_for('create_venue_submission'))

    else:
        insert_error = False

        try:
            new_venue = Venue(name=name, city=city, state=state, address=address,
            phone=phone, seeking_talent=seeking_talent, seeking_description=seeking_description,
            image_link=image_link, website=website, facebook_link=facebook_link)

            for genre in genres:
                get_genre = Genre.query.filter_by(name=genre).one_or_none()
                if get_genre:
                    new_venue.genres.append(get_genre)

                else:
                    add_genre = Genre(name=genre)
                    db.session.add(add_genre)
                    new_venue.genres.append(add_genre)

            db.session.add(new_venue)
            db.session.commit()

        except Exception as e:
            insert_error = True
            print(f'Exception "{e}" in create_venue_submission()')
            db.session.rollback()
        finally:
            db.session.close()

        if not insert_error:
            flash('Venue ' + request.form['name'] + ' was successfully listed!')
            return redirect(url_for('index'))
            #return render_template('pages/home.html')

        else:
            flash('Oops, something went wrong. Venue ' + name + ' could not be listed!')
            print("Error in create_venue_submission()")
            abort(500)







  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    artists=Artist.query.order_by(Artist.name).all()
    data=[]
    for artist in artists:
        data.append({
        "id": artist.id,
        "name": artist.name
        })


    return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_term = request.form.get('search_term', '').strip()

    artists=Artist.query.filter(Artist.name.ilike('%' + search_term + '%')).all()
    artist_list = []
    for artist in artists:
        artist_list.append({
            "id": artist.id,
            "name": artist.name

        })
    response ={
    "count": len(artists),
    "data": artist_list
    }
    return render_template('pages/search_artists.html', results=response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):

    artist = Artist.query.get(artist_id)

    if not artist:
        return redirect(url_for ('index'))

    else:
        genres= [ genre.name for genre in artist.genres] #make a list of artist genres

        upcoming_shows=[]
        upcoming_shows_count=0
        past_shows=[]
        past_shows_count=0

        now=datetime.now()
        for show in artist.shows:
            if show.start_time > now:
                upcoming_shows_count += 1
                upcoming_shows.append({
                    "venue_id": show.venue.id,
                    "venue_name": show.venue.name,
                    "venue_image_link": show.venue.image_link,
                    "start_time": format_datetime(str(show.start_time))

                })

            if show.start_time < now:
                past_shows_count += 1
                past_shows.append({
                    "venue_id": show.venue.id,
                    "venue_name": show.venue.name,
                    "venue_image_link": show.venue.image_link,
                    "start_time": format_datetime(str(show.start_time))
                })
        data= {
            "id": artist_id,
            "name": artist.name,
            "genres": genres,
            "city": artist.city,
            "state": artist.state,
            "phone": (artist.phone[:3] + '-' + artist.phone[3:6] + '-' + artist.phone[6:]),
            "website": artist.website,
            "facebook_link": artist.facebook_link,
            "seeking_venue": artist.seeking_venue,
            "seeking_description": artist.seeking_description,
            "image_link": artist.image_link,
            "past_shows": past_shows,
            "past_shows_count": past_shows_count,
            "upcoming_shows": upcoming_shows,
            "upcoming_shows_count": upcoming_shows_count


        }




    return render_template('pages/show_artist.html', artist=data)




  #data = list(filter(lambda d: d['id'] == artist_id, [data1, data2, data3]))[0]


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist={
    "id": 4,
    "name": "Guns N Petals",
    "genres": ["Rock n Roll"],
    "city": "San Francisco",
    "state": "CA",
    "phone": "326-123-5000",
    "website": "https://www.gunsnpetalsband.com",
    "facebook_link": "https://www.facebook.com/GunsNPetals",
    "seeking_venue": True,
    "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
    "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
  }
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):

    venue=Venue.query.get(venue_id)

    if not venue:
        return redirect(url_for ('index'))
    else:
        form=VenueForm(obj=venue)

    genres= [ genre.name for genre in venue.genres ]

    venue = {

        "id": venue.id,
        "name": venue.name,
        "genres": genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": (venue.phone[:3] + '-' + venue.phone[3:6] + '-' + venue.phone[6:]),
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link
    }
    return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    form = VenueForm(request.form, meta={"csrf": False})

    name = form.name.data.strip()
    city = form.city.data.strip()
    state = form.state.data
    address = form.address.data.strip()
    phone = form.phone.data
    phone = re.sub('\D', '', phone)
    genres = form.genres.data
    seeking_talent = True if form.seeking_talent.data== 'Yes' else False
    seeking_description = form.seeking_description.data.strip()
    image_link = form.image_link.data.strip()
    website = form.website.data.strip()
    facebook_link = form.facebook_link.data.strip()

    if not form.validate():
        flash(form.errors)
        return redirect(url_for('edit_venue_submission', venue_id=venue_id))

    else:
        update_error = False
        try:
            venue=Venue.query.get(venue_id)


            venue.genres = []
            for genre in genres:
                get_genre = Genre.query.filter_by(name=genre).one_or_none()
                if get_genre:
                    venue.genres.append(get_genre)

                else:
                    add_genre = Genre(name=genre)
                    db.session.add(add_genre)
                    venue.genres.append(add_genre)


            venue.name = name
            venue.city = city
            venue.state = state
            venue.address = address
            venue.phone = phone
            venue.seeking_talent = seeking_talent
            venue.seeking_description = seeking_description
            venue.image_link = image_link
            venue.facebook_link = facebook_link
            venue.website = website

            db.session.commit()
        except Exception as e:
            update_error = True
            print(f'Exception "e" in edit_venue_submission()')
            db.session.rollback
        finally:
            db.session.close()
        if not update_error:
            flash('Update on venue ' + request.form['name'] + ' was successful')
            return redirect(url_for('show_venue', venue_id=venue_id))
        else:
            flash('There was an error and venue ' + name + 'was not updated.')
            print("Error in edit_venue_submission()")
            abort(500)


        return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():

     form = ArtistForm(request.form, meta={"csrf": False})

     name = form.name.data.strip()
     city = form.city.data.strip()
     state = form.state.data
     phone = form.phone.data
     phone = re.sub('\D', '', phone)
     genres = form.genres.data
     seeking_venue = True if form.seeking_venue.data== 'Yes' else False
     seeking_description = form.seeking_description.data.strip()
     image_link = form.image_link.data.strip()
     website = form.website.data.strip()
     facebook_link = form.facebook_link.data.strip()

     if not form.validate():
         flash(form.errors)
         return redirect(url_for('create_artist_submission'))

     else:
         insert_error = False

         try:
             new_artist = Artist(name=name, city=city, state=state,
             phone=phone, seeking_venue=seeking_venue, seeking_description=seeking_description,
             image_link=image_link, website=website, facebook_link=facebook_link)

             for genre in genres:
                 get_genre = Genre.query.filter_by(name=genre).one_or_none()
                 if get_genre:
                     new_artist.genres.append(get_genre)

                 else:
                     add_genre = Genre(name=genre)
                     db.session.add(add_genre)
                     new_artist.genres.append(add_genre)

             db.session.add(new_artist)
             db.session.commit()

         except Exception as e:
             insert_error = True
             print(f'Exception "{e}" in create_artist_submission()')
             db.session.rollback()
         finally:
             db.session.close()

         if not insert_error:
             flash('Artist ' + request.form['name'] + ' was successfully listed!')
             return redirect(url_for('index'))
             #return render_template('pages/home.html')

         else:
             flash('Oops, something went wrong. Artist ' + name + ' could not be listed!')
             print("Error in create_artist_submission()")
             abort(500)
             #return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    data=[]
    shows = Show.query.all()

    for show in shows:
        data.append({
            "venue_id": show.venue.id,
            "venue_name": show.venue.name,
            "artist_id": show.artist.id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": format_datetime(str(show.start_time))



        })


    return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():

    form= ShowForm()

    artist_id = form.artist_id.data.strip()
    venue_id = form.venue_id.data.strip()
    start_time = form.start_time.data

    insert_error=False


    try:
        new_show = Show(start_time=start_time, artist_id=artist_id, venue_id=venue_id)
        db.session.add(new_show)
        db.session.commit()
    except:
        insert_error=true
        print(f'Exception "{e}" in create_show_submission')
        db.session.rollback()
    finally:
        db.session.close()
    if insert_error:
        flash(f' An error occurred. Show has not been listed')
        print("Error in create_show_submission")
    else:
        flash(f' Show has been successfully listed')

    return render_template('pages/home.html')





  # on successful db insert, flash success
  #flash('Show was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
