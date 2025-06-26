Flight Tracking API - README

Project Overview
================

This project is a flight tracking and notification system that allows users to monitor flight prices and receive updates about price changes. It consists of a backend API built with FastAPI, a lightweight and modern Python web framework, and a client interface to interact with the API.

Core Features
=============

1. User Management
   - Users register with their email addresses.
   - User information is securely stored in a database.
   - Users can be added, deleted, and listed via API endpoints.

2. Flight Tracking
   - Registered users can add flights they want to track by specifying origin, destination, departure date, and a target price.
   - The system stores details of these flights and periodically updates price information.

3. Price Monitoring & Notifications
   - The backend periodically fetches flight price data from the Amadeus API, a popular flight data provider.
   - A caching mechanism is implemented to reduce API calls and improve performance. This cache stores recent flight search results and access tokens for the Amadeus API.
   - When flight prices drop below the user’s target price (or any price drop if the user chooses), the system flags these flights for notifications. (The actual notification sending can be integrated later.)

4. Robust API Design
   - API endpoints allow for CRUD (Create, Read, Update, Delete) operations on users and flights.
   - Input validation is enforced using Pydantic models to ensure data consistency and integrity.
   - Proper error handling with meaningful HTTP status codes and logging for debugging and monitoring.

5. Database
   - Uses SQLite as a lightweight relational database during development.
   - Database schema supports multiple users and tracks their respective flights.
   - Relational integrity is maintained with foreign keys linking flights to users.

6. Scalability Considerations
   - Though SQLite and in-memory caching are used for simplicity, the design allows future migration to more scalable databases (e.g., PostgreSQL) and distributed caching systems (e.g., Redis).
   - Caching strategies and token management aim to reduce redundant external API calls, which is critical for large scale deployments.

Technical Components
====================

- FastAPI for building RESTful API endpoints with automatic docs.
- Pydantic for defining clear data models and validation.
- Requests for making HTTP calls to the Amadeus flight API.
- Cachetools TTLCache for in-memory caching with time-based expiration.
- SQLite for lightweight data persistence.
- Logging to file and console for operational visibility.
- Environment Variables to safely manage API keys and secrets (using dotenv).

How It Works (Flow Summary)
===========================

1. User registers via /add_user endpoint with email.
2. User adds a flight to track via /add_flight endpoint by specifying flight details and target price.
3. When the client requests flight information via /get_flights, the system first checks the cache for recent flight search results to avoid hitting the external Amadeus API unnecessarily.
4. If cache is empty or expired, the system fetches a new access token (cached separately with TTL) and queries the Amadeus API for current flight prices.
5. The results are cached for future requests and stored in the database linked to the user.
6. Users can update or delete tracked flights.
7. The system can periodically run background tasks to update flight prices and notify users (optional future feature).

Why This Project?
=================

- Provides practical experience in building a full-stack flight tracking service.
- Demonstrates integration with a third-party API (Amadeus) including OAuth token handling and caching.
- Implements proper API design, validation, and error handling.
- Covers important backend concepts like caching, concurrency, database design, and deployment readiness.
- Scalable architecture allows for future feature expansion and improvements.

Contact
=======

For questions or contributions, contact: yokuflik@gmail.com
