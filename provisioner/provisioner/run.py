from flask import Flask
from helpers import k8s_config, config
from routes.instances import OrthancInstancePodList
from flask_restful import reqparse, abort, Api, Resource

k8s_config.load_kubernetes_config()
app = Flask(__name__)
api = Api(app)


TODOS = {
    'todo1': {'task': 'build an API'},
    'todo2': {'task': '?????'},
    'todo3': {'task': 'profit!'},
}


def abort_if_todo_doesnt_exist(todo_id):
    if todo_id not in TODOS:
        abort(404, message="Todo {} doesn't exist".format(todo_id))

parser = reqparse.RequestParser()
parser.add_argument('curapacs_customer', type=str, help='customer designation, e.g. c0100, c0594 ...', required=True)
parser.add_argument('component', type=str, help=f'Component name in: {config.CURAPACS_K8S_COMPONENTS.keys()}')
args = parser.parse_args(strict="true")


class Todo(Resource):
    def get(self, todo_id):
        abort_if_todo_doesnt_exist(todo_id)
        return TODOS[todo_id]

    def delete(self, todo_id):
        abort_if_todo_doesnt_exist(todo_id)
        del TODOS[todo_id]
        return '', 204

    def put(self, todo_id):
        args = parser.parse_args()
        task = {'task': args['task']}
        TODOS[todo_id] = task
        return task, 201


api.add_resource(OrthancInstancePodList, '/instances')

def main():
    app.run(debug=True)

if __name__ == '__main__':
    main()