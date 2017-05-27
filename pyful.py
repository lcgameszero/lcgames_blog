from flask import Flask,jsonify,abort,url_for,make_response,request
from flask_httpauth import HTTPBasicAuth
from itsdangerous import Serializer
from flask_restful import Api,Resource,reqparse,marshal,fields

auth = HTTPBasicAuth()

app = Flask(__name__)
api = Api(app)

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

task_fields = {
    'title':fields.String,
    'description':fields.String,
    'done':fields.Boolean,
    'uri':fields.Url('task'),
}

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

class TaskListAPI(Resource):
    decorators = [auth.login_required]
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('title',type=str,required=True,help='no title provided',location='json')
        self.reqparse.add_argument('description',type=str,default='',location='json')
        super(TaskListAPI,self).__init__()

    def get(self):
        ts = []
        for t in tasks:
            ts.append(marshal(t,task_fields))
        return {'tasks':ts}

    def post(self):
        if not request.json or not 'title' in request.json:
            abort(400)
        
        newid = tasks[-1].get('id')+1
        task = {
            'id':newid,
            'title':request.json.get('title'),
            'description':request.json.get('description',''),
            'done': False
        }

        tasks.append(task)
        return {'task':marshal(task,task_fields)},201

class TaskAPI(Resource):
    decorators = [auth.login_required]
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('title',type=str,location='json')
        self.reqparse.add_argument('description',type=str,location='json')
        self.reqparse.add_argument('done',type=bool,location='json')
        super(TaskAPI,self).__init__()

    def get(self,id):
        ts = [x for x in tasks if x.get('id')==id]
        if len(ts)==0:
            abort(404)
        return {'task':marshal(ts[0],task_fields)}

    def put(self,id):
        print 'update_task' ,request.json
        ts = [x for x in tasks if x.get('id')==id]
        if len(ts)==0:
            abort(404)
        t = ts[0]

        args = self.reqparse.parse_args()
        for k,v in args.iteritems():
            if v is not None:
                t[k] = v

        return {'task':marshal(t,task_fields)}

    def delete(self,id):
        ts = [x for x in tasks if x.get('id')==id]
        if len(ts)==0:
            abort(404)
        tasks.remove(ts[0])
        return {'result':True}

api.add_resource(TaskListAPI,'/todo/api/v1.0/tasks',endpoint='tasks')
api.add_resource(TaskAPI,'/todo/api/v1.0/tasks/<int:id>',endpoint='task')

if __name__ == '__main__':
    app.run(debug = True)