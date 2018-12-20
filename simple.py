from flask import Flask, url_for
from flask_restplus import Api, Resource, fields
from werkzeug.contrib.fixers import ProxyFix
from werkzeug.datastructures import FileStorage
import os
import json


app = Flask(__name__, static_url_path='')
app.wsgi_app = ProxyFix(app.wsgi_app)
api = Api(app, version='1.0', title='ItemMVC API',
    description='A simple ItemMVC API',
)

ns = api.namespace('items', description='Item operations')

item = api.model('Item', {
    'id': fields.Integer(readOnly=True, description='The item unique identifier'),
    'name': fields.String(required=True, description='The item title'),
    'description': fields.String(required=True, description='The item description'),
    'src': fields.String(required=True, description='The item image url')
})


class ItemDAO(object):
    def __init__(self):
        self.counter = 0
        self.items = []

    def get(self, id):
        for item in self.items:
            if item['id'] == id:
                return item
        api.abort(404, "Item {} doesn't exist".format(id))

    def create(self, data):
        item = data
        item['id'] = self.counter = self.counter + 1
        self.items.append(item)
        return item

    def update(self, id, data):
        item = self.get(id)
        item.update(data)
        return item

    def delete(self, id):
        item = self.get(id)
        self.items.remove(item)

    def load(self, filepath):
        with open(filepath, "r") as items_file:
            self.items = json.load(items_file)


DAO = ItemDAO()
DAO.load("items.json")


@ns.route('/')
class ItemList(Resource):
    '''Shows a list of all items, and lets you POST to add new tasks'''
    @ns.doc('list_items')
    @ns.marshal_list_with(item)
    def get(self):
        '''List all tasks'''
        return DAO.items

    @ns.doc('create_item')
    @ns.expect(item)
    @ns.marshal_with(item, code=201)
    def post(self):
        '''Create a new task'''
        return DAO.create(api.payload), 201


@ns.route('/<int:id>')
@ns.response(404, 'Item not found')
@ns.param('id', 'The task identifier')
class Item(Resource):
    '''Show a single item item and lets you delete them'''
    @ns.doc('get_item')
    @ns.marshal_with(item)
    def get(self, id):
        '''Fetch a given resource'''
        return DAO.get(id)

    @ns.doc('delete_item')
    @ns.response(204, 'Item deleted')
    def delete(self, id):
        '''Delete a task given its identifier'''
        DAO.delete(id)
        return '', 204

    @ns.expect(item)
    @ns.marshal_with(item)
    def put(self, id):
        '''Update a task given its identifier'''
        return DAO.update(id, api.payload)


upload_parser = api.parser()
upload_parser.add_argument('file', location='files', type=FileStorage, required=True)


@api.route('/upload/')
@api.expect(upload_parser)
class Upload(Resource):
    def post(self):
        args = upload_parser.parse_args() # upload a file
        uploaded_file = args['file']  # This is FileStorage instance
        file_path = os.path.join('/home/ubuntu/api-server/files', uploaded_file.filename)
        uploaded_file.save(file_path)
        url = url_for('static', filename=uploaded_file.filename)
        return {'url': url}, 201


@app.route('/files/<path:path>')
def send_file(path):
    return app.send_static_file(path)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')