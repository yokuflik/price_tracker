# Flight Tracking API

## Project Overview

This project provides an advanced system for tracking flight prices, receiving updates on changes, and collecting valuable statistical data. At its core is a robust Backend API built with FastAPI, a lightweight and modern Python web framework. The system is designed to allow individual users to track flights while simultaneously collecting and analyzing valuable statistical information that can be potentially sold to airlines in the future.

**Please Note:** Currently, the project is focused solely on Backend development. **Existing Front-end code is not functional or connected to the current Backend.** Updates or CORS adjustments may be required to enable future integration.

## Core Features

1.  **User Management**
    * Users can register using their email addresses.
    * User information is securely stored in a database.
    * Users can be managed (added, deleted, registered) via secured API endpoints.

2.  **Personalized Flight Tracking**
    * Registered users can add flights to track by specifying origin, destination, departure date, and a target price.
    * The system stores these flight details and periodically updates price information.

3.  **Price Monitoring & Notifications**
    * The Backend periodically fetches flight price data from the Amadeus API, a leading global flight data provider.
    * An efficient Caching mechanism is implemented to reduce unnecessary calls to the external API and improve performance. This cache stores recent flight search results and Access Tokens for the Amadeus API.
    * When flight prices drop below the user's target price (or any price drop if the user opts for it), the system flags these flights for notification. (Actual notification sending — e.g., via email — can be integrated in the future).

4.  **Data Collection & Business Potential**
    * The system passively collects statistical data regarding flight searches and price changes.
    * This data is intended for future analysis and has the potential for sale to airlines, providing them with valuable market insights.

5.  **Robust & Secure API Design**
    * API endpoints allow for CRUD (Create, Read, Update, Delete) operations on users and flights.
    * Input validation is strictly enforced using Pydantic, ensuring data consistency and quality.
    * Comprehensive error handling returns clear messages and appropriate HTTP statuses.
    * **Security:** User authentication via JSON Web Tokens (JWT), secure password hashing (bcrypt), and Rate Limiting using `slowapi` to prevent misuse and attacks.

## How It Works (Flow Summary)

1.  A user registers with the system via the `/register_user` endpoint using their email and password.
2.  Upon successful login, the user receives a JWT token, which is used for authentication in subsequent requests.
3.  A logged-in user adds a flight to track via the `/add_flight` endpoint by providing flight details and a target price.
4.  When the client requests flight information (e.g., via `/get_flights` for a specific user, or other endpoints in the future), the system first checks its cache for up-to-date flight search results to avoid unnecessary calls to the external Amadeus API.
5.  If the cache is empty or expired, the system obtains a new Access Token from Amadeus (cached separately with a TTL) and queries the Amadeus API for current flight prices.
6.  The results are cached for future requests and stored in the database, linked to the user.
7.  Users can update or delete their tracked flights.
8.  The system can periodically run background tasks (such as the `updateFlightsInServer.py` script) to update flight prices and send notifications to users in case of a price drop.

## Contact

For questions or contributions, contact: yokuflik@gmail.com