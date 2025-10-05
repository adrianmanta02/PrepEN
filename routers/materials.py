from fastapi import APIRouter, Depends, HTTPException, Path, Request, Form, UploadFile, File, Query
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates 
from sqlalchemy import Column, String, DateTime, func, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import ARRAY
from starlette import status 
from typing import Annotated 
from pydantic import BaseModel
from models import Materials
from typing import List
from datetime import datetime, timezone
from descriptions import page_descriptions
import uuid 

# define the route within the page 
router = APIRouter(
    prefix = "/materials", 
    tags = ["materials"]
)

from .auth import db_dependency, get_current_user
from typing import Optional 

user_dependency = Annotated[dict, Depends(get_current_user)]

class MaterialResponse(BaseModel): 
    id: int
    title: str 
    description: str    
    thumbnail: Optional[str] = None 
    files: Optional[List[str]]
    grade: int 
    owner_id: int
    created_at: datetime 
    updated_at: Optional[datetime] = None 
    path: Optional[str] = None

# ------------------- PAGES ---------------------------
templates = Jinja2Templates(directory = "templates")

def get_presigned_url(filename): 
    # get the presigned URL in order to be able to download the files from the S3 Bucket in AWS
    try: 
        url = s3_client.generate_presigned_url('get_object', 
                                                Params = {'Bucket': S3_BUCKET, 
                                                        'Key': filename}, 
                                                ExpiresIn = 3600)
    except: 
        url = None
    return url

def redirect_to_login(): 
    """Sends the user to the login page if the autentication went unsuccessfully and deletes 
    the cookie containing the JWT Token"""

    redirect_response = RedirectResponse(url = "/auth/login-page", status_code=status.HTTP_302_FOUND)
    redirect_response.delete_cookie(key="access_token")
    return redirect_response

def redirect_to_main_page(): 
    """Sends the student to the main page if they are trying to create a new section. 
    Only teachers have the right to do so."""

    redirect_response = RedirectResponse(url = "/materials/main-page", status_code = status.HTTP_302_FOUND)
    return redirect_response

@router.get("/main-page")
async def render_main_page(request: Request): 
    try: 
        token = request.cookies.get("access_token")
        user = await get_current_user(token = token)

        if user is None: 
            return redirect_to_login() 
        
        # else, pop the main page and let user interact with all subjects 
        return templates.TemplateResponse("main.html", {'request': request, 'user': user})
    except: 
        return redirect_to_login()
    
@router.get("/subject-2")
async def render_subject_2(request: Request):
    try: 
        user = await get_current_user(request.cookies.get('access_token'))
        if user is None: 
            return redirect_to_login() 
        
        return templates.TemplateResponse("subject-2.html", {'request': request, 'user': user})
    except Exception as e: 
        print(f"Error: {e}")
        return redirect_to_login() 

@router.get("/view/{materialId}")
async def render_view_material(request: Request, db: db_dependency,
                               materialId: int = Path(gt = 0)): 
    try: 
        currentToken = request.cookies.get("access_token")
        user = await get_current_user(token = currentToken)
        
        if not user: 
            return redirect_to_login() 
        
        print("Sunt aici")
        material = db.query(Materials).filter(Materials.id == materialId).first()

        if not material: 
            return redirect_to_main_page() 
        
        # get the presigned urls -> load them into the html file to allow downloading 
        # from the AWS S3 Bucket 

        thumbnailUrl = get_presigned_url(filename = material.thumbnail)
        fileUrls = [get_presigned_url(filename = file) for file in material.files]

        return templates.TemplateResponse("material.html", {'request': request, 
                                                            'material': material,
                                                            'user': user, 
                                                            'thumbnailUrl': thumbnailUrl, 
                                                            'fileUrls': fileUrls}
                                        )
    except Exception as e:  
        print(f'Error: {e}')
        return redirect_to_main_page() 
    
@router.get("/{subject}/{part}")
async def render_materials_page(request: Request, 
                                subject: str, part: str, 
                                db: db_dependency): 
    try: 
        currentToken =  request.cookies.get('access_token')
        print(currentToken)
        user = await get_current_user(token = currentToken)
        print(user)

        if user is None: 
            return redirect_to_login() 
    
        pathName = f"/materials/{subject}/{part}"
        materials = await show_all_materials(db = db, 
                                             pathGiven = pathName, 
                                             user = user)
        if materials: 
            print(materials)
            for material in materials: 
                print(material.title)
                print(material.description)
                print(material.thumbnail)
                for file in material.files: 
                    print(file)
        
                print(material.grade)
                print(material.owner_id)
                print(material.path)

        # for each teaching material, get the specific thumbnail from the S3 Bucket 
        thumbnailUrls = [] 
        for material in materials: 
            url = get_presigned_url(filename = material.thumbnail)
            thumbnailUrls.append(url)
        

        return templates.TemplateResponse("materials-page.html", 
                                          {'request': request, 'materials': materials, 
                                           'subject': subject, 'part': part, 
                                           'user': user, 'thumbnailUrls': thumbnailUrls, 
                                           'page_descriptions': page_descriptions[part]})
    
    except Exception as e:
        print(f"Error: {e} awaweaweaw") 
        return redirect_to_login() 
    
