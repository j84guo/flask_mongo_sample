from uwlink import db

# The model classes here (anything which inherits from db.Document) represent data stored in the database
#
# Each class also has a to_dict method, which returns a dictionary of data that we intend to send back to the user in
# API responses. Having this method decouples the schema of the database from the schema of the API responses
#
# I got this idea from UWFlow (which is also a Flask+MongoDB project)
#
# https://github.com/UWFlow/rmc/blob/00bcc1450ffbec3a6c8d956a2a5d1bb3a04bfcb9/models/course.py


class Owner(db.Document):
    # Setting unique=True causes MongoEngine to create this collection with a unique index on this field
    #
    # https://docs.mongodb.com/manual/core/index-unique/
    username = db.StringField(unique=True)
    pets = db.ListField(db.StringField())
    joined_at = db.DateTimeField()

    def to_dict(self):
        return {
            "owner_id": str(self.id),
            "pets": self.pets,
            "joined_at": self.joined_at
        }


class Pet(db.Document):
    name = db.StringField()
    type = db.StringField()
    owner_id = db.StringField()

    def to_dict(self):
        return {
            "pet_id": str(self.id),
            "name": self.name,
            "type": self.type,
            "owner_id": self.owner_id
        }
