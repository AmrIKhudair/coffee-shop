import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Transaction, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! YOU CAN INSTEAD RUN `python -m src.db_drop_and_create_all`
'''
# db_drop_and_create_all()

## ROUTES
'''
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks', methods=['GET'])
def get_drinks():
    response = {
        'success': True,
        'drinks': [drink.short() for drink in Drink.query.all()]
    }

    return jsonify(response)


'''
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_detail():
    response = {
        'success': True,
        'drinks': [drink.long() for drink in Drink.query.all()]
    }

    return jsonify(response)


'''
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def post_drink():
    @Transaction
    def tx():
        try:
            request_json = request.get_json()
            title = request_json.get('title', '')
            recipe = request_json.get('recipe', [])
            drink = Drink(title=title, recipe=json.dumps(recipe))
        except: abort(422)


        drink.insert()
        return drink

    success = lambda drink: jsonify({ 'success': True, 'drinks': [drink.long()] })
    return tx.success(success).run()

'''
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(id):
    @Transaction
    def tx():
        drink = Drink.query.get(id)
        if not drink: abort(404)

        try:
            request_json = request.get_json()

            title = request_json.get('title', '')
            if title: drink.title = title

            recipe = request_json.get('recipe', [])
            if recipe: drink.recipe = json.dumps(recipe)

        except: abort(422)

        return drink

    success = lambda drink: jsonify({ 'success': True, 'drinks': [drink.long()] })
    return tx.success(success).run()

'''
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drinks(id):
    @Transaction
    def tx():
        drink = Drink.query.get(id)
        if not drink: abort(404)
        drink.delete()
        return drink

    success = lambda drink: jsonify({ 'success': True, 'delete': drink.id })
    return tx.success(success).run()

## Error Handling
'''
Example error handling for unprocessable entity
'''
@app.errorhandler(422)
def unprocessable(error):
    response = {
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }

    return jsonify(response), 422

'''
    error handler should conform to general task above
'''
@app.errorhandler(404)
def resource_not_found(error):
    response = {
        "success": False,
        "error": 404,
        "message": "resource not found"
    }

    return jsonify(response), 404

'''
    error handler should conform to general task above
'''
@app.errorhandler(AuthError)
def auth_error(error):
    response = {
        "success": False,
        "error": error.status_code,
        "message": error.error
    }

    return jsonify(response), error.status_code
