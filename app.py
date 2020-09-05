#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import sys

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app,db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500), nullable=True)
    website = db.Column(db.String(150), nullable=True)
    facebook_link = db.Column(db.String(120), nullable=False)
    seeking_talent = db.Column(db.Boolean, nullable=True,default=False)
    seeking_description = db.Column(db.String(), nullable=True,default="")
    genres = db.Column(db.ARRAY(db.String()),nullable=False,server_default="{}")

    def __repr__(self):
      return f'<Venue {self.id} {self.name}>'

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    genres = db.Column(db.ARRAY(db.String()),nullable=False,server_default="{}")
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500), nullable=True)
    facebook_link = db.Column(db.String(120), nullable=False)
    website = db.Column(db.String(150), nullable=False)
    seeking_venue = db.Column(db.Boolean, nullable=True,default=False)
    seeking_description = db.Column(db.String(1000), nullable=True)

    def __repr__(self):
      return f'<Artist {self.id} {self.name}>'
    # TODO: implement any missing fields, as a database migration using Flask-Migrate

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues Endpoints for CRUD Methods
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  venues = Venue.query.order_by(Venue.city,Venue.state).all()
  data = []
  for venue in venues:
    foundLocation = False
    for location in data:
      if location.city == venue.city and location.state == venue.state:
        newVenue = {
          "id": venue.id,
          "name": venue.name,
          "num_upcoming_shows":0,
        }
        location.venues.append(newVenue)
        foundLocation = True
    if foundLocation == False:
      newVenue = {
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows":0,
      }
      newLocation = {
        "city":venue.city,
        "state": venue.state,
        "venues":[newVenue],
      }
      data.append(newLocation)
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # seach for venues with column Name containing word in "sear_term" 
  search_term = request.form['search_term']
  search = f'%{search_term}%'
  venues = Venue.query.filter(Venue.name.ilike(search)).all()
  
  response={
    "count": len(venues),
    "data": [],
  }

  for venue in venues:
    newItem = {
      "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows": 0,
    }
    response['data'].append(newItem)

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  venue = Venue.query.filter_by(id = venue_id).first()
  if venue is None:
    flash(f'An error occurred. Venue with ID= {venue_id} does not exist.')
    return render_template('pages/home.html')
  else:
    return render_template('pages/show_venue.html', venue=venue)

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  error = False
  idToreturn = 1
  try:
    venueDict = request.form
    name = venueDict['name']
    city = venueDict['city']
    state = venueDict['state']
    address= venueDict['address']
    phone = venueDict['phone']
    genresList = venueDict.getlist('genres')
    facebookLink = venueDict['facebook_link']
    imageLink = venueDict['image_link']
    venueToAdd = Venue(name=name,city=city,state=state,address=address,phone=phone,genres=genresList,facebook_link=facebookLink,image_link=imageLink)
    db.session.add(venueToAdd)
    db.session.commit()
    idToreturn = venueToAdd.id
  except:
    db.session.rollback()
    error=True
    print(sys.exc_info())
  finally:
    db.session.close()
  
  if error:
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
    return render_template('pages/home.html')
  else:
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
    return redirect(url_for('show_venue',venue_id=idToreturn)) 

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.filter_by(id = venue_id).first()
  if venue is None:
    flash(f'An error occurred. Venue with ID= {venue_id} does not exist.')
    return render_template('pages/home.html')
  else:
    return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  error = False
  try:
    venueDict = request.form
    venue = Venue.query.get(venue_id)
    venue.name = venueDict['name']
    venue.city = venueDict['city']
    venue.state = venueDict['state']
    venue.address= venueDict['address']
    venue.phone = venueDict['phone']
    venue.genres = venueDict.getlist('genres')
    venue.facebook_Link = venueDict['facebook_link']
    venue.image_link = venueDict['image_link']
    db.session.commit()
  except:
    db.session.rollback()
    error=True
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash(f'An error occurred. Venue with ID = {venue_id} could not be updated.')
    return render_template('pages/home.html')
  else:
    flash(f'Venue with ID = {venue_id} was successfully updated!')
    return redirect(url_for('show_venue',venue_id=venue_id)) 

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  error = False
  try:
    Venue.query.filter_by(id=venue_id).delete()
    db.session.commit()
  except:
    db.session.rollback()
    error=True
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash(f'An error occurred. Venue with ID = {venue_id} could not be deleted.')
  else:
    flash(f'Venue with ID = {venue_id} was successfully deleted!')
  return render_template('pages/home.html') 

