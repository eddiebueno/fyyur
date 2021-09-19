# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import json, sys
import dateutil.parser
import babel
from flask import (
    Flask,
    render_template,
    request,
    Response,
    flash,
    redirect,
    url_for,
    jsonify,
    abort,
)
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from sqlalchemy.dialects.postgresql import ARRAY

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object("config")
db = SQLAlchemy(app)

# connect to a local postgresql database
migrate = Migrate(app, db, compare_type=True)

# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#


class Venue(db.Model):
    __tablename__ = "Venue"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(ARRAY(db.String(120)))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(120))
    shows = db.relationship("Show", backref="venue", cascade="all,delete", lazy=True)

    # implement any missing fields, as a database migration using Flask-Migrate
    def __repr__(self):
        return f"<Venue {self.id} {self.name}>"


class Artist(db.Model):
    __tablename__ = "Artist"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(ARRAY(db.String(120)))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(120))
    shows = db.relationship("Show", backref="artist", cascade="all,delete", lazy=True)

    # implement any missing fields, as a database migration using Flask-Migrate
    def __repr__(self):
        return f"<Artist {self.id} {self.name}>"


# Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
class Show(db.Model):
    __tablename__ = "Show"

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(
        db.Integer, db.ForeignKey("Artist.id", ondelete="CASCADE"), nullable=False
    )
    venue_id = db.Column(
        db.Integer, db.ForeignKey("Venue.id", ondelete="CASCADE"), nullable=False
    )
    start_time = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f"<Show {self.id}: {self.artist_id} playing at {self.venue_id}>"


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#


def format_datetime(value, format="medium"):
    date = dateutil.parser.parse(value)
    if format == "full":
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == "medium":
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale="en")


app.jinja_env.filters["datetime"] = format_datetime

# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@app.route("/")
def index():
    return render_template("pages/home.html")


#  Venues
#  ----------------------------------------------------------------


@app.route("/venues")
def venues():
    data = []

    venues = Venue.query.all()
    venues_locations = set()
        
    # Find unique city and state  for each venue
    for v in venues:
        venues_locations.add((v.city, v.state)) if (v.city, v.state) not in venues_locations

    data = list(data)

    # combine all venues that share the same city and state
    for loc in venues_locations:
        city = loc[0]
        state = loc[1]
        location_venues = []
        for v in venues:
            if v.city == city and v.state == state:
                location_venues.append(v)
        data.append({"city": city, "state": state, "venues": location_venues})
    return render_template("pages/venues.html", areas=data)


@app.route("/venues/search", methods=["POST"])
def search_venues():
    # implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    venues = Venue.query.filter(
        Venue.name.ilike(f"%{request.form.get('search_term')}%")
    ).all()

    response = {
        "count": len(venues),
        "data": venues,
    }

    return render_template(
        "pages/search_venues.html",
        results=response,
        search_term=request.form.get("search_term", ""),
    )


@app.route("/venues/<int:venue_id>")
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # replace with real venue data from the venues table, using venue_id
    now = datetime.now()
    upcoming_shows = (
        Show.query.filter(Show.venue_id == venue_id, Show.start_time > now)
        .join(Artist)
        .all()
    )
    past_shows = (
        Show.query.filter(Show.venue_id == venue_id, Show.start_time < now)
        .join(Artist)
        .all()
    )
    for show in upcoming_shows + past_shows:
        show.start_time = str(show.start_time)
        show.artist_name = show.artist.name
        show.artist_image_link = show.artist.image_link

    data = Venue.query.get(venue_id)
    data.upcoming_shows = upcoming_shows
    data.past_shows = past_shows
    data.upcoming_shows_count = len(upcoming_shows)
    data.past_shows_count = len(past_shows)
    print(data.genres)
    return render_template("pages/show_venue.html", venue=data)


#  Create Venue
#  ----------------------------------------------------------------


@app.route("/venues/create", methods=["GET"])
def create_venue_form():
    form = VenueForm()
    return render_template("forms/new_venue.html", form=form)