@router.get('/add-material')
async def render_add_material_page(request: Request, 
                                   db: db_dependency,
                                   materialId: int = None
                                   ): 
    try: 
        teacher = await get_current_user(token = request.cookies.get('access_token'))
        if teacher is None:
            return redirect_to_login()

        if teacher.get('role') != 'teacher': 
            raise HTTPException(status_code = status.HTTP_403_FORBIDDEN, 
                                detail = "Only teachers can add materials on the platform.")
        
        thumbnailUrl = None
        material_to_edit = None
        fileUrls = []

        if materialId: 
            material_to_edit = db.query(Materials).filter(Materials.id == materialId).first() 
            if not material_to_edit: 
                raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, 
                                    detail = "The material with the ID given was not found!")
            
            # teaching material found -> load the presigned URLs in the page 
            # get the url for the thumbnail, as well as for each file loaded 

            thumbnailUrl = get_presigned_url(filename = material_to_edit.thumbnail)
            fileUrls = [get_presigned_url(filename = file) for file in material_to_edit.files]

    
        return templates.TemplateResponse("add-material.html", 
                                          {'request': request,
                                           'material': material_to_edit, 
                                           'user': teacher,
                                           'thumbnailUrl': thumbnailUrl, 
                                           'fileUrls': fileUrls}
                                           )
    except: 
        return redirect_to_login() 
    
# -------------------- ENDPOINTS -----------------------

import boto3
import os
from dotenv import load_dotenv

load_dotenv() # loading the variables from .env

# for importing the files to the AWS S3 Bucket, we need an s3 client 
s3_client = boto3.client("s3",
                         region_name = "eu-north-1", 
                         aws_access_key_id = os.getenv("AWS_ACCESS_KEY"), 
                         aws_secret_access_key= os.getenv("AWS_SECRET_ACCESS_KEY"))
S3_BUCKET = os.getenv("BUCKET")

@router.post("/material", response_model= MaterialResponse, 
             status_code = status.HTTP_201_CREATED)
async def create_material(db: db_dependency,
                          user: dict = Depends(get_current_user),
                          title: str = Form(..., min_length = 3), 
                          description: str = Form(..., min_length = 3), 
                          thumbnail: Optional[UploadFile] = File(None), 
                          grade: int = Form(..., ge = 5, le = 8), 
                          files: List[UploadFile] = File(...), 
                          path: str = Form(...) # even if it is not placed manually, it is managed by base.js 
                          ): 
    
    if user is None or user.get('role') != "teacher": 
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = 'Access not granted. You do not have permissions for that!')

    # upload the file details into Materials database
    # make the connection with the S3 server that will host all the files uploaded
    
    thumbnail_path = None
    if thumbnail and thumbnail.filename: # verify if there is any file and has a name (empty thumbnails are objects and have "" as filename!) 
        thumbnail_path = f"{uuid.uuid4()}_{thumbnail.filename}"
        s3_client.upload_fileobj(thumbnail.file, S3_BUCKET, thumbnail_path)

    file_paths = []

    for file in files: 
        # manage conflicts (if multiple teachers are trying to upload the same-named file, one will override the other)
        unique_filename = f"{uuid.uuid4()}_{file.filename}" # unique filename using uuid.uuid4() 
        s3_client.upload_fileobj(file.file, S3_BUCKET, unique_filename)

        # save the unique filenames in the database as well 
        file_paths.append(unique_filename)

    # create the new entry with the data given 
    new_material = Materials(
        title = title, 
        description = description, 
        thumbnail = thumbnail_path, 
        files = file_paths, 
        grade = grade, 
        path = path,
        owner_id = user.get('id')
    )

    db.add(new_material)
    db.commit()  # commit changes into the database 
    db.refresh(new_material) # brings any field automatically generated by the database 

    return new_material 


from sqlalchemy import desc, case 

async def show_all_materials(db: db_dependency, 
                             pathGiven: str,
                             user: dict = Depends(get_current_user)
                            ): 
    """Shows all the materials on a certain section"""

    if user is None: 
        raise HTTPException(status_code=401, detail="Could not validate user.")

    order_case = case(
        (Materials.updated_at != None, Materials.updated_at),  # note: fără listă
        else_=Materials.created_at
    )

    query = db.query(Materials).filter(Materials.path == pathGiven)

    if user.get('role') != 'teacher':
        query = query.filter(Materials.grade <= user['grade'])

    materials = query.order_by(desc(order_case)).all()
    return materials

