# RoundCall Backend v2 🚀

A modern learning management system that facilitates interaction between trainers and trainees, built with FastAPI and MongoDB.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100.0+-00a393.svg)](https://fastapi.tiangolo.com)
[![MongoDB](https://img.shields.io/badge/MongoDB-6.0+-00ed64.svg)](https://www.mongodb.com/)

## 🌟 Features

### For Trainers

- Create, edit, and manage lessons with rich content (text, video, or both)
- Design custom questions for each lesson
- Assign lessons to trainees
- Track trainee progress and performance
- View detailed analytics for assigned lessons

### For Trainees

- Access assigned lessons with various content types
- Track personal progress through lessons
- Answer lesson questions and get immediate feedback
- View performance analytics
- Time-based lesson completion tracking

## 🛠️ Tech Stack

- **Backend Framework**: FastAPI
- **Database**: MongoDB
- **Authentication**: JWT with refresh tokens
- **API Documentation**: OpenAPI (Swagger)
- **Testing**: pytest
- **Code Style**: Black, isort

## 📋 Prerequisites

- Python 3.9+
- MongoDB 6.0+
- pnpm (for development)

## 🚀 Getting Started

1. **Clone the repository**

   ```bash
   git clone https://github.com/byigitt/roundcall-backend-v2.git
   cd roundcall-backend-v2
   ```

2. **Set up a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pnpm install
   ```

4. **Set up environment variables**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000`
API Documentation will be available at `http://localhost:8000/docs`

## 🏗️ Project Structure

```
roundcall-backend-v2/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       └── api.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── database.py
│   ├── models/
│   │   ├── user.py
│   │   ├── lesson.py
│   │   └── analytics.py
│   └── main.py
├── tests/
├── .env
├── .gitignore
└── README.md
```

## 📚 API Documentation

The API provides comprehensive endpoints for:

- User Authentication (Register, Login, Refresh Token)
- Lesson Management
- Question Management
- Progress Tracking
- Analytics

Detailed API documentation is available at `/docs` when running the server.

## 🔐 Authentication

The system uses JWT tokens with refresh token mechanism:

- Access tokens expire after 30 minutes
- Refresh tokens expire after 7 days
- Tokens are stored securely in HTTP-only cookies

## 📊 Database Schema

The system uses MongoDB with the following collections:

- Users
- Lessons
- AssignedLessons
- Analytics

Each collection is properly indexed for optimal query performance.

## 🔒 Security Features

- Password hashing using bcrypt
- JWT token authentication
- Rate limiting
- Input validation
- CORS protection
- HTTP-only cookies for tokens

## 🧪 Running Tests

```bash
pytest
```

For coverage report:

```bash
pytest --cov=app --cov-report=term-missing
```

## 📈 Performance Considerations

- Indexed MongoDB queries
- Caching for frequently accessed data
- Rate limiting to prevent abuse
- Pagination for large datasets
- Efficient data validation

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Wired** - [byigitt](https://github.com/byigitt)
**Wired** - [phun333](https://github.com/phun333)

## 🙏 Acknowledgments

- FastAPI for the amazing framework
- MongoDB team for the robust database
- All contributors who have helped shape this project

## 🚢 Deployment

### Prerequisites

- Docker and Docker Compose installed on your VPS
- SSH access to your VPS
- GitHub repository secrets configured

### Automatic Deployment

The project uses GitHub Actions for CI/CD. Every push to the main branch triggers:

1. Running tests
2. Building Docker images
3. Deploying to VPS

### Manual Deployment

To deploy manually on your VPS:

```bash
# Clone the repository
git clone https://github.com/byigitt/roundcall-backend-v2.git
cd roundcall-backend-v2

# Create and configure .env file
cp .env.example .env
# Edit .env with your configuration

# Start the application
docker-compose up -d
```

The application will be available at `http://your-vps-ip:8000`

### GitHub Repository Configuration

The following secrets need to be configured in your GitHub repository (Settings > Secrets and Variables > Actions):

1. **VPS Access**

   - `VPS_HOST`: Your VPS IP address
   - `VPS_USERNAME`: Your VPS SSH username
   - `VPS_SSH_KEY`: Your SSH private key

2. **Application Configuration**
   - `MONGODB_URL`: MongoDB connection URL
   - `DATABASE_NAME`: Name of the MongoDB database
   - `SECRET_KEY`: Secret key for JWT tokens

### Environment Variables

The following environment variables are automatically set up during deployment:

```bash
MONGODB_URL=<from GitHub secrets>
DATABASE_NAME=<from GitHub secrets>
SECRET_KEY=<from GitHub secrets>
ENVIRONMENT=production
```

---

Made with ❤️ by [Wired](https://github.com/byigitt)
