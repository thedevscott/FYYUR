# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import json
import datetime
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, \
    url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app, db)


# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    genres = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=True, nullable=False)
    seeking_description = db.Column(db.String(500))
    website = db.Column(db.String(120))
    shows = db.relationship('Show', backref='Venue', lazy=True)


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=True, nullable=False)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship('Show', backref='Artist', lazy=True)


class Show(db.Model):
    __tablename__ = 'Shows'
    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'),
                          nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    results = Venue.query.order_by(Venue.city, Venue.state).all()

    db_data = []
    past_city = []
    past_state = []

    for result in results:
        # pack venue
        if (result.city in past_city) and (result.state in past_state):
            db_data[-1]['venues'].append({
                "id": result.id,
                "name": result.name,
                "num_upcoming_shows": len(result.shows)
            })
        else:
            past_city.append(result.city)
            past_state.append(result.state)
            db_data.append({
                "city": result.city,
                "state": result.state,
                "venues": [{
                    "id": result.id,
                    "name": result.name,
                    "num_upcoming_shows": len(result.shows),
                }]
            })

    return render_template('pages/venues.html', areas=db_data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    response = {
        "count": 0,
        "data": []
    }

    # Get the search term and look it up
    search_term = request.form.get('search_term')
    results = Venue.query.filter(Venue.name.ilike('%' + search_term +
                                                  '%')).all()

    # Process the results
    for result in results:
        data = {
            "id:": result.id,
            "name": result.name,
            "num_upcoming_shows": len(result.shows),
        }
        response["data"].append(data)

    # update the number of search results found
    response["count"] = len(response["data"])

    return render_template('pages/search_venues.html', results=response,
                           search_term=search_term, )


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id

    results = Venue.query.get(venue_id)

    past_shows = []
    upcoming_shows = []

    # pack the show data for the view
    if results.shows:

        for show in results.shows:
            show_pack = {
                "artist_id": show.artist_id,
                "artist_name": show.Artist.name,
                "artist_image_link": show.Artist.image_link,
                "start_time": str(show.start_time)
            }

            # Add shows to list based on start time & current time
            if show.start_time > datetime.now():
                upcoming_shows.append(show_pack)
            else:
                past_shows.append(show_pack)

    db_data = {
        "id": results.id,
        "name": results.name,
        "genres": results.genres.split(','),
        "address": results.address,
        "city": results.city,
        "state": results.state,
        "phone": results.phone,
        "website": results.website,
        "facebook_link": results.facebook_link,
        "seeking_talent": results.seeking_talent,
        "seeking_description": results.seeking_description,
        "image_link": results.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }

    return render_template('pages/show_venue.html', venue=db_data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    try:
        form = VenueForm(request.form)
        if form.validate_on_submit():
            print('valid form')
        else:
            print('invalid')

        venue = Venue(name=request.form['name'],
                      city=request.form['city'],
                      state=request.form['state'],
                      address=request.form['address'],
                      phone=request.form['phone'],
                      genres=','.join(request.form.getlist('genres')),
                      facebook_link=request.form['facebook_link'])

        # on successful db insert, flash success
        db.session.add(venue)
        db.session.commit()

        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred. Venue ' + request.form['name'] +
              ' could not be listed.')
    finally:
        db.session.close()

    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):

    try:
        Venue.query.filter_by(id=venue_id).delete()
        db.session.commit()
        flash('Venue deleted')
    except Exception as e:
        db.session.rollback()
        flash('Unable to delete Venue')
    finally:
        db.session.close()

    return redirect(url_for('index'))


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    db_data = []

    # Pack artists data for view
    for query in Artist.query.all():
        db_data.append({
            "id": query.id,
            "name": query.name,
        })

    return render_template('pages/artists.html', artists=db_data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    response = {
        "count": 0,
        "data": []
    }

    search_term = request.form.get('search_term')
    results = Artist.query.filter(Artist.name.ilike('%' + search_term +
                                                    '%')).all()

    for result in results:
        data = {
            "id:": result.id,
            "name": result.name,
            "num_upcoming_shows": len(result.shows),
        }
        response["data"].append(data)

    # update the number of search results found
    response["count"] = len(response["data"])

    return render_template('pages/search_artists.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artists page with the given artist_id

    artist = Artist.query.get(artist_id)

    past_shows = []
    upcoming_shows = []

    # pack the show data for the view
    if artist.shows:

        for show in artist.shows:
            show_pack = {
                "venue_id": show.venue_id,
                "venue_name": show.Venue.name,
                "venue_image_link": show.Venue.image_link,
                "start_time": str(show.start_time)
            }

            # Add shows to list based on start time & current time
            if show.start_time > datetime.now():
                upcoming_shows.append(show_pack)
            else:
                past_shows.append(show_pack)

    db_data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres.split(','),
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }

    return render_template('pages/show_artist.html', artist=db_data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    db_artist = Artist.query.get(artist_id)
    form = ArtistForm(name=db_artist.name,
                      city=db_artist.city,
                      state=db_artist.state,
                      phone=db_artist.phone,
                      image_link=db_artist.image_link,
                      genres=db_artist.genres.split(','),
                      facebook_link=db_artist.facebook_link)

    return render_template('forms/edit_artist.html', form=form,
                           artist=db_artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    try:
        artist = Artist.query.get(artist_id)

        artist.name = request.form['name']
        artist.city = request.form['city']
        artist.state = request.form['state']
        artist.phone = request.form['phone']
        artist.genres = ','.join(request.form.getlist('genres'))
        artist.facebook_link = request.form['facebook_link']

        db.session.commit()
        flash('Successfully updated Artist ' + request.form['name'])
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while updating the Artist. {}'.format(e))
    finally:
        db.session.close()

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    db_venue = Venue.query.get(venue_id)
    form = VenueForm(name=db_venue.name,
                     genres=db_venue.genres.split(','),
                     address=db_venue.address,
                     city=db_venue.city,
                     state=db_venue.state,
                     phone=db_venue.phone,
                     facebook_link=db_venue.facebook_link,
                     image_link=db_venue.image_link)

    return render_template('forms/edit_venue.html', form=form, venue=db_venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    try:
        venue = Venue.query.get(venue_id)

        venue.name = request.form['name']
        venue.city = request.form['city']
        venue.state = request.form['state']
        venue.phone = request.form['phone']
        venue.address = request.form['address']
        venue.genres = ','.join(request.form.getlist('genres'))
        venue.facebook_link = request.form['facebook_link']

        db.session.commit()
        flash('Successfully updated Venue ' + request.form['name'])
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while updating the Venue. {}'.format(e))
    finally:
        db.session.close()

    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form

    try:
        artist = Artist(name=request.form['name'],
                        city=request.form['city'],
                        state=request.form['state'],
                        phone=request.form['phone'],
                        genres=','.join(request.form.getlist('genres')),
                        facebook_link=request.form['facebook_link'])
        db.session.add(artist)
        db.session.commit()

        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except Exception as e:
        flash('An error occurred. Artist ' + request.form['name'] +
              ' could not be listed.')
    finally:
        db.session.close()

    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    db_data = []

    # Package the data for the view by adding dict for each query to list
    for query in Show.query.all():
        db_data.append({
            "venue_id": query.venue_id,
            "venue_name": query.Venue.name,
            "artist_id": query.artist_id,
            "artist_name": query.Artist.name,
            "artist_image_link": query.Artist.image_link,
            "start_time": str(query.start_time)
        })
    return render_template('pages/shows.html', shows=db_data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form

    try:
        show = Show(artist_id=request.form['artist_id'],
                    venue_id=request.form['venue_id'],
                    start_time=request.form['start_time'])

        db.session.add(show)
        db.session.commit()

        # on successful db insert, flash success
        flash('Show was successfully listed!')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred. Show could not be listed.')
    finally:
        db.session.close()

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
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run(debug=True)

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
