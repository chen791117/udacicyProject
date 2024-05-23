import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  
  '''
  @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
  '''  
  # CORS(app, resources={r"*/api/*" : {origins: '*'}})
  CORS(app)
  '''
  @TODO: Use the after_request decorator to set Access-Control-Allow
  '''
  @app.after_request
  def after_request(response):
      """设置响应头支持跨域和对 RESTful 方法的支持"""
      response.headers.add(
          "Access-Control-Allow-Headers", "Content-Type, Authorization"
      )
      response.headers.add(
          "Access-Control-Allow-Headers", "GET, POST, PATCH, DELETE, OPTION"
      )
      return response


  '''
  @TODO: 
  Create an endpoint to handle GET requests 
  for all available categories.
  '''
  @app.route('/categories')
  def get_categories():
      """获取所有类别"""
      categories = Category.query.all()
      if not categories:
            # 如果没有找到任何类别，返回404错误        
          abort(404)
      category_dict = {category.id: category.type for category in categories}  # 将类别数据格式化为字典

      return jsonify({
          'success': True,
          'categories': category_dict
      })


  '''
  @TODO: 
  Create an endpoint to handle GET requests for questions, 
  including pagination (every 10 questions). 
  This endpoint should return a list of questions, 
  number of total questions, current category, categories. 
  

  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions. 
  '''
  def paginate_questions(request, selection):
      page = request.args.get('page', 1, type=int)  # 从请求中获取页码，默认为第一页
      start = (page - 1) * QUESTIONS_PER_PAGE
      end = start + QUESTIONS_PER_PAGE
      questions = [question.format() for question in selection]
      current_questions = questions[start:end]      
      return current_questions
  
  @app.route('/questions')
  def get_questions():
      selection = Question.query.order_by(Question.id).all()  # 从数据库获取所有问题，并按 ID 排序
      current_questions = paginate_questions(request, selection)  # 应用分页
      if len(current_questions) == 0:
            abort(404)
      

      categories = Category.query.all()  # 获取所有类别
      categories_dict = {category.id: category.type for category in categories}  # 格式化类别数据为字典

      # 返回的 JSON 包括问题列表、总问题数、当前类别（初始设为 None），以及所有类别
      return jsonify({
          'success': True,
          'questions': current_questions,
          'total_questions': len(selection),
          'current_category': None,
          'categories': categories_dict
      })

  '''
  @TODO: 
  Create an endpoint to DELETE question using a question ID. 

  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page. 
  '''
  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  def delete_question(question_id):
      question = Question.query.get(question_id)  # 根据 ID 查找问题
      if not question:
          abort(404)
      try:          
          question.delete()  # 调用模型中的删除方法，从数据库中删除这个问题
          return jsonify({
              'success': True,
              'deleted': question_id
          })
      except Exception as e:
          # 如果出现异常，返回错误信息
          abort(422)

  '''
  @TODO: 
  Create an endpoint to POST a new question, 
  which will require the question and answer text, 
  category, and difficulty score.

  TEST: When you submit a question on the "Add" tab, 
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.  
  '''
  @app.route('/questions', methods=['POST'])
  def add_question():
      body = request.get_json()  # 从请求体中获取 JSON 数据

      question_text = body.get('question', None)
      answer_text = body.get('answer', None)
      category = body.get('category', None)
      difficulty = body.get('difficulty', None)

      if not (question_text and answer_text and category and difficulty):
          # 如果任何必需字段缺失，返回错误
          abort(400)

      try:
          question = Question(question=question_text, answer=answer_text, category=category, difficulty=difficulty)
          question.insert()  # 调用模型的 insert 方法，将问题添加到数据库

          return jsonify({
              'success': True,
              'created': question.id  # 返回新创建问题的 ID
          })
      except Exception as e:
          # 如果出现异常，返回错误信息
          abort(422)


  '''
  @TODO: 
  Create a POST endpoint to get questions based on a search term. 
  It should return any questions for whom the search term 
  is a substring of the question. 

  TEST: Search by any phrase. The questions list will update to include 
  only question that include that string within their question. 
  Try using the word "title" to start. 
  '''
  @app.route('/questions/search', methods=['POST'])
  def search_questions():
      body = request.get_json()
      search_term = body.get('searchTerm', None)
      

      if search_term:
          search_results = Question.query.filter(Question.question.ilike(f'%{search_term}%')).all()  # 使用不区分大小写的 LIKE 查询
          if not search_results:
                abort(404)
          formatted_questions = [question.format() for question in search_results]

          return jsonify({
              'success': True,
              'questions': formatted_questions,
              'total_questions': len(formatted_questions),
              'current_category': None
          })
      else:
          abort(400)

  '''
  @TODO: 
  Create a GET endpoint to get questions based on category. 

  TEST: In the "List" tab / main screen, clicking on one of the 
  categories in the left column will cause only questions of that 
  category to be shown. 
  '''
  @app.route('/categories/<int:category_id>/questions')
  def get_questions_by_category(category_id):
      try:
          # 确认类别存在
          category = Category.query.filter_by(id=category_id).one_or_none()
          if not category:
              abort(404)

          # 查询该类别下的所有问题
          questions = Question.query.filter_by(category=str(category_id)).all()
          formatted_questions = [question.format() for question in questions]

          return jsonify({
              'success': True,
              'questions': formatted_questions,
              'total_questions': len(formatted_questions),
              'current_category': category.type
          })
      except Exception as e:
          abort(500)


  '''
  @TODO: 
  Create a POST endpoint to get questions to play the quiz. 
  This endpoint should take category and previous question parameters 
  and return a random questions within the given category, 
  if provided, and that is not one of the previous questions. 

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not. 
  '''
  @app.route('/quizzes', methods=['POST'])
  def get_random_quiz_question():
      body = request.get_json()
      previous_questions = body.get('previous_questions', [])
      quiz_category = body.get('quiz_category', None)

      try:
          # 如果提供了类别，只在该类别中查找问题，否则在所有类别中查找
          if quiz_category and quiz_category['id'] != 0:  # 0 表示选择了 'All' 类别
              questions_query = Question.query.filter_by(category=str(quiz_category['id']))
          else:
              questions_query = Question.query

          # 从查询结果中排除已显示的问题
          remaining_questions = questions_query.filter(Question.id.notin_(previous_questions)).all()

          # 随机选择一个新问题
          if remaining_questions:
              new_question = random.choice(remaining_questions).format()
          else:
              new_question = None

          return jsonify({
              'success': True,
              'question': new_question
          })
      except Exception as e:
          abort(500)

  '''
  @TODO: 
  Create error handlers for all expected errors 
  including 404 and 422. 
  '''
  @app.errorhandler(404)
  def not_found(error):
      return jsonify({
          "success": False,
          "error": 404,
          "message": "resource not found"
      }), 404

  @app.errorhandler(422)
  def unprocessable(error):
      return jsonify({
          "success": False,
          "error": 422,
          "message": "unprocessable entity"
      }), 422

  @app.errorhandler(400)
  def bad_request(error):
      return jsonify({
          "success": False,
          "error": 400,
          "message": "bad request"
      }), 400

  @app.errorhandler(500)
  def internal_server_error(error):
      return jsonify({
          "success": False,
          "error": 500,
          "message": "internal server error"
      }), 500
  
  return app

    