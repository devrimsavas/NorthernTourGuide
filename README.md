# Aurora Trails

![Tests](https://github.com/devrimsavas/NorthernTourGuide/actions/workflows/tests.yml/badge.svg)

A booking platform for Arctic adventure tours in Northern Norway. Guides publish tours such as husky safaris, northern lights tours and Sami culture experiences, and customers book them by date and available capacity.

## Why This Project

This project is personal to me. As a developer with a background in Arctic tourism, including working as a tour guide in Alta, I know the challenges of the industry from the inside. I have previously presented to Innovasjon Norge on how digitalization could strengthen tourism in Northern Norway. Many tour operators in the region are small, often just a few guides, and they lack simple digital tools to reach visitors and manage bookings. Aurora Trails is my attempt to build that tool: a platform where local guides can offer their experiences and travelers can discover and book them easily, helping small businesses grow and bringing more visitors to the Arctic.

> Work in progress.

## Roadmap

_Last updated: 2026-10-19_

- [x] PostgreSQL setup with environment-based configuration
- [x] Custom user model with roles (guide, customer, admin) and email login
- [x] Data models: guides, activity types, locations, tours, tour slots, bookings
- [x] Customized Django admin
- [x] REST API: tour list and tour detail with live slot availability
- [x] REST API: booking creation with server-side price calculation
- [x] Capacity-safe booking (row locking with `select_for_update` to prevent overbooking)
- [x] Role-based permissions: customers only can create bookings
- [x] Automated tests, including concurrent booking scenarios
- [x] REST API: customer booking history ("my bookings")
- [x] REST API: booking cancellation by customers
- [x] Role-based permissions and endpoints for guides
- [x] Token-based authentication for the frontend
- [x] Customer self-registration with automatic login (guides are added by admins only)
- [x] Current user endpoint for role-based navigation in the frontend
- [x] Weather and aurora forecast integration (MET Norway API)
- [x] Aurora forecast (Kp index from NOAA, combined with cloud cover)
- [x] Continuous integration with GitHub Actions (tests run against PostgreSQL on every push)
- [x] Reviews (only for confirmed bookings after the tour has ended)
- [x] Public guide profiles for the frontend
- [x] Image uploads for tours and guide profiles (cover image in the tour list, gallery in the tour detail)
- [x] Tour filtering by location, activity type, difficulty, price and date range
- [x] Guide view of bookings for their own tours (customer contact details for operational use)
- [x] Booking actions for the frontend (`can_cancel`, `can_review`, `has_review`), sharing the same rules as the service layer
- [ ] Angular frontend

## Tech Stack

- Python 3.14, Django 6.1
- Django REST Framework, Simple JWT
- PostgreSQL (row locking with `select_for_update`)
- django-filter, django-cors-headers, Pillow
- requests (MET Norway and NOAA integrations)
- GitHub Actions (CI with a PostgreSQL service container)

## Getting Started

Uploaded images are stored in `aurora_trails/media/`, which is not committed to the repository. Upload tour and guide images through the Django admin.

```bash
# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure the database
# Copy aurora_trails/.env.example to aurora_trails/.env and fill in your PostgreSQL credentials
# Generate a SECRET_KEY with:
# python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Run migrations and start the server
cd aurora_trails
python manage.py migrate
python manage.py runserver
```

## API Endpoints

Authenticated endpoints require an `Authorization: Bearer <access_token>` header.

| Method          | Endpoint                            | Access        | Description                                                                                    |
| --------------- | ----------------------------------- | ------------- | ---------------------------------------------------------------------------------------------- |
| POST            | `/api/auth/token/`                  | Public        | Log in with email and password, returns access and refresh tokens                              |
| POST            | `/api/auth/token/refresh/`          | Public        | Get a new access token using a refresh token                                                   |
| GET             | `/api/tours/`                       | Public        | List active tours                                                                              |
| GET             | `/api/tours/<id>/`                  | Public        | Tour details with upcoming slots and available spots                                           |
| GET             | `/api/tours/<id>/forecast/`         | Public        | Weather forecast for each upcoming slot (MET Norway)                                           |
| POST            | `/api/bookings/`                    | Customer      | Create a booking (`slot`, `participants`)                                                      |
| GET             | `/api/bookings/me/`                 | Customer      | List the logged-in customer's bookings, with `can_cancel`, `can_review` and `has_review` flags |
| POST            | `/api/bookings/<reference>/cancel/` | Customer      | Cancel a booking                                                                               |
| GET, POST       | `/api/guide/tours/`                 | Guide         | List own tours or create a new tour                                                            |
| GET, PUT, PATCH | `/api/guide/tours/<id>/`            | Guide         | View or update an own tour                                                                     |
| GET, POST       | `/api/guide/tours/<id>/slots/`      | Guide         | List slots or add a new slot to an own tour                                                    |
| GET             | `/api/tours/<id>/reviews/`          | Public        | List reviews of a tour                                                                         |
| POST            | `/api/bookings/<reference>/review/` | Customer      | Review a finished tour (`rating`, `comment`)                                                   |
| POST            | `/api/auth/register/`               | Public        | Create a customer account, returns the user and access/refresh tokens                          |
| GET             | `/api/auth/me/`                     | Authenticated | Details and role of the logged-in user                                                         |
| GET             | `/api/guides/`                      | Public        | List guides with bio, languages and base location                                              |
| GET             | `/api/guides/<id>/`                 | Public        | Guide details                                                                                  |
| GET             | `/api/locations/`                   | Public        | List locations (for filter dropdowns)                                                          |
| GET             | `/api/activity-types/`              | Public        | List activity types (for filter dropdowns)                                                     |
| GET             | `/api/guide/bookings/`              | Guide         | Bookings for own tours, filterable by `slot` and `status`                                      |

## Filtering

The tour list supports filtering through query parameters, built with [django-filter](https://django-filter.readthedocs.io/). Invalid values (an unknown location ID, a malformed date) return `400 Bad Request` with a clear error message. In the browsable API, the **Filters** button shows a form for all parameters.

| Parameter       | Type                                  | Example                 | Description                                        |
| --------------- | ------------------------------------- | ----------------------- | -------------------------------------------------- |
| `location`      | ID                                    | `?location=2`           | Tours in a given location                          |
| `activity_type` | ID                                    | `?activity_type=1`      | Tours of a given activity type                     |
| `difficulty`    | `easy` \| `moderate` \| `challenging` | `?difficulty=easy`      | Tours with a given difficulty                      |
| `max_price`     | Number (NOK)                          | `?max_price=2000`       | Tours with a price per person up to this amount    |
| `date_from`     | Date (`YYYY-MM-DD`)                   | `?date_from=2026-12-01` | Tours with an upcoming slot on or after this date  |
| `date_to`       | Date (`YYYY-MM-DD`)                   | `?date_to=2026-12-15`   | Tours with an upcoming slot on or before this date |

Parameters can be combined:

```
GET /api/tours/?location=2&difficulty=easy&date_from=2026-12-01&date_to=2026-12-15
```

### Implementation notes

- **Date range on the same slot:** `date_from` and `date_to` are evaluated together, so a tour matches only if a single slot falls inside the range. A tour with one slot before the range and another after it is not returned.
- **Subquery instead of a join:** the date filter uses `id__in` with a subquery on tour slots. Joining slots directly would duplicate rows and distort the annotated `average_rating` and `review_count`.
- **Only upcoming slots count:** past slots never make a tour match a date search.
- **Time zone aware:** dates are compared in the configured time zone (`Europe/Oslo`), so a slot at 00:30 falls on the correct day.
- **Stable ordering:** results are always sorted by title.

## Testing

The project has 33 automated tests covering booking rules, permissions and external API integrations.

```bash
cd aurora_trails
python manage.py test -v 2
```

Django creates a temporary test database (`test_aurora_trails`) for each run and deletes it afterwards, so tests never touch real data. The PostgreSQL user therefore needs the `CREATEDB` permission.

### Test suites

| Test class             | Base class            | Database                  | What it covers                                                                                                                                    |
| ---------------------- | --------------------- | ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `BookingCapacityTests` | `TransactionTestCase` | Yes, real commits         | Capacity limits, cancellation, and concurrent bookings competing for the same spots                                                               |
| `ReviewApiTests`       | `APITestCase`         | Yes, rolled back per test | Review rules: only the booking's customer, only confirmed and finished tours, one review per booking, rating 1-5, average rating in the tour list |
| `GuideTourApiTests`    | `APITestCase`         | Yes, rolled back per test | Guide endpoints: tour ownership, role checks, capacity rules                                                                                      |
| `TourForecastApiTests` | `APITestCase`         | Yes, rolled back per test | Forecast endpoint with MET Norway and NOAA mocked, including service outages                                                                      |
| `RegisterApiTests`     | `APITestCase`         | Yes, rolled back per test | Self-registration: always a customer, case-insensitive unique email, password strength, tokens returned                                           |
| `MeApiTests`           | `APITestCase`         | Yes, rolled back per test | Current user endpoint: returns details and role, requires authentication                                                                          |
| `AuroraChanceTests`    | `SimpleTestCase`      | No                        | The aurora chance rule as a pure function                                                                                                         |
| `GuideListApiTests`    | `APITestCase`         | Yes, rolled back per test | Public guide list: only active guides with a profile, no private data                                                                             |

                                                                   |

| `TourImageApiTests` | `APITestCase` | Yes, rolled back per test | Tour images: cover image chosen by order, full URLs, all images in the detail, temporary media folder |
| `TourFilterApiTests` | `APITestCase` | Yes, rolled back per test | Tour filters (location, price, date range on a single slot, invalid input) and sorted lookup lists |
| `GuideBookingApiTests` | `APITestCase` | Yes, rolled back per test | Guide booking list: only bookings for the guide's own tours, slot filter, customers rejected |

### Why different test types?

- **`TransactionTestCase` for concurrency:** Django's default `TestCase` wraps each test in a transaction and rolls it back, which is fast but keeps everything in a single database connection. Row locking with `select_for_update` can only be tested with separate connections that really commit. The concurrency test starts two threads, each with its own connection, synchronized with a `threading.Barrier` so they hit the database at the same moment. Exactly one booking must succeed.
- **`APITestCase` for endpoints:** Tests send real HTTP requests through DRF's test client. `force_authenticate` simulates a logged-in user, and URLs are resolved by name with `reverse()`, so tests keep working if paths change.
- **`SimpleTestCase` for pure logic:** No database is created, which makes these the fastest tests.

### External APIs are mocked

Tests never call MET Norway or NOAA. `unittest.mock.patch` replaces the fetch functions with fakes that return minimal responses or raise errors. This keeps tests fast, deterministic and runnable offline, and avoids sending unnecessary traffic to public services.

## Screen Shots

![Admin panel-bookings](docs/screenshots/bookings.png)
![Admin panel-accounts](docs/screenshots/accounts.png)
![Admin panel-customer](docs/screenshots/customer.png)

## Data Sources

- Weather data from [MET Norway](https://api.met.no/), licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
- Kp index data from the [NOAA Space Weather Prediction Center](https://www.swpc.noaa.gov/).
