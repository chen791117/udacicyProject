#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
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

class Venue(db.Model):
    __tablename__ = 'Venue'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(500))
    website_link = db.Column(db.String(500))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(500))
    genres = db.Column(db.String(500))
    past_shows = db.relationship('Shows', back_populates='venue', lazy=True, foreign_keys='Shows.venue_id', overlaps="upcoming_shows")
    upcoming_shows = db.relationship('Shows', back_populates='venue', lazy=True, foreign_keys='Shows.venue_id', overlaps="past_shows")

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(500))
    website = db.Column(db.String(500))
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(500))
    past_shows = db.relationship('Shows', back_populates='artist', lazy=True, foreign_keys='Shows.artist_id', overlaps="upcoming_shows")
    upcoming_shows = db.relationship('Shows', back_populates='artist', lazy=True, foreign_keys='Shows.artist_id', overlaps="past_shows")

class Shows(db.Model):
    __tablename__ = 'Shows'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=True)
    venue = db.relationship("Venue", back_populates="past_shows", overlaps="upcoming_shows")
    artist = db.relationship("Artist", back_populates="past_shows", overlaps="upcoming_shows")
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
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  # 查询所有场地并按城市和州组织
  venue_list = Venue.query.all()
  data = []

  cities_states = set()
  for venue in venue_list:
      cities_states.add((venue.city, venue.state))

  for city_state in cities_states:
      venues_in_city = Venue.query.filter_by(city=city_state[0], state=city_state[1]).all()
      venue_data = []
      for venue in venues_in_city:
          # 计算每个场地的即将进行的演出数量
          num_upcoming_shows = Shows.query.filter(Shows.venue_id == venue.id, Shows.start_time > datetime.now()).count()
          venue_data.append({
              "id": venue.id,
              "name": venue.name,
              "num_upcoming_shows": num_upcoming_shows
          })
      data.append({
          "city": city_state[0],
          "state": city_state[1],
          "venues": venue_data
      })

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on venues with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee" 
  search_term = request.form.get('search_term', '')
  # 使用 SQLAlchemy 的 ilike 进行部分字符串搜索（不区分大小写）
  matching_venues = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()

  response_data = []

  for venue in matching_venues:
      # 计算每个场地的即将进行的演出数量
      num_upcoming_shows = Shows.query.filter(Shows.venue_id == venue.id, Shows.start_time > datetime.now()).count()
      response_data.append({
          "id": venue.id,
          "name": venue.name,
          "num_upcoming_shows": num_upcoming_shows
      })

  response = {
      "count": len(matching_venues),
      "data": response_data
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  # 通过主键获取目标场地数据，如果没有找到则返回 404 页面
  venue = Venue.query.get_or_404(venue_id)

  # 查询该场地的过去和即将到来的演出
  past_shows_query = Shows.query.join(Artist).filter(
      Shows.venue_id == venue_id,
      Shows.start_time < datetime.now()
  ).all()

  upcoming_shows_query = Shows.query.join(Artist).filter(
      Shows.venue_id == venue_id,
      Shows.start_time >= datetime.now()
  ).all()

  # 构建过去的演出数据
  past_shows = [{
      "artist_id": show.artist.id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime("%Y-%m-%dT%H:%M:%S")
  } for show in past_shows_query]

  # 构建即将到来的演出数据
  upcoming_shows = [{
      "artist_id": show.artist.id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime("%Y-%m-%dT%H:%M:%S")
  } for show in upcoming_shows_query]

  # 构建返回的场地数据
  data = {
      "id": venue.id,
      "name": venue.name,
      "genres": venue.genres.replace('{', '').replace('}', '').split(','),  # 如果 genres 是字符串，将其转为列表
      "address": venue.address,
      "city": venue.city,
      "state": venue.state,
      "phone": venue.phone,
      "website_link": venue.website_link,
      "facebook_link": venue.facebook_link,
      "seeking_talent": venue.seeking_talent,
      "seeking_description": venue.seeking_description,
      "image_link": venue.image_link,
      "past_shows": past_shows,
      "upcoming_shows": upcoming_shows,
      "past_shows_count": len(past_shows),
      "upcoming_shows_count": len(upcoming_shows),
  }
  # 渲染页面模板并传递数据
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  form = VenueForm(request.form)
  if form.validate():
        try:
            new_venue = Venue(
                name=form.name.data,
                city=form.city.data,
                state=form.state.data,
                address=form.address.data,
                phone=form.phone.data,
                image_link=form.image_link.data,
                facebook_link=form.facebook_link.data,
                genres=form.genres.data,
                website_link=form.website_link.data,  # 歌手的個人網站連結
                #seeking_venue =form.seeking_venue.data,  # 是否在尋找演出場地
                seeking_description = form.seeking_description.data  # 尋找演出場地的描述
            )
            db.session.add(new_venue)
            db.session.commit()
            flash('Venue ' + request.form['name'] + ' was successfully listed!')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
            print(f"Error: {e}")
            
        finally:
            db.session.close()
  else:
        flash('Form validation failed. Venue ' + request.form['name'] + ' could not be listed.')           
  # on successful db insert, flash success
  #flash('Venue ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  try:
      # 检索要删除的场地
      venue = Venue.query.get_or_404(venue_id)

      # 删除场地
      db.session.delete(venue)

      # 提交事务
      db.session.commit()

      flash(f'Venue {venue.name} was successfully deleted.', 'success')
  except SQLAlchemyError as e:
      # 捕获错误并回滚事务
      db.session.rollback()
      flash(f'An error occurred while trying to delete the venue: {str(e)}', 'error')
    
  # 最终将用户重定向到主页
  return redirect(url_for('index'))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database  
  # 查询数据库中的所有艺术家信息
  artists = Artist.query.all()
    
  # 将查询到的艺术家对象转换为字典列表
  data = [{"id": artist.id, "name": artist.name} for artist in artists]
    
  # 将字典数据传递给模板并进行渲染
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  # 获取用户输入的搜索词
  search_term = request.form.get('search_term', '')
    
  # 执行数据库查询（不区分大小写的部分匹配）
  search_results = Artist.query.filter(func.lower(Artist.name).contains(search_term.lower())).all()
    
  # 将查询结果转换为字典列表
  data = [{"id": artist.id, "name": artist.name, "num_upcoming_shows": len(artist.upcoming_shows)} for artist in search_results]
    
  # 创建响应字典
  response = {
      "count": len(data),
      "data": data
  }
    
  # 渲染搜索结果到模板
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  # 查詢資料庫中與給定 artist_id 匹配的藝術家
  artist = Artist.query.get(artist_id)
  if not artist:
      # 如果沒有找到藝術家，可以重定向到其他頁面或顯示錯誤消息
      flash("No artist found with the provided ID.")
      return redirect(url_for('index'))  # 假設有一個名為 'index' 的路由

  # 如果找到了藝術家，則準備過去和未來的表演數據
  past_shows_query = Shows.query.filter(Shows.artist_id == artist_id, Shows.start_time < datetime.now()).all()
  upcoming_shows_query = Shows.query.filter(Shows.artist_id == artist_id, Shows.start_time >= datetime.now()).all()

  # 組織過去和未來的表演數據以便在模板中顯示
  past_shows = [{
      'venue_id': show.venue_id,
      'venue_name': show.venue.name,
      'venue_image_link': show.venue.image_link,
      'start_time': show.start_time.strftime('%Y-%m-%d %H:%M:%S')
  } for show in past_shows_query]

  upcoming_shows = [{
      'venue_id': show.venue_id,
      'venue_name': show.venue.name,
      'venue_image_link': show.venue.image_link,
      'start_time': show.start_time.strftime('%Y-%m-%d %H:%M:%S')
  } for show in upcoming_shows_query]

  # 將藝術家數據和表演數據傳遞給前端模板
  artist_data = {
      'id': artist.id,
      'name': artist.name,
      'genres': artist.genres.replace('{', '').replace('}', '').split(','),
      'city': artist.city,
      'state': artist.state,
      'phone': artist.phone,
      'website': artist.website,
      'facebook_link': artist.facebook_link,
      'seeking_venue': artist.seeking_venue,
      'seeking_description': artist.seeking_description,
      'image_link': artist.image_link,
      'past_shows': past_shows,
      'upcoming_shows': upcoming_shows,
      'past_shows_count': len(past_shows),
      'upcoming_shows_count': len(upcoming_shows)
  }

  return render_template('pages/show_artist.html', artist=artist_data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()  
  # TODO: populate form with fields from artist with ID <artist_id>
  # 从数据库获取艺术家信息
  artist = Artist.query.get(artist_id)

  # 检查艺术家是否存在
  if not artist:
      return render_template('errors/404.html'), 404

  # 创建并填充表单
  form = ArtistForm(
      name=artist.name,
      genres=artist.genres,
      city=artist.city,
      state=artist.state,
      phone=artist.phone,
      website_link=artist.website,
      facebook_link=artist.facebook_link,
      seeking_venue=artist.seeking_venue,
      seeking_description=artist.seeking_description,
      image_link=artist.image_link
  )

  # 将数据传递到模板
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  # 获取用户提交的表单
  form = ArtistForm(request.form)
  try:
      # 查询要更新的艺术家对象
      artist = Artist.query.get(artist_id)

      if not artist:
          flash(f"Artist with ID {artist_id} not found.", "danger")
          return redirect(url_for('artists'))

      # 更新艺术家对象属性
      artist.name = form.name.data
      artist.genres = form.genres.data
      artist.city = form.city.data
      artist.state = form.state.data
      artist.phone = form.phone.data
      artist.website = form.website_link.data
      artist.facebook_link = form.facebook_link.data
      artist.seeking_venue = form.seeking_venue.data
      artist.seeking_description = form.seeking_description.data
      artist.image_link = form.image_link.data

        # 提交更新到数据库
      db.session.commit()
      flash("Artist information was successfully updated.", "success")

  except Exception as e:
      # 在更新失败的情况下回滚事务并显示错误消息
      db.session.rollback()
      flash(f"An error occurred while updating the artist: {str(e)}", "danger")
  finally:
      # 确保会话关闭
      db.session.close()

  # 重定向到艺术家详情页面
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  # TODO: populate form with values from venue with ID <venue_id>
  # 查询数据库中的场馆对象
  venue = Venue.query.get(venue_id)

  if not venue:
      flash(f"Venue with ID {venue_id} not found.", "danger")
      return redirect(url_for('venues'))

  # 使用数据库中的场馆对象填充表单
  form = VenueForm(
      name=venue.name,
      genres=venue.genres,
      address=venue.address,
      city=venue.city,
      state=venue.state,
      phone=venue.phone,
      website_link=venue.website_link,
      facebook_link=venue.facebook_link,
      seeking_talent=venue.seeking_talent,
      seeking_description=venue.seeking_description,
      image_link=venue.image_link
  )

  # 将表单和场馆对象传递给模板
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  form = VenueForm(request.form)
  venue = Venue.query.get(venue_id)
    
  if venue:
      try:
          # 使用表单数据更新场馆信息
          venue.name = form.name.data
          venue.city = form.city.data
          venue.state = form.state.data
          venue.address = form.address.data
          venue.phone = form.phone.data
          venue.genres = form.genres.data  # 假设这是一个列表或其他形式的数据
          venue.image_link = form.image_link.data
          venue.facebook_link = form.facebook_link.data
          venue.website_link = form.website_link.data
          venue.seeking_talent = form.seeking_talent.data
          venue.seeking_description = form.seeking_description.data

          db.session.commit()
          flash('Venue ' + request.form['name'] + ' was successfully updated!')
      except Exception as e:
          db.session.rollback()
          flash(f'An error occurred. Venue {form.name.data} could not be updated. Error: {str(e)}')
      finally:
           db.session.close()
  else:
      flash(f"Venue with ID {venue_id} not found.", "danger")
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
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  form = ArtistForm(request.form)
  if form.validate():
      try:
          new_artist = Artist(
              name=form.name.data,
              city=form.city.data,
              state=form.state.data,
              phone=form.phone.data,
              genres=form.genres.data,
              image_link=form.image_link.data,
              facebook_link=form.facebook_link.data,

              website = form.website_link.data,  # 歌手的個人網站連結
              seeking_venue = form.seeking_venue.data,  # 是否在尋找演出場地
              seeking_description = form.seeking_description.data  # 尋找演出場地的描述
          )
          db.session.add(new_artist)
          db.session.commit()
          flash('Artist ' + request.form['name'] + ' was successfully listed!')
      except Exception as e:
          db.session.rollback()
          flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
          print(f"Error: {e}")

      finally:
          db.session.close()
  else:
      flash('Form validation failed. Artist ' + request.form['name'] + ' could not be listed.')

  # on successful db insert, flash success
  #flash('Artist ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.  
  # 查询所有表演记录，包括相关的艺术家和场馆信息
  shows_query = db.session.query(Shows).join(Venue).join(Artist).all()

  # 格式化数据以传递给模板
  data = [{
      "venue_id": show.venue.id,
      "venue_name": show.venue.name,
      "artist_id": show.artist.id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
  } for show in shows_query]

  # 渲染页面，并传递数据
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
  form = ShowForm(request.form)
  if form.validate():
      try:
          new_show = Shows(
              venue_id=form.venue_id.data,
              artist_id=form.artist_id.data,
              start_time=form.start_time.data
          )
          db.session.add(new_show)
          db.session.commit()
          flash('Show was successfully listed!')
      except:
          db.session.rollback()
          flash('An error occurred. Show could not be listed.')
      finally:
          db.session.close()
  else:
      flash('Form validation failed. Show could not be listed.')

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
