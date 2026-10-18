
import os
from pathlib import Path

import mysql.connector 
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "student_manager"),
    )


class Student(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=254)
    age: int = Field(ge=1, le=120)
    department: str = Field(min_length=1, max_length=100)


@app.get("/")
def home():
    return FileResponse(BASE_DIR / "index.html")


@app.get("/students")
def get_students():
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, name, email, age, department "
            "FROM students ORDER BY id DESC"
        )
        return cursor.fetchall()

    except mysql.connector.Error as error:
        raise HTTPException(
            status_code=500,
            detail="Could not retrieve students. Check the MySQL connection."
        ) from error

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@app.post("/students")
def add_student(student: Student):
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO students (name, email, age, department)
            VALUES (%s, %s, %s, %s)
            """,
            (
                student.name.strip(),
                student.email.strip(),
                student.age,
                student.department.strip(),
            ),
        )

        connection.commit()
        student_id = cursor.lastrowid

        return {
            "message": "Student saved successfully!",
            "id": student_id,
        }

    except mysql.connector.Error as error:
        if connection and connection.is_connected():
            connection.rollback()

        raise HTTPException(
            status_code=500,
            detail="Could not save student. Check the MySQL connection."
        ) from error

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@app.delete("/students/{student_id}")
def delete_student(student_id: int):
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "DELETE FROM students WHERE id = %s",
            (student_id,),
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Student not found."
            )

        connection.commit()
        return {"message": "Student deleted successfully!"}

    except HTTPException:
        raise

    except mysql.connector.Error as error:
        if connection and connection.is_connected():
            connection.rollback()

        raise HTTPException(
            status_code=500,
            detail="Could not delete student. Check the MySQL connection."
        ) from error

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

