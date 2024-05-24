import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app
from models import setup_db, Question, Category
from settings import DBTEST_NAME,DBTEST_USER


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = DBTEST_NAME
        self.database_path = 'postgresql://{}@{}/{}'.format(DBTEST_USER,'localhost:5432', self.database_name)
        setup_db(self.app, self.database_path)

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()
            # 添加测试类别
            new_category1 = Category(type="Science")
            new_category2 = Category(type="Art")
            # 添加可以被搜索的问题
            question = Question(question='What is the capital of France?', answer='Paris', difficulty=1, category=1)
            self.new_question={'question': 'What is the capital of France?', 'answer':'Paris', 'difficulty':'1', 'category':'1'}
            self.db.session.add(question)
            self.db.session.add(new_category1)
            self.db.session.add(new_category2)
            self.db.session.commit()
    
    def tearDown(self):
        """Executed after reach test"""
        pass

    """
    TODO
    Write at least one test for each test for successful operation and for expected errors.
    """
    def test_get_categories(self):
        res = self.client().get('/categories')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])
        self.assertTrue(len(data['categories']))

    def test_get_categories_no_categories_found(self):
        """Test retrieval of categories when none are available."""
        # Ensure there are no categories
        Category.query.delete()
        res = self.client().get('/categories')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 404)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'resource not found')
    def test_get_questions_pagination(self):
        """Test question pagination success."""
        res = self.client().get('/questions?page=1')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])
        self.assertTrue(len(data['questions']) <= 10)

    def test_get_questions_beyond_valid_page(self):
        """Test questions request beyond valid page."""
        res = self.client().get('/questions?page=1000')  # Assuming there aren't that many pages
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 404)
        self.assertFalse(data['success'])
        self.assertIn('message', data)
    

    def test_add_question(self):
        new_question = {
            'question': 'What is the capital of France?',
            'answer': 'Paris',
            'difficulty': 3,
            'category': '3'
        }
        res = self.client().post('/questions', json=new_question)
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])

    def test_400_if_question_creation_fails(self):
        new_question = {
            'question': 'What is the capital of France?'
        }
        res = self.client().post('/questions', json=new_question)
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 400)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'bad request')
    def test_search_questions(self):
        res = self.client().post('/questions/search', json={'searchTerm': 'capital'})
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])
        self.assertIsNotNone(data['questions'])

    def test_search_questions_no_results(self):
        res = self.client().post('/questions/search', json={'searchTerm': 'xyz123'})
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 404)
        self.assertFalse(data['success'])

    def test_delete_question(self):
        """Test successful deletion of a question."""
        # Add a question to delete
        question = Question(question='test question', answer='test answer', difficulty=1, category=1)
        question.insert()
        question_id = question.id
        res = self.client().delete(f'/questions/{question_id}')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['deleted'], question_id)

    def test_delete_nonexistent_question(self):
        """Test deletion of a non-existent question."""
        res = self.client().delete('/questions/9999')  # Assuming this ID doesn't exist
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 404)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'resource not found')
    
    def test_get_random_question(self):
        # 插入一些问题以供测试
        res = self.client().post('/questions', json=self.new_question)
        self.assertEqual(res.status_code, 200)

        # 测试获取随机问题
        res = self.client().post('/quizzes', json={
            'previous_questions': [],
            'quiz_category': {'id': '3'}
        })
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])
        self.assertIsNotNone(data['question'])

    def test_no_questions_left_to_ask(self):
        # 假设所有问题都已被回答
        res = self.client().post('/quizzes', json={
            'previous_questions': [11, 12, 13, 14, 15],  # 假设这些 ID 已存在
            'quiz_category': {'id': '13'}
        })
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])
        self.assertIsNone(data['question'])

    def test_no_category_questions(self):
        # 测试一个没有问题的类别
        res = self.client().post('/quizzes', json={
            'previous_questions': [],
            'quiz_category': {'id': '99'}  # 假设此 ID 的类别没有问题
        })
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])
        self.assertIsNone(data['question'])


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()