import botocore
@router.delete("/material/{materialId}", status_code = status.HTTP_200_OK)
async def delete_material(db: db_dependency, 
                          user: dict = Depends(get_current_user), 
                          materialId: int = Path(gt = 0)): 
    if user is None or user.get('role') != 'teacher': 
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = 'Access not granted. You do not have permissions for that!')
    
    # user exists and it is a teacher :D
    searched_material = db.query(Materials).filter(Materials.id == materialId).first() 
    if searched_material is None: 
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = "Could not find the material with the ID given.")

    # material found !
    # make sure to delete the files stored in the Bucket as well! 
    thumbnail = searched_material.thumbnail # string only 
    files = searched_material.files # list of strings 

    # search in the bucket
    for file in files: 
        if file: 
            try: 
                s3_client.delete_object(Bucket = S3_BUCKET, Key = file)
            except botocore.exceptions.ClientError as e: 
                print("Could not delete file {file}: {e}")

    if thumbnail: 
        try: 
            s3_client.delete_object(Bucket = S3_BUCKET, Key = thumbnail)
        except botocore.exceptions.ClientError as e: 
            print("Could not delete thumbnail {thumbnail}: {e}")

    # erase data from the database 
    db.delete(searched_material)
    db.commit() 

@router.put("/material/edit/{materialId}", status_code = status.HTTP_204_NO_CONTENT)
async def edit_material(db: db_dependency, 
                        user: user_dependency,
                        title: str = Form(..., min_length = 3), 
                        description: str = Form(..., min_length = 3), 
                        thumbnail: Optional[UploadFile] = File(None), 
                        grade: int = Form(..., ge = 5, le = 8), 
                        files: Optional[List[UploadFile]] = File(None),
                        existing_files: Optional[List[str]] = Form(None), 
                        materialId: int = Path(gt=0)
                        ): 
    if not user: 
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, 
                            detail = "Could not validate user.")
    
    if user.get('role') != 'teacher': 
        raise HTTPException(status_code = status.HTTP_403_FORBIDDEN,
                            detail = "Only teachers can update files inside the platform!")
    
    material_to_edit = db.query(Materials).filter(Materials.id == materialId).first() 
    if not material_to_edit: 
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, 
                            detail = "Could not find the material with the ID given!")

    # edit the desired material
    material_to_edit.title = title
    material_to_edit.description = description
    
    if thumbnail and thumbnail.filename:
        thumbnailPath = f"{uuid.uuid4()}_{thumbnail.filename}"
        s3_client.upload_fileobj(thumbnail.file, S3_BUCKET, thumbnailPath)
        material_to_edit.thumbnail = thumbnailPath

    filePaths = [] 
    if existing_files: 
        filePaths.extend(existing_files)

    if files:
        for file in files:
            if file and file.filename:  
                unique_filename = f"{uuid.uuid4()}_{file.filename}"
                s3_client.upload_fileobj(file.file, S3_BUCKET, unique_filename)
                filePaths.append(unique_filename)

    material_to_edit.files = filePaths
    material_to_edit.grade = grade 

    # manage last edit time 
    material_to_edit.updated_at = datetime.now(timezone.utc)

    db.add(material_to_edit)
    db.commit() 
    db.refresh(material_to_edit)

@router.delete("/material/{materialId}/file")
async def remove_file_from_material(materialId: int,
                                    db: db_dependency,
                                    user: user_dependency,
                                    filename: str = Query(...)):
    
    if not user or user.get("role") != "teacher":
        raise HTTPException(status_code=403, detail="Not authorized. Only teachers can modify items!")

    material = db.query(Materials).filter(Materials.id == materialId).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    # decode the URL-encoded material 
    from urllib.parse import unquote
    decoded_filename = unquote(filename)
    
    if decoded_filename not in material.files:
        raise HTTPException(status_code=404, detail=f"File not found in material. Available: {material.files}")

    # remove from S3 bucket
    try:
        s3_client.delete_object(Bucket=S3_BUCKET, Key=decoded_filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete from S3: {str(e)}")

    # remove from DB - PostgreSQL ARRAY requires special handling
    try:
        material.files = [f for f in material.files if f != decoded_filename]
        material.updated_at = datetime.now(timezone.utc)
        
        # Force SQLAlchemy to recognize the change
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(material, "files")
        
        db.commit()
        db.refresh(material)

    except Exception as e:
        db.rollback()
        print(f"DB update error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update database: {str(e)}")

    return {"detail": f"File {decoded_filename} removed successfully", "remaining_files": material.files}
