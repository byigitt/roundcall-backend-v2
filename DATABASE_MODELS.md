# MongoDB Database Models

## Users Collection

```json
{
  "_id": "507f1f77bcf86cd799439011",
  "email": "john.doe@example.com",
  "password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKxcQw8SI9U4o/C",
  "firstName": "John",
  "lastName": "Doe",
  "role": "Trainer", // "Trainer" or "Trainee"
  "createdAt": "2024-02-15T10:30:00.000Z",
  "updatedAt": "2024-02-15T10:30:00.000Z"
}
```

## Lessons Collection

```json
{
  "_id": "507f1f77bcf86cd799439012",
  "title": "Introduction to Python",
  "description": "Learn the basics of Python programming language",
  "contentType": "Both", // "Text", "Video", or "Both"
  "textContent": "Python is a versatile programming language...",
  "videoURL": "https://example.com/video/python-intro",
  "timeBased": 3600, // Time limit in seconds (optional)
  "createdBy": "507f1f77bcf86cd799439011", // Reference to Users._id
  "createdAt": "2024-02-15T11:00:00.000Z",
  "updatedAt": "2024-02-15T11:30:00.000Z",
  "questions": [
    {
      "questionText": "What is Python?",
      "options": [
        {
          "text": "A programming language",
          "isCorrect": true
        },
        {
          "text": "A snake",
          "isCorrect": false
        },
        {
          "text": "A text editor",
          "isCorrect": false
        }
      ],
      "timeLimit": 60 // Time limit per question in seconds (optional)
    }
  ]
}
```

## AssignedLessons Collection

```json
{
  "_id": "507f1f77bcf86cd799439013",
  "lessonID": "507f1f77bcf86cd799439012", // Reference to Lessons._id
  "traineeID": "507f1f77bcf86cd799439014", // Reference to Users._id (Trainee)
  "trainerID": "507f1f77bcf86cd799439011", // Reference to Users._id (Trainer)
  "status": "In Progress", // "Assigned", "In Progress", or "Completed"
  "startedAt": "2024-02-15T12:00:00.000Z",
  "completedAt": null,
  "assignedAt": "2024-02-15T11:45:00.000Z",
  "maxAttempts": 1
}
```

## Analytics Collection

```json
{
  "_id": "507f1f77bcf86cd799439015",
  "trainerID": "507f1f77bcf86cd799439011", // Reference to Users._id (Trainer)
  "traineeID": "507f1f77bcf86cd799439014", // Reference to Users._id (Trainee)
  "lessonID": "507f1f77bcf86cd799439012", // Reference to Lessons._id
  "totalQuestions": 10,
  "correctAnswers": 8,
  "avgResponseTime": 45.5, // Average response time in seconds
  "attempts": 1,
  "generatedAt": "2024-02-15T13:00:00.000Z"
}
```

## ChatSessions Collection

```json
{
  "_id": "507f1f77bcf86cd799439016",
  "traineeID": "507f1f77bcf86cd799439014", // Reference to Users._id (Trainee)
  "characterType": "happy_customer",
  "messages": [
    {
      "role": "customer",
      "content": "İyi günler! Komşum sizin kampanyanızdan bahsetti, memnun kalmış. Ben de fiber internet düşünüyorum.",
      "timestamp": "2024-02-15T14:00:00.000Z"
    },
    {
      "role": "agent",
      "content": "Hoş geldiniz! Size nasıl yardımcı olabilirim?",
      "timestamp": "2024-02-15T14:01:00.000Z"
    }
  ],
  "createdAt": "2024-02-15T14:00:00.000Z",
  "updatedAt": "2024-02-15T14:01:00.000Z",
  "isActive": true,
  "collectedInfo": {
    "fiyat": false,
    "taahhut": false,
    "hiz": false,
    "kurulum": false,
    "cayma_bedeli": false
  }
}
```

## Example Relationships

1. A Trainer creates Lessons
2. Trainer assigns Lessons to Trainees (creates AssignedLessons)
3. Trainees complete Lessons, generating Analytics
4. Trainees can have ChatSessions for practice

## Indexes

### Users Collection

- `email`: Unique index
- `role`: Index for filtering

### Lessons Collection

- `createdBy`: Index for filtering trainer's lessons

### AssignedLessons Collection

- `traineeID`: Index for finding trainee's lessons
- `trainerID`: Index for finding trainer's assigned lessons
- `lessonID`: Index for finding lesson assignments

### Analytics Collection

- `traineeID`: Index for finding trainee's performance
- `lessonID`: Index for finding lesson analytics

### ChatSessions Collection

- `traineeID`: Index for finding trainee's chat sessions
- `isActive`: Index for finding active sessions