@app.route("/venues/create", methods=["POST"])
def create_venue_submission():
    # insert form data as a new Venue record in the db, instead
    # modify data to be the data object returned from db insertion
    data = request.form
    try:
        venue = Venue(
            name=data["name"],
            city=data["city"],
            state=data["state"],
            address=data["address"],
            phone=data["phone"],
            genres=data.getlist("genres"),
            image_link=data["image_link"],
            facebook_link=data["facebook_link"],
            seeking_description=data["seeking_description"],
            seeking_talent=bool(data.get("seeking_talent")),
            website_link=data["website_link"],
        )
        db.session.add(venue)
        db.session.commit()
        # on successful db insert, flash success
        flash("Venue " + venue.name + " was successfully listed!")
    except:
        db.session.rollback()
        # on unsuccessful db insert, flash an error instead.
        flash("An error occurred. Venue " + data["name"] + " could not be listed.")
    finally:
        db.session.close()

    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template("pages/home.html")


@app.route("/venues/<venue_id>", methods=["DELETE"])
def delete_venue(venue_id):
    # Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    venue = Venue.query.get(venue_id)
    redirect_url = url_for("venues")
    error = False
    if not venue:
        return jsonify({"deleted": error, "url": redirect_url})

    try:
        db.session.delete(venue)
        db.session.commit()
    except:
        error = False
        redirect_url = url_for("show_venue", venue_id=venue_id)
        db.session.rollback()
        flash(f"Error occured when deleting venue")
        abort(500)
    finally:
        db.session.close()

    return jsonify({"deleted": error, "url": url_for("venues")})
    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage


#  Artists
#  ----------------------------------------------------------------
@app.route("/artists")
def artists():
    # replace with real data returned from querying the database
    artists = Artist.query.all()

    return render_template("pages/artists.html", artists=artists)


@app.route("/artists/search", methods=["POST"])
def search_artists():
    # implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    artists = Artist.query.filter(
        Artist.name.ilike(f"%{request.form.get('search_term')}%")
    ).all()

    response = {
        "count": len(artists),
        "data": artists,
    }

    return render_template(
        "pages/search_artists.html",
        results=response,
        search_term=request.form.get("search_term", ""),
    )


