from flask import Flask, jsonify, request
from flask_mongoengine import MongoEngine

app = Flask(__name__)
app.config['MONGODB_SETTINGS'] = {
    'db': 'mydatabase',
    'host': 'mongodb://localhost/mydatabase'}

db = MongoEngine(app)


# User Model
class User(db.Document):
    username = db.StringField(unique=True, required=True)
    password = db.StringField(required=True)
    is_active = db.BooleanField(default=True)
    role = db.StringField(choices=['admin', 'client'])


# Registration
@app.route('/register', methods=['POST'])
def register():
    username = request.json.get('username')
    password = request.json.get('password')
    role = request.json.get('role')

    # User Control
    existing_user = User.objects(username=username).first()
    if existing_user:
        return jsonify({'message': 'user already registered'}), 400


    user = User(username=username, password=password, role=role)
    user.save()

    return jsonify({'message': 'Registration Successful'}), 201


# Login
@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')

    # User and password control
    user = User.objects(username=username).first()
    if user and user.password == password:
        return jsonify({'message': 'Login Successful'}), 200

    return jsonify({'message': 'Invalid username or password'}), 401



# Deactivate User
@app.route('/deactivate', methods=['POST'])
def deactivate_user():
    username = request.json.get('username')

    current_user = User.objects(username=request.json.get('current_user')).first()
    if not current_user or current_user.role != 'admin':
        return jsonify({'message': 'You are not authorized to perform this action'}), 403

    user = User.objects(username=username).first()
    if not user:
        return jsonify({'message': 'User not found'}), 404

    user.is_active = False
    user.save()

    return jsonify({'message': 'User deactivated'}), 200



# Product model
class Product(db.Document):
    name = db.StringField(required=True)
    amount_in_stock = db.IntField(required=True)
    price = db.FloatField(required=True)
    in_stock = db.BooleanField(default=True)

# Display products
def get_products():
    products = Product.objects(in_stock=True).all()
    result = []
    for product in products:
        result.append({
            'id': str(product.id),
            'name': product.name,
            'amount_in_stock': product.amount_in_stock,
            'price': product.price,
            'in_stock': product.in_stock
        })
    return jsonify(result), 200

# Add product
@app.route('/products', methods=['POST'])
def create_product():
    current_user = User.objects(username=request.json.get('current_user')).first()
    if not current_user or current_user.role != 'admin':
        return jsonify({'message': 'You are not authorized to perform this action'}), 403

    name = request.json.get('name')
    amount_in_stock = request.json.get('amount_in_stock')
    price = request.json.get('price')
    in_stock = request.json.get('in_stock', True)

    product = Product(name=name, amount_in_stock=amount_in_stock, price=price, in_stock=in_stock)
    product.save()

    return jsonify({'message': 'The product has been successfully created'}), 201

# update product
@app.route('/products/<product_id>', methods=['PUT'])
def update_product(product_id):

    current_user = User.objects(username=request.json.get('current_user')).first()
    if not current_user or current_user.role != 'admin':
        return jsonify({'message': 'You are not authorized to perform this action'}), 403

    product = Product.objects(id=product_id).first()
    if not product:
        return jsonify({'message': 'Product not found'}), 404

    product.name = request.json.get('name', product.name)
    product.amount_in_stock = request.json.get('amount_in_stock', product.amount_in_stock)
    product.price = request.json.get('price', product.price)
    product.in_stock = request.json.get('in_stock', product.in_stock)
    product.save()

    return jsonify({'message': 'The product has been successfully updated'}), 200

# delete product
@app.route('/products/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    current_user = User.objects(username=request.json.get('current_user')).first()
    if not current_user or current_user.role != 'admin':
        return jsonify({'message': 'You are not authorized to perform this action'}), 403

    product = Product.objects(id=product_id).first()
    if not product:
        return jsonify({'message': 'Product not found'}), 404

    product.delete()

    return jsonify({'message': 'The product has been successfully deleted'}), 200

# category model
class Category(db.Document):
    name = db.StringField(required=True)


# create category
@app.route('/categories', methods=['POST'])
def create_category():
    if request.json['current_user'] != 'admin':
        return jsonify({'message': 'You are not authorized to perform this action'}), 403

    name = request.json['name']

    category = Category(name=name)
    category.save()

    return jsonify({'message': 'The category has been successfully created'}), 201


# update category
@app.route('/categories/<category_id>', methods=['PUT'])
def update_category(category_id):
    if request.json['current_user'] != 'admin':
        return jsonify({'message': 'You are not authorized to perform this action'}), 403

    category = Category.objects(id=category_id).first()
    if not category:
        return jsonify({'message': 'category not found'}), 404

    name = request.json['name']

    category.name = name
    category.save()

    return jsonify({'message': 'The category has been successfully updated'}), 200


# delete category
@app.route('/categories/<category_id>', methods=['DELETE'])
def delete_category(category_id):
    if request.json['current_user'] != 'admin':
        return jsonify({'message': 'You are not authorized to perform this action'}), 403

    category = Category.objects(id=category_id).first()
    if not category:
        return jsonify({'message': 'category not found'}), 404

    category.delete()

    return jsonify({'message': 'The category has been successfully deleted'}), 200


cart = db.DictField()


# add to cart product
@app.route('/cart', methods=['POST'])
def add_to_cart():
    username = request.json['username']
    password = request.json['password']
    product_id = request.json['product_id']
    quantity = request.json['quantity']

    user = User.objects(username=username, password=password, is_active=True).first()
    if not user:
        return jsonify({'message': 'User not found or account not active'}), 404

    product = Product.objects(id=product_id, in_stock=True).first()
    if not product:
        return jsonify({'message': 'Product not found or out of stock'}), 404

    if 'cart' not in user:
        user.cart = {}

    if product_id in user.cart:
        user.cart[product_id] += quantity
    else:
        user.cart[product_id] = quantity

    user.save()

    return jsonify({'message': 'Product added to cart'}), 200


# view cart
@app.route('/cart', methods=['GET'])
def view_cart():
    username = request.json['username']
    password = request.json['password']

    user = User.objects(username=username, password=password, is_active=True).first()
    if not user:
        return jsonify({'message': 'User not found or account not active'}), 404

    cart = user.cart
    result = []
    total_price = 0

    for product_id, quantity in cart.items():
        product = Product.objects(id=product_id, in_stock=True).first()
        if product:
            total_price += product.price * quantity
            result.append({
                'product_id': str(product.id),
                'product_name': product.name,
                'quantity': quantity,
                'subtotal': product.price * quantity
            })

    return jsonify({
        'cart': result,
        'total_price': total_price
    }), 200


if __name__ == '__main__':
    app.run(debug=True)
