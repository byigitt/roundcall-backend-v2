# MongoDB Database Models

## Users Collection

```json
{
  "_id": "ObjectId",
  "email": "string",
  "password": "string (hashed)",
  "firstName": "string",
  "lastName": "string",
  "role": "Trainer | Trainee",
  "createdAt": "datetime",
  "updatedAt": "datetime"
}
```

## Lessons Collection

```json
{
  "_id": "ObjectId",
  "title": "string",
  "description": "string",
  "contentType": "Text | Video | Both",
  "textContent": "string",
  "videoURL": "string",
  "timeBased": "number", // Time limit in seconds (optional)
  "createdBy": "ObjectId", // Reference to Users._id
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

## AssignedLessons Collection

```json
{
  "_id": "ObjectId",
  "lessonID": "ObjectId", // Reference to Lessons._id
  "traineeID": "ObjectId", // Reference to Users._id (Trainee)
  "trainerID": "ObjectId", // Reference to Users._id (Trainer)
  "status": "Assigned | In Progress | Completed",
  "startedAt": "datetime",
  "completedAt": "datetime",
  "assignedAt": "datetime",
  "maxAttempts": "number"
}
```

## Analytics Collection

```json
{
  "_id": "ObjectId",
  "trainerID": "ObjectId", // Reference to Users._id (Trainer)
  "traineeID": "ObjectId", // Reference to Users._id (Trainee)
  "lessonID": "ObjectId", // Reference to Lessons._id
  "totalQuestions": "number",
  "correctAnswers": "number",
  "avgResponseTime": "number", // Average response time in seconds
  "attempts": "number",
  "generatedAt": "datetime"
}
```

## Indexes

### Users Collection

- `email`: Unique index
- `role`: Index for filtering users by role

### Lessons Collection

- `createdBy`: Index for filtering trainer's lessons
- `contentType`: Index for filtering lessons by type

### AssignedLessons Collection

- `traineeID`: Index for finding trainee's lessons
- `trainerID`: Index for finding trainer's assigned lessons
- `lessonID`: Index for finding lesson assignments
- `status`: Index for filtering by lesson status
- Compound index on `(traineeID, status)` for efficient trainee progress queries

### Analytics Collection

- `traineeID`: Index for finding trainee's performance
- `lessonID`: Index for finding lesson analytics
- `trainerID`: Index for finding trainer's analytics
- Compound index on `(lessonID, traineeID)` for efficient progress tracking

## Relationships

1. Users (Trainer) -> Lessons (One-to-Many)
   - A trainer can create multiple lessons
2. Users (Trainer) -> AssignedLessons (One-to-Many)
   - A trainer can assign lessons to multiple trainees
3. Users (Trainee) -> AssignedLessons (One-to-Many)
   - A trainee can have multiple assigned lessons
4. Lessons -> AssignedLessons (One-to-Many)
   - A lesson can be assigned to multiple trainees
5. AssignedLessons -> Analytics (One-to-One)
   - Each assigned lesson can have associated analytics

## Data Validation Rules

1. Users

   - Email must be unique and valid format
   - Password must be hashed before storage
   - Role must be either "Trainer" or "Trainee"

2. Lessons

   - Must have at least one question
   - Content type must match provided content (text/video/both)
   - Created by must reference a valid trainer user

3. AssignedLessons

   - Cannot be completed without a started date
   - Status transitions: Assigned -> In Progress -> Completed
   - Max attempts must be positive number

4. Analytics
   - Total questions must match lesson questions count
   - Correct answers cannot exceed total questions
   - Average response time must be positive number