@app.route("/artists/<int:artist_id>")
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    # replace with real artist data from the artist table, using artist_id
    now = datetime.now()
    upcoming_shows = (
        Show.query.filter(Show.artist_id == artist_id, Show.start_time > now)
        .join(Venue)
        .all()
    )
    past_shows = (
        Show.query.filter(Show.artist_id == artist_id, Show.start_time < now)
        .join(Venue)
        .all()
    )
    for show in upcoming_shows + past_shows:
        show.start_time = str(show.start_time)
        show.venue_name = show.venue.name
        show.venue_image_link = show.venue.image_link

    data = Artist.query.get(artist_id)
    data.upcoming_shows = upcoming_shows
    data.past_shows = past_shows
    data.upcoming_shows_count = len(upcoming_shows)
    data.past_shows_count = len(past_shows)
    print(data.genres)
    return render_template("pages/show_artist.html", artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route("/artists/<int:artist_id>/edit", methods=["GET"])
def edit_artist(artist_id):
    artist = Artist.query.get(artist_id)
    form = ArtistForm(obj=artist)

    # populate form with fields from artist with ID <artist_id>
    return render_template("forms/edit_artist.html", form=form, artist=artist)


@app.route("/artists/<int:artist_id>/edit", methods=["POST"])
def edit_artist_submission(artist_id):
    # take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    data = request.form
    try:
        artist = Artist.query.get(artist_id)
        artist.name = data["name"]
        artist.city = data["city"]
        artist.state = data["state"]
        artist.phone = data["phone"]
        artist.genres = data.getlist("genres")
        artist.image_link = data["image_link"]
        artist.facebook_link = data["facebook_link"]
        artist.website_link = data["website_link"]
        artist.seeking_venue = bool(data.get("seeking_venue"))
        artist.seeking_description = data["seeking_description"]
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()

    return redirect(url_for("show_artist", artist_id=artist_id))


@app.route("/venues/<int:venue_id>/edit", methods=["GET"])
def edit_venue(venue_id):
    venue = Venue.query.get(venue_id)
    form = VenueForm(obj=venue)

    # populate form with values from venue with ID <venue_id>
    return render_template("forms/edit_venue.html", form=form, venue=venue)


@app.route("/venues/<int:venue_id>/edit", methods=["POST"])
def edit_venue_submission(venue_id):
    # take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    data = request.form
    try:
        venue = Venue.query.get(venue_id)
        venue.name = data["name"]
        venue.city = data["city"]
        venue.state = data["state"]
        venue.phone = data["phone"]
        venue.genres = data.getlist("genres")
        venue.image_link = data["image_link"]
        venue.facebook_link = data["facebook_link"]
        venue.website_link = data["website_link"]
        venue.seeking_talent = bool(data.get("seeking_talent"))
        venue.seeking_description = data["seeking_description"]
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    return redirect(url_for("show_venue", venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------


@app.route("/artists/create", methods=["GET"])
def create_artist_form():
    form = ArtistForm()

    return render_template("forms/new_artist.html", form=form)


@app.route("/artists/create", methods=["POST"])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # insert form data as a new Artist in the db, instead
    # modify data to be the data object returned from db insertion
    # data = request.get_json()
    data = request.form

    try:
        print(data.getlist("genres"))
        artist = Artist(
            name=data["name"],
            city=data["city"],
            state=data["state"],
            phone=data["phone"],
            genres=data.getlist("genres"),
            image_link=data["image_link"],
            facebook_link=data["facebook_link"],
            website_link=data["website_link"],
            seeking_venue=bool(data.get("seeking_venue")),
            seeking_description=data["seeking_description"],
        )
        print(artist.genres)
        db.session.add(artist)
        db.session.commit()
        # on successful db insert, flash success
        flash("Artist " + artist.name + " was successfully listed!")
    except:
        db.session.rollback()
        # on unsuccessful db insert, flash an error instead.
        flash("An error occurred. Artist " + data["name"] + " could not be listed.")
    finally:
        db.session.close()
    return render_template("pages/home.html")


#  Shows
#  ----------------------------------------------------------------


@app.route("/shows")
def shows():
    # displays list of shows at /shows
    # replace with real venues data.

    data = []
    shows = Show.query.join(Venue).join(Artist).all()
    for show in shows:
        data.append(
            {
                "venue_id": show.venue_id,
                "venue_name": show.venue.name,
                "artist_id": show.artist_id,
                "artist_name": show.artist.name,
                "artist_image_link": show.artist.image_link,
                "start_time": format_datetime(str(show.start_time)),
            }
        )
    print(data)
    return render_template("pages/shows.html", shows=data)


@app.route("/shows/create")
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template("forms/new_show.html", form=form)


@app.route("/shows/create", methods=["POST"])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # insert form data as a new Show record in the db, instead

    data = request.form

    try:
        show = Show(
            start_time=data["start_time"],
            artist_id=data["artist_id"],
            venue_id=data["venue_id"],
        )
        db.session.add(show)
        db.session.commit()
        # on successful db insert, flash success
        flash("Show was successfully listed!")
    except:
        db.session.rollback()
        print(sys.exc_info())
        # on unsuccessful db insert, flash an error instead.
        flash("An error occurred. Show could not be listed.")
    finally:
        db.session.close()
    return render_template("pages/home.html")


@app.errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error(error):
    return render_template("errors/500.html"), 500


if not app.debug:
    file_handler = FileHandler("error.log")
    file_handler.setFormatter(
        Formatter("%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]")
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info("errors")

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == "__main__":
    app.run()

# Or specify port manually:
"""
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
"""
