import json
import uuid
from chalice import Chalice
import boto3

app = Chalice(app_name='user_management')
TABLE = boto3.resource('dynamodb').Table('Users')

## Routes Of The API ##

@app.route('/')
def index():
    return {"Success": True, "message": "Welcome to the User Management API"}

@app.route('/users', methods=['GET'])
def list_users():
    request = app.current_request
    if request.query_params is None:
        page = None
    else:
        page = request.query_params.get('page', None)
    if page is None:
        response = TABLE.scan(Limit=10)
    else:
        response = TABLE.scan(
            Limit=10,
            ExclusiveStartKey = {
                "id": page
            }
        )
    users = response.get('Items', [])
    return {
        "users": users,
        "next_page": response.get('LastEvaluatedKey', None)
    }

@app.route('/users/{user_id}', methods=['GET'])
def get_user(user_id):
    user = TABLE.get_item(
        Key={'id': user_id}
    )
    if 'Item' in user:
        return user['Item']
    else:
        return {"error": "User not found"}, 404
    
@app.route('/users', methods=['POST'])
def create_user():
    request = app.current_request
    user_data = request.json_body

    if not user_data or 'name' not in user_data or 'email' not in user_data:
        return {"error": "Invalid user data"}, 400
    
    TABLE.put_item(
        Item={
            'id': str(uuid.uuid4()),
            'name': user_data.get('name'),
            'email': user_data.get('email')
        }
    )

    return {"message": "User created successfully", "user": user_data}, 201

@app.route('/users/{user_id}', methods=['PUT'])
def update_user(user_id):
    request = app.current_request
    user_data = request.json_body
    if not user_data or 'name' not in user_data or 'email' not in user_data:
        return {"error": "Invalid user data"}, 400
    TABLE.update_item(
        Key={'id': user_id},
        UpdateExpression="set name=:n, email=:e",
        ExpressionAttributeValues={
            ':n': user_data['name'],
            ':e': user_data['email']
        },
        ReturnValues="UPDATED_NEW"
    )
    return {"message": "User updated successfully", "user": user_data}

@app.route('/users/{user_id}', methods=['DELETE'])
def delete_user(user_id):
    TABLE.delete_item(
        Key={'id': user_id}
    )
    if TABLE.get_item(Key={'id': user_id}).get('Item'):
        return {"error": "Failed to delete user"}, 500
    return {"message": f"User with ID {user_id} deleted successfully"}

