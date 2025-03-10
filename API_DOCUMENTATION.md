# RoundCall v2 API Documentation

## Overview

RoundCall v2 is a learning management system that facilitates interaction between trainers and trainees. This API provides endpoints for managing lessons, questions, and tracking progress.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

The API uses JWT (JSON Web Token) authentication. Most endpoints require a valid access token.

### Token Format

Include the token in the Authorization header:

```
Authorization: Bearer <your_access_token>
```

## Error Responses

The API uses standard HTTP status codes and returns error messages in the following format:

```json
{
  "detail": "Error message description"
}
```

Common status codes:

- 200: Success
- 201: Created
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 422: Validation Error
- 500: Internal Server Error

## Endpoints

### Authentication

#### Register User

```http
POST /users/register
```

Register a new user (trainer or trainee).

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "strongpassword",
  "firstName": "John",
  "lastName": "Doe",
  "role": "Trainer" // or "Trainee"
}
```

**Response:** (201 Created)

```json
{
  "id": "user_id",
  "email": "user@example.com",
  "firstName": "John",
  "lastName": "Doe",
  "role": "Trainer",
  "createdAt": "2024-02-15T21:51:00Z"
}
```

#### Login

```http
POST /users/login
```

Authenticate user and get access token.

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "strongpassword"
}
```

**Response:** (200 OK)

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

#### Refresh Token

```http
POST /users/refresh
```

Get new access and refresh tokens using the current refresh token.

**Response:** (200 OK)

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

### User Management

#### Get Current User

```http
GET /users/me
```

Get the profile of the currently authenticated user.

**Response:** (200 OK)

```json
{
  "id": "user_id",
  "email": "user@example.com",
  "firstName": "John",
  "lastName": "Doe",
  "role": "Trainer",
  "createdAt": "2024-02-15T21:51:00Z"
}
```

#### Get Assigned Trainees (Trainer Only)

```http
GET /users/assigned-trainees
```

Get all trainees assigned to your lessons with their progress information.

**Response:** (200 OK)

```json
[
  {
    "id": "trainee_id",
    "email": "trainee@example.com",
    "firstName": "John",
    "lastName": "Doe",
    "totalAssignedLessons": 5,
    "completedLessons": 2,
    "inProgressLessons": 1,
    "notStartedLessons": 2,
    "completionRate": 40.0
  }
]
```

### Lesson Management

#### Create Lesson (Trainer Only)

```http
POST /lessons
```

Create a new lesson.

**Request Body:**

```json
{
  "title": "Introduction to Python",
  "description": "Learn Python basics",
  "contentType": "Text", // "Text", "Video", or "Both"
  "textContent": "Python is a versatile programming language...",
  "videoURL": "https://example.com/video",
  "questions": [
    {
      "questionText": "What is Python?",
      "options": ["A programming language", "A snake"],
      "correctAnswer": 0
    }
  ]
}
```

**Response:** (201 Created)

```json
{
  "id": "lesson_id",
  "title": "Introduction to Python",
  "description": "Learn Python basics",
  "contentType": "Text",
  "textContent": "Python is a versatile programming language...",
  "videoURL": "https://example.com/video",
  "questions": [...],
  "createdBy": "trainer_id",
  "createdAt": "2024-02-15T21:51:00Z"
}
```

#### Get Lessons

```http
GET /lessons
```

Get lessons (filtered by role - trainers see created lessons, trainees see assigned lessons).

**Response:** (200 OK)

```json
[
  {
    "id": "lesson_id",
    "title": "Introduction to Python",
    "description": "Learn Python basics",
    "contentType": "Text",
    "textContent": "Python is a versatile programming language...",
    "videoURL": "https://example.com/video",
    "questions": [...],
    "createdBy": "trainer_id",
    "createdAt": "2024-02-15T21:51:00Z"
  }
]
```

#### Update Lesson (Trainer Only)

```http
PUT /lessons/{lesson_id}
```

Update an existing lesson. Only the trainer who created the lesson can update it.

**Request Body:**
Same as Create Lesson

**Response:** (200 OK)
Same as Create Lesson Response

#### Delete Lesson (Trainer Only)

```http
DELETE /lessons/{lesson_id}
```

Delete a lesson and its associated assignments. Only the trainer who created the lesson can delete it.

**Response:** (200 OK)

```json
{
  "message": "Lesson deleted successfully"
}
```

#### Update Lesson Status (Trainee Only)

```http
PUT /lessons/{lesson_id}/status
```

Update the status of an assigned lesson.

**Request Body:**

```json
{
  "status": "In Progress" // "Assigned", "In Progress", or "Completed"
}
```

**Response:** (200 OK)

```json
{
  "message": "Lesson status updated successfully"
}
```

#### Assign Lesson (Trainer Only)

```http
POST /lessons/{lesson_id}/assign
```

Assign a lesson to a trainee. You can identify the trainee either by their ID or email address.

**Request Body:**

```json
{
  // Option 1: Using trainee_id
  "trainee_id": "trainee_user_id"

  // Option 2: Using trainee_email
  "trainee_email": "trainee@example.com"
}
```

**Response:** (200 OK)

```json
{
  "message": "Lesson assigned successfully to trainee@example.com"
}
```

**Possible Errors:**

