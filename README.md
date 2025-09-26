# Deals89.store - E-commerce Deals Platform

A modern Flask-based e-commerce platform for showcasing deals and offers with automated blog content generation.

## Features

- 🛍️ **Deal Management**: Add, edit, and manage product deals
- 📝 **Automated Blog**: AI-powered blog content generation
- 🔍 **Search & Filter**: Advanced search and category filtering
- 📱 **Responsive Design**: Mobile-first design with Tailwind CSS
- 🔐 **Admin Panel**: Secure admin dashboard for content management
- 📊 **Analytics**: Built-in analytics and tracking
- 📧 **Newsletter**: Email subscription management
- 🔄 **Scheduler**: Automated tasks and content generation

## Tech Stack

- **Backend**: Flask, SQLAlchemy, Flask-Login
- **Frontend**: HTML5, Tailwind CSS, JavaScript
- **Database**: SQLite (development), PostgreSQL (production)
- **Deployment**: Docker, Nginx
- **Automation**: APScheduler, Selenium

## Quick Start

### Prerequisites

- Python 3.11+
- Git

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/deals89.store.git
cd deals89.store
```

2. Create virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Initialize database:
```bash
python init_db.py
```

6. Run the application:
```bash
python app.py
```

Visit `http://localhost:5000` to see the application.

## Environment Variables

Copy `.env.example` to `.env` and configure:

- `SECRET_KEY`: Flask secret key
- `DATABASE_URL`: Database connection string
- `ADMIN_PASSWORD`: Admin panel password
- `TELEGRAM_BOT_TOKEN`: Telegram bot token (optional)
- `FACEBOOK_PAGE_ID`: Facebook page ID (optional)

## Deployment

### Docker

```bash
docker-compose up -d
```

### Production

The application is production-ready with:
- Gunicorn WSGI server
- Nginx reverse proxy
- SSL/TLS support
- Security headers
- Rate limiting

## API Endpoints

- `GET /api/deals` - Get all deals
- `GET /api/deals/<id>` - Get specific deal
- `GET /api/search` - Search deals
- `POST /api/newsletter/subscribe` - Newsletter subscription

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support, email support@deals89.store or create an issue on GitHub.