#  Artists Endpoints for CRUD Methods
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # Query all Artist in database
  artists = Artist.query.all()
  data = []
  for artist in artists:
    newArtist = {
      "id": artist.id,
      "name":artist.name,
    }
    data.append(newArtist)
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # seach for venues with column Name containing word in "sear_term" 
  search_term = request.form['search_term']
  search = f'%{search_term}%'
  artists = Artist.query.filter(Artist.name.ilike(search)).all()
  
  response={
    "count": len(artists),
    "data": [],
  }

  for artist in artists:
    newItem = {
      "id": artist.id,
      "name": artist.name,
      "num_upcoming_shows": 0,
    }
    response['data'].append(newItem)
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  artist = Artist.query.filter_by(id = artist_id).first()
  if artist is None:
    flash(f'An error occurred. Artist with ID= {artist_id} does not exist.')
    return render_template('pages/home.html')
  else:
    return render_template('pages/show_artist.html', artist=artist)

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  error = False
  idToreturn = 1
  try:
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    genresList = request.form.getlist('genres')
    facebookLink = request.form['facebook_link']
    imageLink = request.form['image_link']
    website = request.form['website']
    artist = Artist(name=name,city=city,state=state,phone=phone,genres=genresList,facebook_link=facebookLink,image_link=imageLink,website=website)
    db.session.add(artist)
    db.session.commit()
    idToreturn = artist.id
  except:
    db.session.rollback()
    error=True
    print(sys.exc_info())
  finally:
    db.session.close()
  
  if error:
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
    return render_template('pages/home.html')
  else:
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
    return redirect(url_for('show_artist',artist_id=idToreturn)) 

@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.filter_by(id = artist_id).first()
  if artist is None:
    flash(f'An error occurred. Venue with ID= {artist_id} does not exist.')
    return render_template('pages/home.html')
  else:
    return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # update artist record with ID <artist_id> using the new attributes
  error = False
  try:
    artist = Artist.query.get(artist_id)
    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    artist.genres = request.form.getlist('genres')
    artist.website = request.form['website']
    artist.facebook_Link = request.form['facebook_link']
    artist.image_link = request.form['image_link']
    db.session.commit()
  except:
    db.session.rollback()
    error=True
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash(f'An error occurred. Artist with ID = {artist_id} could not be updated.')
    return render_template('pages/home.html')
  else:
    flash(f'Artist with ID = {artist_id} was successfully updated!')
    return redirect(url_for('show_artist', artist_id=artist_id))


#  Shows Endpoints for CRUD Methods
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  data=[{
    "venue_id": 1,
    "venue_name": "The Musical Hop",
    "artist_id": 4,
    "artist_name": "Guns N Petals",
    "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
    "start_time": "2019-05-21T21:30:00.000Z"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 5,
    "artist_name": "Matt Quevedo",
    "artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
    "start_time": "2019-06-15T23:00:00.000Z"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 6,
    "artist_name": "The Wild Sax Band",
    "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    "start_time": "2035-04-01T20:00:00.000Z"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 6,
    "artist_name": "The Wild Sax Band",
    "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    "start_time": "2035-04-08T20:00:00.000Z"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 6,
    "artist_name": "The Wild Sax Band",
    "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    "start_time": "2035-04-15T20:00:00.000Z"
  }]
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead

  # on successful db insert, flash success
  flash('Show was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

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
