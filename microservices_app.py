from flask import Flask, request, jsonify
from flask_mongoengine import MongoEngine
import pika
import json
import uuid
import os

# Initialize Flask application
app = Flask(__name__)
app.config['MONGODB_SETTINGS'] = {
    'db': 'microservices_db',
    'host': 'mongodb://localhost:27017/microservices_db'
}

# Initialize database
db = MongoEngine(app)

# User Model
class User(db.Document):
    username = db.StringField(required=True, unique=True)
    email = db.StringField(required=True, unique=True)

# Message Broker Setup
RABBITMQ_HOST = 'localhost'
QUEUE_NAME = 'task_queue'

def send_message(message):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    channel.basic_publish(exchange='', routing_key=QUEUE_NAME, body=json.dumps(message),
                          properties=pika.BasicProperties(delivery_mode=2,))
    connection.close()

@app.route('/users', methods=['POST'])
def create_user():
    username = request.json.get('username')
    email = request.json.get('email')
    user = User(username=username, email=email)
    user.save()

    send_message({'username': username, 'email': email, 'action': 'create'})
    return jsonify({'id': str(user.id), 'username': username, 'email': email}), 201

@app.route('/users/<user_id>', methods=['GET'])
def get_user(user_id):
    user = User.objects(id=user_id).first()
    if user:
        return jsonify({'id': str(user.id), 'username': user.username, 'email': user.email}), 200
    return jsonify({'error': 'User not found'}), 404

@app.route('/users/<user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.objects(id=user_id).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    username = request.json.get('username', user.username)
    email = request.json.get('email', user.email)
    user.update(username=username, email=email)

    send_message({'username': username, 'email': email, 'action': 'update'})
    return jsonify({'id': str(user.id), 'username': username, 'email': email}), 200

@app.route('/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.objects(id=user_id).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    user.delete()
    send_message({'username': user.username, 'action': 'delete'})
    return jsonify({'message': 'User deleted'}), 204

def callback(ch, method, properties, body):
    message = json.loads(body)
    print('Received Message: %r' % message)
    # Further processing can be done here

def start_rabbitmq_listener():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)

    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback, auto_ack=True)
    print('Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    from threading import Thread
    rabbitmq_thread = Thread(target=start_rabbitmq_listener)
    rabbitmq_thread.start()
    
    app.run(port=int(os.environ.get("PORT", 5000)), debug=True)