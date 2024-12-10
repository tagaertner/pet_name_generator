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
    
    try:
        temp_pet = Pet(
            animal_type=request_body["animal_type"],
            personality=request_body["personality"],
            color=request_body["color"]
            )
        # generate name using ai
        new_name = generate_name(temp_pet)
        request_body["name"] = new_name
        
        # create new pet with generated name
        new_pet = Pet(
            name=new_name,
            animal_type=request_body.get("animal_type"),
            personality=request_body.get("personality"),
            color=request_body.get("color")
        )
        
        db.session.add(new_pet)
        db.session.commit()
        
        return new_pet.to_dict(), 201

    except KeyError as missing_field:
        abort(make_response({"message": f"Missing required field: {missing_field}"}, 400))
    except Exception as error:
        abort(make_response({"message": f"Error creating pet: {str(error)}"}, 500))

def generate_name(pet):
    model = genai.GenerativeModel("gemini-1.5-flash")
    input_message = f"Please generate one suitable name based on {pet.animal_type} with a {pet.personality} and a {pet.color} color and remove all description."
    response = model.generate_content(input_message)
    response_name = response.text.strip("\n")
    print(response)
    return response_name

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