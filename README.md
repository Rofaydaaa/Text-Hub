# Text Hub
## Overview
<p>The project is a web application built using Flask, a lightweight web framework in Python. It allows users to simultaneously post, delete, and modify content on multiple social media platforms. The development environment uses SQLite, while the production environment is configured with PostgreSQL. Please note that the current platforms integrated do not support the update functionality.</p>

**Currently supported platforms:**
- Medium
- Dev.to
- Facebook
- Twitter

## Main Functionality
- **Simultaneous Posting:** Users can create and post content to multiple platforms at the same time.
- **Deletion and Modification:** The application allows users to delete and modify their posts across all integrated platforms.
- **Token Configuration:** Users can sign in and configure their platform tokens to enable posting functionalities.

## Framework and Technologies Used
- Framework: Flask (Python)
- Database (Development): SQLite
- Database (Production): PostgreSQL

## Getting Started
### Prerequisites
- Python
- Docker
- Docker Compose

Running Locally<br>

#### Clone the repository:
```bash
git clone https://github.com/your-username/your-repository.git](https://github.com/Rofaydaaa/Text-Hub.git
```
#### Navigate to the project directory:

```bash
cd Text-Hub
```
### Create a .env file and add the following configuration:
```env
# Use your own PostgreSQL database configuration
DB_URL=postgresql://your-postgres-user:your-postgres-password@your-postgres-host:5432/your-postgres-db
POSTGRES_PASSWORD=your-postgres-password
POSTGRES_USER=your-postgres-user
POSTGRES_DB=your-postgres-db

# Set your own Flask application secret key
SECRET_KEY=YourSecretKeyHere
```
### Build and run the Docker containers:

```bash
docker-compose up --build
```

Access the application in your browser at http://localhost:5000.

## Configuration
To use the application, users need to sign in and configure their platform tokens. Follow the instructions in the user profile section to set up tokens.

## Future work
- Make the app support more platforms, and this would be easy due to the modularity of platforms code constructions
- For every post, show the interactions throw all platforms(like, comments, and share)
- Advanced: Respond to some interactions throw the app

### A big thanks
To these API documentations
<br>**[Medium](https://github.com/Medium/medium-api-docs)** (currently unsupported)
<br>**[Dev.to](https://developers.forem.com/api)**
<br>**[Facebook](https://developers.facebook.com/docs/graph-api)**
<br>**[Twitter(X)](https://developer.twitter.com/en/docs/twitter-api)**
