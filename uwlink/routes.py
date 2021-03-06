import datetime

from flask import Blueprint, jsonify, request, render_template, flash, redirect, url_for
from flask_login import UserMixin, current_user, login_required, login_user
from mongoengine.errors import DoesNotExist
from uwlink import login_manager
from uwlink.forms import LoginForm, SignupForm
from uwlink.models import Owner, Pet
from werkzeug.security import check_password_hash, generate_password_hash


# In Flask, a blueprint is just a group of related routes (the functions below), it helps organize your code
routes = Blueprint('api', __name__)


class User(UserMixin):
    def __init__(self, owner):
        self.id = owner.id
        self.owner = owner


@login_manager.user_loader
def user_loader(owner_id):
    try:
        owner = Owner.objects.get(id=owner_id)
        return User(owner)
    except DoesNotExist:
        return None


# Signup creates a new user. Note that we store a HASH of the user's password - this is a common practice. On login,
# the provided password will be hashed, and that hash will be compared to the stored hash for the user
#
# https://en.wikipedia.org/wiki/Cryptographic_hash_function#Password_verification
@routes.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        owner = Owner(username=form.username.data,
                      pets=[],
                      joined_at=datetime.datetime.now(),
                      hashed_password=generate_password_hash(form.password.data))
        owner.save()
        flash('You have been signed up!')
        return redirect(url_for('.login'))
    return render_template('signup.html', form=form)

@routes.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        try:
            owner = Owner.objects.get(username=form.username.data)
            if check_password_hash(owner.hashed_password, form.password.data):
                user = User(owner)
                login_user(user)
                return "logged in"
        except DoesNotExist:
            pass
    return render_template('login.html', form=form)


# Getting all the documents in a collection is usually not a good idea (too many), but this is just provided to help you
# explore the database through the API
@routes.route('/owners', methods=['GET'])
@login_required
def get_all_owners():
    # Owner.objects is an iterable that will iterate over all documents from the owner collection in MongoDB. We
    # construct a list out of this iterable and convert it to json
    return jsonify([o.to_dict() for o in Owner.objects])


@routes.route('/owners/<string:owner_id>', methods=['GET'])
@login_required
def get_owner(owner_id):
    # In MongoDB, all documents have an implicit _id primary key - MongoEngine allows you to lookup documents by _id
    # using the id keyword argument
    #
    # https://docs.mongodb.com/manual/core/document/
    #
    # The get_or_404 method causes Flask to return an HTTP 404 response if the document could not be found
    return Owner.objects.get_or_404(id=owner_id).to_dict()


@routes.route('/pets', methods=['GET'])
@login_required
def get_all_pets():
    return jsonify([o.to_dict() for o in Pet.objects])


@routes.route('/pets/<string:pet_id>', methods=['GET'])
@login_required
def get_pet(pet_id):
    return Pet.objects.get_or_404(id=pet_id).to_dict()


@routes.route('/pets', methods=['POST'])
@login_required
def create_pet():
    request_json = request.get_json()

    # Get owner_id from the provided JWT token
    owner_id = current_user.get_id()

    # Get the current owner (throws exception if doesn't exist)
    owner = Owner.objects.get(id=owner_id)

    # Create the new pet
    pet = Pet(name=request_json['name'],
              type=request_json['type'],
              owner_id=owner_id)
    pet.save()

    # Add the pet to the owner's list of pets and save the updated owner
    owner.pets.append(str(pet.id))
    owner.save()

    # You might be familar with the concept of transactions. A transaction is
    # a group of operations which must either all succeed or all fail - this
    # preserves data consistency. In a production application, you could argue
    # that this function should indeed perform a transaction with the database
    # (which MongoDB supports).
    #
    # For our prototype, this might be overkill. You can explore transactions
    # if you're interested.
    #
    # https://docs.mongodb.com/manual/core/transactions/
    return pet.to_dict()
