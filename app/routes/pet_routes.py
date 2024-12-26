from flask import Blueprint, request, abort, make_response
from ..db import db
from ..models.pet import Pet
import google.generativeai as genai
import os

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

bp = Blueprint("pets", __name__, url_prefix="/pets")

@bp.post("")
def create_pet():
    request_body = request.get_json()
    request_body["name"] = generate_name(request_body)
    try: 
        new_pet = Pet.from_dict(request_body)
        db.session.add(new_pet)
        db.session.commit()

        return make_response(new_pet.to_dict(), 201)
    
    except KeyError as e:
        abort(make_response({"message": f"missing required value: {e}"}, 400))

@bp.patch("/<pet_id>")
def update_pet_name(pet_id):
    pet = validate_model(Pet, pet_id)
    pet_dict = pet.to_dict()
    new_name = generate_name(pet_dict)

    pet.name = new_name
    db.session.add(pet)
    db.session.commit()

    return pet_dict, 201



@bp.get("")
def get_pets():
    pet_query = db.select(Pet)

    pets = db.session.scalars(pet_query)
    response = []

    for pet in pets:
        response.append(pet.to_dict())

    return response

@bp.get("/<pet_id>")
def get_single_pet(pet_id):
    pet = validate_model(Pet,pet_id)
    return pet.to_dict()

def generate_name(request):
    model = genai.GenerativeModel("gemini-1.5-flash")

    if request["name"]:
        input_message = f"I have a {request["coloration"]} {request["animal"]} named {request["name"]}. They are very {request["personality"]}. I'm not a huge fan of the name though, could you suggest another? Just the name, nothing else."
    else:
        input_message = f"I have a {request["animal"]} who is {request["coloration"]} and {request["personality"]}. Please give me a name for them? Just the name, nothing else."

    response = model.generate_content(input_message)
    print(response.text)
    return response.text.strip()

def validate_model(cls,id):
    try:
        id = int(id)
    except:
        response =  response = {"message": f"{cls.__name__} {id} invalid"}
        abort(make_response(response , 400))

    query = db.select(cls).where(cls.id == id)
    model = db.session.scalar(query)
    if model:
        return model

    response = {"message": f"{cls.__name__} {id} not found"}
    abort(make_response(response, 404))