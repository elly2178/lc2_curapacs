from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
import os

# import os for the paths in the python

app = Flask(__name__)
# shows the absolute path to the database and puts it in the basedir variable
basedir = os.path.abspath(os.path.dirname(__file__))
# Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite')
# dont need this code, but if you dont have it, the console will complain
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False

# inisialize db
db = SQLAlchemy(app)
# initialize mashmallow
ma = Marshmallow(app)

#Product class
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique =True)
    description = db.Column(db.String(1000))
    price = db.Column(db.Float)
    quantity = db.Column(db.Integer)

    # constructor
    def __init__(self,name, description, price, quantity):
        self.name = name
        self.description = description
        self.price = price
        self.quantity = quantity

# product schema
class ProductSchema(ma.Schema):
    class Meta:
        # these are the fealds you are allowed to show (the ones in the '')
        fields = ('id', 'name', 'description', 'price', 'quantity')
# initialize Schema, in the tut you had: strinct = True --> remove it so code will work
product_schema = ProductSchema()
# put strict = True --> no error in the cosole
products_schema = ProductSchema(many=True)


# this crates the db that was defined in the class ProductSchema
db.create_all()

# create a prodcut
@app.route('/product', methods = ['POST'])
def add_product():
    # var. for each element that you want to get. you get them with the request from a json file
    name = request.json['name']
    description = request.json['description']
    price = request.json['price']
    quantity = request.json['quantity']

    new_product = Product(name, description, price, quantity)

    db.session.add(new_product)
    #save to db
    db.session.commit()
    # this will be returned to the client
    return product_schema.jsonify(new_product)


# route to fetch all products 
@app.route('/product', methods=['GET'])
def get_products():
    all_products = Product.query.all()
    result = products_schema.dump(all_products)
    # in the tut: return jsonify(result.data) --> error. Remove .data and no error
    return jsonify(result)

# getting a single product
@app.route('/product/<id>', methods=['GET'])
def get_singleProduct(id):
    one_product = Product.query.get(id)
    return product_schema.jsonify(one_product)

# updateing a product
@app.route('/product/<id>', methods = ['PuT'])
def update_product(id):
    # get the product that you want
    product_to_update = Product.query.get(id)
    # get all the variables from the request:
    name = request.json['name']
    description = request.json['description']
    price = request.json['price']
    quantity = request.json['quantity']

    product_to_update.name = name
    product_to_update.description = description
    product_to_update.price = price
    product_to_update.quantity = quantity

    #save to db
    db.session.commit()
    # this will be returned to the client
    return product_schema.jsonify(product_to_update)

# Delete product
@app.route('/product/<id>', methods=['DELETE'])
def delete_product(id):
    delete_product = Product.query.get(id)
    db.session.delete(delete_product)
    db.session.commit()
    return product_schema.jsonify(delete_product)

# run server
if __name__ == "__main__":
    app.run(debug=True)
