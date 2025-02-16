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
- AI-powered chatbot for practice

## 🛠️ Tech Stack

- **Backend Framework**: FastAPI
- **Database**: MongoDB
- **Authentication**: JWT with refresh tokens
- **API Documentation**: OpenAPI (Swagger)
- **Testing**: pytest
- **Code Style**: Black, isort
- **AI Integration**: Google Gemini Pro

## 📋 Prerequisites

- Python 3.9+
- MongoDB 6.0+ (Atlas recommended for hackathon)
- Docker & Docker Compose (optional, but recommended)

## 🚀 Quick Start for Hackathon Participants

### 1. Clone the repository

```bash
git clone https://github.com/byigitt/roundcall-backend-v2.git
cd roundcall-backend-v2
```

### 2. Set up environment variables

Create a `.env` file in the root directory with the following content:

```env
# Database Configuration
MONGODB_URL=mongodb+srv://your-atlas-url
DATABASE_NAME=roundcallv2

# Security
# Generate a secure SECRET_KEY using Python:
# python -c "import secrets; import base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"
SECRET_KEY=your-generated-base64-encoded-32-byte-key-here

# API Keys
GOOGLE_API_KEY=your-google-api-key-here  # Get from https://makersuite.google.com/app/apikey

# Environment
ENVIRONMENT=development
```

### 3. Choose Your Installation Method

#### A. Using Docker (Recommended for Hackathon)

```bash
# Build and start the containers
docker-compose up -d --build

# Check logs
docker-compose logs -f
```

#### B. Manual Installation

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Verify Installation

- API will be available at `http://localhost:8000`
- Swagger documentation at `http://localhost:8000/docs`
- Try the health check endpoint: `http://localhost:8000/api/v1`

## 🔑 Required API Keys & Services

1. **MongoDB Atlas** (Free Tier)

   - Sign up at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register)
   - Create a new cluster (Free tier is sufficient)
   - Get your connection string
   - Add your IP address to the allowlist

2. **Google AI (Gemini Pro)** (Free)
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create an API key
   - Add it to your .env file

## 📚 API Documentation

The API provides comprehensive endpoints for:

- User Authentication (Register, Login, Refresh Token)
- Lesson Management
- Question Management
- Progress Tracking
- Analytics
- AI Chatbot Integration

Detailed API documentation is available at `/docs` when running the server.

## 🔐 Authentication Flow

1. Register a new user (Trainer/Trainee)
2. Login to get access & refresh tokens
3. Use access token in Authorization header: `Bearer <token>`
4. Refresh token when access token expires

## 📊 Database Schema

See [DATABASE_MODELS.md](DATABASE_MODELS.md) for detailed schema information.

## 🧪 Testing

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=app --cov-report=term-missing
```

## 🔍 Common Issues & Solutions

1. **MongoDB Connection Issues**

   - Check if your IP is whitelisted in MongoDB Atlas
   - Verify connection string in .env
   - Make sure DATABASE_NAME is set correctly

2. **CORS Issues**

   - Add your frontend URL to the origins list in main.py
   - Check if you're using https/http correctly

3. **JWT Issues**
   - Ensure SECRET_KEY is set in .env
   - Check if tokens are being sent correctly in Authorization header

## 📈 Performance Tips

- Use indexes for frequently queried fields
- Implement pagination for large datasets
- Cache frequently accessed data
- Use appropriate HTTP methods

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Authors

**Wired** - [byigitt](https://github.com/byigitt)<br>
**Wired** - [phun333](https://github.com/phun333)

## 🙏 Acknowledgments

- FastAPI for the amazing framework
- MongoDB team for the robust database
- Google for Gemini Pro API
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