- 400: Invalid trainee identification or lesson already assigned
- 403: Not a trainer or not your lesson
- 404: Lesson or trainee not found

#### Unassign Lesson (Trainer Only)

```http
DELETE /lessons/assigned/{assigned_lesson_id}
```

Remove a lesson assignment from a trainee. Only the trainer who created the lesson can unassign it.

**Response:** (200 OK)

```json
{
  "message": "Lesson unassigned successfully"
}
```

**Possible Errors:**

- 403: Not a trainer or not your lesson
- 404: Assigned lesson not found

### Question Management

#### Create Question (Trainer Only)

```http
POST /questions
```

Create a new question for a lesson.

**Request Body:**

```json
{
  "lessonID": "lesson_id",
  "questionText": "What is Python?",
  "options": {
    "A": "A programming language",
    "B": "A snake",
    "C": "A text editor",
    "D": "An operating system"
  },
  "correctAnswer": "A",
  "timeLimit": 60 // seconds
}
```

**Response:** (201 Created)

```json
{
  "id": "question_id",
  "lessonID": "lesson_id",
  "questionText": "What is Python?",
  "options": {
    "A": "A programming language",
    "B": "A snake",
    "C": "A text editor",
    "D": "An operating system"
  },
  "correctAnswer": "A",
  "timeLimit": 60,
  "trainerID": "trainer_id",
  "createdAt": "2024-02-15T21:51:00Z"
}
```

#### Get Lesson Questions

```http
GET /questions/lesson/{lesson_id}
```

Get all questions for a specific lesson.

**Response:** (200 OK)

```json
[
  {
    "id": "question_id",
    "lessonID": "lesson_id",
    "questionText": "What is Python?",
    "options": {
      "A": "A programming language",
      "B": "A snake",
      "C": "A text editor",
      "D": "An operating system"
    },
    "timeLimit": 60,
    "trainerID": "trainer_id",
    "createdAt": "2024-02-15T21:51:00Z"
  }
]
```

#### Answer Question (Trainee Only)

```http
POST /questions/answer
```

Submit an answer to a question.

**Request Body:**

```json
{
  "questionID": "question_id",
  "selectedAnswer": "A",
  "responseTime": 45.5 // seconds
}
```

**Response:** (200 OK)

```json
{
  "isCorrect": true,
  "selectedAnswer": "A",
  "correctAnswer": "A"
}
```

### Analytics

#### Get Lesson Analytics (Trainer Only)

```http
GET /analytics/lesson/{lesson_id}
```

Get analytics for a specific lesson.

**Response:** (200 OK)

```json
[
  {
    "id": "analytics_id",
    "trainerID": "trainer_id",
    "traineeID": "trainee_id",
    "lessonID": "lesson_id",
    "totalQuestions": 10,
    "correctAnswers": 8,
    "avgResponseTime": 45.5,
    "attempts": 1,
    "generatedAt": "2024-02-15T21:51:00Z"
  }
]
```

#### Get Trainee Analytics (Trainer Only)

```http
GET /analytics/trainee/{trainee_id}
```

Get analytics for a specific trainee.

**Response:** (200 OK)

```json
[
  {
    "id": "analytics_id",
    "trainerID": "trainer_id",
    "traineeID": "trainee_id",
    "lessonID": "lesson_id",
    "totalQuestions": 10,
    "correctAnswers": 8,
    "avgResponseTime": 45.5,
    "attempts": 1,
    "generatedAt": "2024-02-15T21:51:00Z"
  }
]
```

## Models

### User Model

```json
{
  "id": "string",
  "email": "string",
  "firstName": "string",
  "lastName": "string",
  "role": "Trainer | Trainee",
  "createdAt": "datetime",
  "updatedAt": "datetime"
}
```

### Lesson Model

```json
{
  "id": "string",
  "title": "string",
  "description": "string",
  "contentType": "Text | Video | Both",
  "textContent": "string",
  "videoURL": "string",
  "timeBased": "number", // Time limit in seconds (optional)
  "createdBy": "string", // Reference to User ID
  "createdAt": "datetime",
  "questions": [
    {
      "questionText": "string",
      "options": {
        "A": "string",
        "B": "string",
        "C": "string",
        "D": "string"
      },
      "correctAnswer": "string", // "A", "B", "C", or "D"
      "timeLimit": "number" // Time limit per question in seconds (optional)
    }
  ]
}
```

### AssignedLesson Model

```json
{
  "id": "string",
  "lessonID": "string",
  "traineeID": "string",
  "trainerID": "string",
  "status": "Assigned | In Progress | Completed",
  "startedAt": "datetime",
  "completedAt": "datetime",
  "assignedAt": "datetime",
  "maxAttempts": "number"
}
```

### Analytics Model

```json
{
  "id": "string",
  "trainerID": "string",
  "traineeID": "string",
  "lessonID": "string",
  "totalQuestions": "number",
  "correctAnswers": "number",
  "avgResponseTime": "number",
  "attempts": "number",
  "generatedAt": "datetime"
}
```

## Rate Limiting

The API implements rate limiting to prevent abuse. Limits are as follows:

- 100 requests per minute for authenticated users
- 20 requests per minute for unauthenticated users

## Security Recommendations

1. Always use HTTPS in production
2. Store tokens securely
3. Never share your tokens
4. Implement token refresh mechanism
5. Use strong passwords
