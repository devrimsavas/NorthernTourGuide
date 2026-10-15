# Aurora Trails

A booking platform for Arctic adventure tours in Northern Norway. Guides publish tours such as husky safaris, northern lights tours and Sami culture experiences, and customers book them by date and available capacity.

> Work in progress.

## Tech Stack

- Python 3.14
- Django 6.1
- PostgreSQL

## Getting Started

```bash
# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure the database
# Copy aurora_trails/.env.example to aurora_trails/.env and fill in your PostgreSQL credentials

# Run migrations and start the server
cd aurora_trails
python manage.py migrate
python manage.py runserver
```
