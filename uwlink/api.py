import datetime

from flask import Blueprint, jsonify, request
from uwlink.models import Owner, Pet

# In Flask, a blueprint is just a group of related routes (the functions below), it helps organize your code
api = Blueprint('api', __name__)


# Getting all the documents in a collection is usually not a good idea (too many), but this is just provided to help you
# explore the database through the API
@api.route('/owners', methods=['GET'])
def get_all_owners():
    # Owner.objects is an iterable that will iterate over all documents from the owner collection in MongoDB. We
    # construct a list out of this iterable and convert it to json
    return jsonify([o.to_dict() for o in Owner.objects])


@api.route('/owners/<string:owner_id>', methods=['GET'])
def get_owner(owner_id):
    # In MongoDB, all documents have an implicit _id primary key - MongoEngine allows you to lookup documents by _id
    # using the id keyword argument
    #
    # https://docs.mongodb.com/manual/core/document/
    #
    # The get_or_404 method causes Flask to return an HTTP 404 response if the document could not be found
    return Owner.objects.get_or_404(id=owner_id).to_dict()


@api.route('/owners', methods=['POST'])
def create_owner():
    request_json = request.get_json()
    owner = Owner(username=request_json['username'],
                  pets=[],
                  joined_at=datetime.datetime.now())
    owner.save()
    return owner.to_dict()


@api.route('/pets', methods=['GET'])
def get_all_pets():
    return jsonify([o.to_dict() for o in Pet.objects])


@api.route('/pets/<string:pet_id>', methods=['GET'])
def get_pet(pet_id):
    return Pet.objects.get_or_404(id=pet_id).to_dict()


@api.route('/pets', methods=['POST'])
def create_pet():
    request_json = request.get_json()

    # Once authentication is added, it would make sense to simply extract the owner_id from the current
    # logged-in user. After all, a user shouldn't really be able to modify OTHER users' list of pets - just
    # their own!
    owner_id = request_json['owner_id']

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
