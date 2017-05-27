from flask import Flask,jsonify,abort,url_for,make_response,request
from flask_httpauth import HTTPBasicAuth
from itsdangerous import Serializer

auth = HTTPBasicAuth()

app = Flask(__name__)

tasks = [
    {
        'id': 1,
        'title': u'Buy groceries',
        'description': u'Milk, Cheese, Pizza, Fruit, Tylenol',
        'done': False
    },
    {
        'id': 2,
        'title': u'Learn Python',
        'description': u'Need to find a good Python tutorial on the web',
        'done': False
    }
]

@auth.get_password
def get_password(username):
    print 'get_password',username
    if username=='lzp':
        return 'pwd'
    return None

@auth.verify_password
def verify_password(uname,pwd):
    print 'verify_password',uname,pwd
    if get_password(uname)==pwd:
        return True
    return False

@auth.error_handler
def unauthorized():
    return make_response(jsonify({'error':'unauthorized access'}),403)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error':'Not found'}))

@app.errorhandler(400)
def not_found(error):
    return make_response(jsonify({'error':'Not found 400'}))

@app.route('/todo/api/v1.0/tasks',methods=['GET'])
@auth.login_required
def get_tasks():
    return jsonify({'tasks':tasks})

@app.route('/todo/api/v1.0/tasks',methods=['POST'])
def create_task():
    if not request.json or not 'title' in request.json:
        abort(400)
    
    newid = tasks[-1].get('id')+1
    task = {
        'id':newid,
        'url':url_for('get_task',task_id=newid,_external=True),
        'title':request.json.get('title'),
        'description':request.json.get('description',''),
        'done': False
    }

    tasks.append(task)
    return jsonify({'task':task}),201

@app.route('/todo/api/v1.0/tasks/<int:task_id>',methods=['PUT'])
def update_task(task_id):
    print 'update_task' ,request.json
    ts = [x for x in tasks if x.get('id')==task_id]
    if len(ts)==0:
        abort(404)
    if not request.json:
        abort(400)
    if 'done' in request.json and type(request.json['done']) is not bool:
        abort(400)
    
    ts[0]['title'] = request.json.get('title', ts[0]['title'])
    ts[0]['description'] = request.json.get('description', ts[0]['description'])
    ts[0]['done'] = request.json.get('done', ts[0]['done'])

    return jsonify({'task':ts[0]})

@app.route('/todo/api/v1.0/tasks/<int:task_id>',methods=['DELETE'])
def delete_task(task_id):
    ts = [x for x in tasks if x.get('id')==task_id]
    if len(ts)==0:
        abort(404)
    tasks.remove(ts[0])
    return jsonify({'result':True})

@app.route('/todo/api/v1.0/tasks/<int:task_id>',methods=['GET'])
def get_task(task_id):
    ts = [x for x in tasks if x.get('id')==task_id]
    if len(ts)==0:
        abort(404)
    return jsonify({'task':ts[0]}) 

if __name__ == '__main__':
    app.run(debug = True)