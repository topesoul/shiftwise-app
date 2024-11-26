# ShiftWise: Revolutionizing Shift Management for All

![ShiftWise Favicon](./static/images/favicon.ico)

[Link to the deployed/live app on Heroku](https://shiftwise-6b603db1db32.herokuapp.com/)

![Dark Mode View](./docs/images/dark-mode-responsive-view.png)

ShiftWise Web App has been developed as a robust, scalable, and secure shift management platform meticulously crafted to streamline scheduling for workforce management, such as flexible staffing in care home agencies in the UK for example. Built with Django, ShiftWise offers a comprehensive suite of features that facilitate efficient shift assignments, user authentication, profile management, email notifications, insightful reporting dashboards, and subscription-based services. Our mission is to reduce administrative overhead, enhance communication, and provide actionable analytics to optimize workforce management.

This project marks the final of a series of milestone projects undertaken as part of the Code Institute Diploma in Web Application Development, showcasing proficiency in full-stack development, Test-Driven Development (TDD), and adherence to mobile-first responsive design principles. ShiftWise was developed with care and attention to adopt best practices in database design, security, and deployment, ensuring a reliable and efficient solution for users and visitors alike.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Strategy Plane](#strategy-plane)
   - [Project Goals](#project-goals)
   - [Target Audience](#target-audience)
   - [User Stories](#user-stories)
3. [Scope Plane](#scope-plane)
   - [Functional Requirements](#functional-requirements)
   - [Content Requirements](#content-requirements)
4. [Structure Plane](#structure-plane)
   - [Site Map](#site-map)
   - [Navigation Structure](#navigation-structure)
5. [Skeleton Plane](#skeleton-plane)
   - [Wireframes](#wireframes)
6. [Surface Plane](#surface-plane)
   - [Visual Design](#visual-design)
7. [Features](#features)
   - [User Authentication and Profile Management](#user-authentication-and-profile-management)
   - [Shift Management](#shift-management)
   - [Notifications](#notifications)
   - [Reporting Dashboard](#reporting-dashboard)
   - [Subscriptions](#subscriptions)
   - [Admin Controls](#admin-controls)
   - [Responsive Design](#responsive-design)
   - [Dark Mode](#dark-mode)
   - [Features-Testing](#features-testing)
   - [Bugs and Fixes](#known-bugs)
8. [Technologies Used](#technologies-used)
   - [Backend](#backend)
   - [Frontend](#frontend)
   - [Third-Party Integrations](#third-party-integrations)
   - [DevOps](#devops)
   - [Security](#security)
9. [Setup and Deployment](#setup-and-deployment)
   - [Prerequisites](#prerequisites)
   - [Installation Steps](#installation-steps)
   - [Deploying to Heroku](#deploying-to-heroku)
10. [Database Structure](#database-structure)
    - [Models](#models)
    - [Relationships](#relationships)
    - [Entity Relationship Diagram (ERD)](#entity-relationship-diagram-erd)
11. [Usage](#usage)
    - [User Registration and Authentication](#user-registration-and-authentication)
    - [Profile Management](#profile-management)
    - [Shift Management](#shift-management-1)
    - [Notifications](#notifications-1)
    - [Reporting Dashboard](#reporting-dashboard-1)
    - [Subscriptions](#subscriptions-1)
12. [Security Features](#security-features)
    - [Environment Configuration](#environment-configuration)
    - [User Authentication and Authorization](#user-authentication-and-authorization)
    - [Data Validation and Sanitization](#data-validation-and-sanitization)
    - [File Upload Handling](#file-upload-handling)
    - [Session Management](#session-management)
    - [Access Control](#access-control)
    - [Error Handling](#error-handling)
    - [HTTPS and SSL](#https-and-ssl)
13. [API Integration](#api-integration)
14. [Testing](#testing)
    - [Testing Methodologies](#testing-methodologies)
    - [Testing Tools](#testing-tools)
    - [Running Tests](#running-tests)
15. [Credits and Acknowledgements](#credits-and-acknowledgements)
16. [Future Development](#future-development)
17. [Conclusion](#conclusion)

---

## Introduction

ShiftWise is a cutting-edge shift management platform designed to streamline scheduling for care home agencies and their employees. Leveraging the power of Django, ShiftWise offers a comprehensive array of features that facilitate efficient shift assignments, secure user authentication, profile management, email notifications, insightful reporting dashboards, and flexible subscription-based services.

![Homepage of ShiftWise](./docs/images/homepage-image.png)

Our platform aims to minimize administrative overhead, enhance communication, and provide actionable analytics to optimize workforce management.

This project represents the culmination of a series of milestones undertaken as part of the Code Institute Diploma in Web Application Development, showcasing expertise in full-stack development, security best practices, and responsive design.

---

## Strategy Plane

### Project Goals

ShiftWise was developed with the following objectives:

- **For Agencies:** Simplify the process of assigning, tracking, and managing employee shifts.
- **For Employees:** Provide a user-friendly interface to view, accept, and manage their shift schedules.
- **For Administrators:** Offer advanced tools for monitoring shift activities, generating reports, and managing subscriptions.

### Target Audience

- **Agencies:** Care home agencies requiring efficient shift scheduling and management for their workforce.
- **Employees (of Agencies):** Caregivers seeking clarity and control over their shift assignments.
- **Administrators (Agency Owners, Agency Managers, Superusers):** Personnel responsible for overseeing the operational aspects of shift management within the platform.

### User Stories

#### Guest Users

- **Understand Purpose:** As a visitor, I want to understand the purpose of ShiftWise without needing to log in so that I can decide if it suits my needs.
- **Easy Navigation:** As a visitor, I want to easily navigate to the signup or login pages from the homepage.

#### Registered Users

- **Profile Management:** As a registered user, I want to create, view, edit, and delete my profile to maintain up-to-date personal information.
- **Shift Visibility:** As a registered user, I want to view my assigned shifts and receive notifications for upcoming shifts.
- **Subscription Management:** As a registered user, I want to manage my subscriptions to access premium features.

#### Agency Administrators

- **Efficient Shift Assignment:** As an agency administrator, I want to assign shifts to employees efficiently to ensure optimal workforce distribution.
- **Report Generation:** As an agency administrator, I want to see or generate reports on shift activities to analyze performance and attendance.
- **User Role Management:** As an agency administrator, I want to manage user roles and permissions to maintain platform security.

#### Superusers

- **Comprehensive Oversight:** As a superuser, I want to have full access to all aspects of the platform to manage agencies, users, shifts, and system settings.
- **Advanced Reporting:** As a superuser, I want to generate and view advanced reports to monitor overall platform performance and usage.
- **System Maintenance:** As a superuser, I want to perform system maintenance tasks, such as managing subscriptions, overseeing security settings, and handling escalated support issues.

---

## Scope Plane

### Functional Requirements

ShiftWise encompasses the following functionalities:

- **User Authentication:**
  - Secure registration, login, and logout processes with multi-factor authentication (MFA).
  - Password reset and recovery mechanisms.
- **Profile Management:**
  - Users can update their personal information and profile pictures.
  - Address management with autocomplete functionality using Google Places API.
- **Shift Management:**
  - Agencies can create, assign, and manage shifts for employees.
  - Employees can accept or decline shift assignments.
- **Notifications:**
  - Email notifications for shift assignments, updates, and reminders.
  - UI CRUD feedback messages to inform users about actions.
- **Reporting Dashboard:**
  - Visual analytics for shift activities, employee performance, and other key metrics.
- **Subscriptions:**
  - Tiered subscription plans offering varying levels of access and features.
  - Integration with Stripe for payment processing.
- **Admin Controls:**
  - Comprehensive tools for managing users, shifts, subscriptions, and platform settings.
- **Security:**
  - Role-based access control (RBAC).
  - Secure file uploads to AWS S3 using `django-storages`.
  - SSL/TLS encryption.

### Content Requirements

- **User Profiles:**
  - Detailed profiles including personal information, role designation, and shift history.
- **Shifts:**
  - Comprehensive details for each shift, including date, time, assigned employee, and status.
- **Notifications:**
  - Clear and concise messages informing users of important updates.
- **Reports:**
  - Visual and textual reports generated from shift and user data.
- **Subscription Plans:**
  - Descriptions of available subscription tiers and their respective benefits.

---

## Structure Plane

### Site Map

- **Home Page**
  - Overview of ShiftWise features.
  - Call-to-action for signup and login.
  - Testimonials and user feedback.
- **User Dashboard**
  - View assigned shifts.
  - Manage profile and settings.
  - Access notifications.
  - Subscription management.
- **Agency Dashboard**
  - Create and assign shifts.
  - View employee shift schedules.
  - Generate and view reports.
  - Manage subscriptions and user roles.
- **Superuser Dashboard**
  - Comprehensive oversight of all agencies and users.
  - Advanced reporting and analytics.
  - System settings and maintenance tools.
- **Reporting Dashboard**
  - Visual analytics on shift activities.
  - Performance metrics for employees.
- **Authentication Pages**
  - Signup, login, password reset, and MFA verification.
- **Admin Panel**
  - Manage users, shifts, subscriptions, and platform settings.

### Navigation Structure

- **Top Navigation Bar**

  - **Logo/Home:** Redirects to the home page.
  - **Features:** Highlights key functionalities.
  - **Dashboard:** Access user, agency, or superuser dashboards.
  - **Subscriptions:** View and manage subscription plans.
  - **Contact:** Reach out for support or inquiries.
  - **Profile:** Access and manage user profile.
  - **Logout:** Securely log out of the platform.

  ![Navigation Bar](./docs/images/nav-bar.png)

- **Footer**

  - **Quick Links:** Links to important pages like Privacy Policy, Terms of Service.
  - **Social Media Icons:** Connect via various social platforms.
  - **Contact Information:** Email and support channels.

  ![Footer Section](./docs/images/footer-image.png)

---

## Skeleton Plane

The ShiftWise skeleton emphasizes user-friendly navigation and intuitive layouts. Key pages are organized to ensure that users can easily access and manage their shifts, profiles, and subscriptions. Wireframes were developed to map out the user journey, ensuring a seamless experience from login to shift management.

### Wireframes

ShiftWise's design was meticulously planned using wireframes to map out the user journey and interface.

- **Home Page Wireframe:**

  [Home Page Wireframe](./docs/wireframes/shiftwise-home-page-desktop-and-mobile.jpg)

- **Dashboard Wireframe:**

  [Dashboard Wireframe](./docs/wireframes/shiftwise-dashboard-one.jpg)

- **Manage Agencies Wireframe:**

  [Manage Agencies Wireframe](./docs/wireframes/shiftwise-manage-agencies.jpg)

- **Manage Users Wireframe:**

  [Manage Users Wireframe](./docs/wireframes/shiftwise-manage-users.jpg)

- **View Shifts Wireframe:**

  [View Shifts Wireframe](./docs/wireframes/shiftwise-view-shifts.jpg)

- **Contact Page Wireframe:**

  [Contact Page Wireframe](./docs/wireframes/shiftwise-contact-page.jpg)

Wireframes for ShiftWise were created using Figma and are stored in the `docs/wireframes` directory. These serve as the foundational blueprints for the user interface and user experience design.

---

## Surface Plane

The visual design of ShiftWise combines modern aesthetics with functionality, ensuring an engaging user experience.

### Visual Design

- **Hero Section:**

![Hero Section](./docs/images/hero-section.png)

- **Features Section:**

  [Additional Features Section](./docs/images/features-buttons.png)

- **Testimonials:**

  ![Testimonials](./docs/images/testimonials.png)

- **Navigation Bar and Footer:**

  - **Navigation Bar:**

    ![Navigation Bar](./docs/images/nav-bar.png)

  - **Footer:**

    ![Footer Section](./docs/images/footer-image.png)

- **Logo:**

  The ShiftWise logo embodies professionalism and efficiency, reflecting the platform's purpose of streamlined shift management.

- **Color Scheme:**

  - **Primary Color (#0056b3):** Utilized for headers, buttons, and active elements to establish brand identity.
  - **Secondary Color (#ffffff):** Used for backgrounds and text to ensure readability.
  - **Accent Color (#ffc107):** Highlights important features and calls-to-action.
  - **Dark Mode (#121212):** Provides a sleek, modern look for users preferring dark themes.

- **Typography:**

  - **Roboto:** Chosen for its clarity and modern feel, enhancing readability across devices.

- **Imagery:**

  - High-quality images representing professional settings, shift activities, and user interactions.
  - Icons from Font Awesome to denote actions like editing, deleting, and viewing details.

- **Interactive Elements:**
  - Buttons and links feature hover effects for better user engagement.
  - Modal dialogs provide focused interactions without navigating away from the current page.

- **Additional Images:**

  ![Superuser Dashboard](./docs/images/superuser-dashboard.png)

  ![Staff Dashboard View](./docs/images/staff-dashboard-view.png)

  ![Agency Staff Shift List View Without Shift Create Button](./docs/images/agency-staff-shift-list-view-without-shift-create-button.png)

  ![Available Workers View](./docs/images/available-workers-view.png)

  ![Shift Book and Detail View Buttons](./docs/images/shift-book-and-detail-view-buttons.png)

  ![Responsive Navbar](./docs/images/responsive-navbar.png)

  ![Responsive Design on Multiple Devices](./docs/images/responsive-image-multiple-devices.png)

  ![Social Section](./docs/images/social-section.png)

---

## Features

ShiftWise offers a comprehensive suite of features tailored to the needs of care home agencies and their employees.

### User Authentication and Profile Management

- **Secure Registration and Login:**
  - Implements Django Allauth for robust user authentication.
  - Multi-Factor Authentication (MFA) enhances account security.

- **Profile Customization:**
  - Users can update personal information, including profile pictures.
  - Address fields with autocomplete using Google Places API.

  [User Profile Page](./docs/images/profile.png)

- **Role Designation:**
  - Role designation (Agency Owner, Agency Manager, Agency Staff, Superuser) determines access levels.

### Shift Management

- **Creating Shifts:**
  - Agency admins can create new shifts specifying details like name, date, time, and role.

  ![Create Shift Button](./docs/images/create-shift-button.png)

- **Shift List and Detail Views:**
  - Users can view a list of available shifts and detailed information about each shift.

  ![Shift List View](./docs/images/shift-list-view.png)  
  ![Shift Detail View](./docs/images/shift-detail-view.png)

- **Shift Completion:**
  - Employees can complete shifts by capturing their location and providing a digital signature.

  ![Shift Completion Modal](./docs/images/shift-completion-modal.png)

- **CRUD Operations:**
  - Create, read, update, and delete shifts with detailed information including timing, capacity, and financials.

  ![CRUD Buttons](./docs/images/crud-buttons.png)

### Notifications

- **Email Notifications:**
  - Users receive email notifications for shift assignments, updates, and reminders for upcoming shifts.

- **UI Feedback Messages:**
  - Real-time UI feedback messages inform users about actions such as creating, updating, or deleting shifts.

  ![Successful Subscription Notification](./docs/images/successful-subscription-notification.png)

### Reporting Dashboard

![Agency Owner and Manager Dashboard](./docs/images/agency-owner-and-manager-dashboard.png)

- **Analytics:**
  - Visual representations of shift activities, attendance rates, and employee performance metrics.

- **Export Options:**
  - Generate reports in CSV for offline analysis and record-keeping.

### Subscriptions

![Price Cards with Plans](.docs/images/price-cards-dark-mode.png)  
[Stripe Payment Page](./docs/images/payment_stripe.png)  
[Stripe Payment Success](./docs/images/payment-stripe-test-success.png)  
[Stripe Webhook Event Success](./docs/images/stripe-webhook-test-subscription-event-success.png)

- **Tiered Subscription Plans:**

  - **Basic:** Limited number of shifts and features.
  - **Pro:** Additional analytics and reporting features.
  - **Enterprise:** Unlimited staff, shifts, and advanced capabilities.

- **Payment Integration:**
  - Seamless subscription management with Stripe for secure billing and payment processing.

- **Plan Management:**
  - Users can upgrade, downgrade, or cancel subscriptions directly within the platform. ***(Please Note:The upgrade and downgrade features are illustrative and may require further configuration and testing)*** 

  ![Manage Subscription View](./docs/images/manage-subscription-view.png)

### Admin Controls

- **Comprehensive Management Tools:**
  - Manage users, shifts, subscriptions, and platform settings through the Django admin interface.

  ![Django Admin Panel](./docs/images/django-admin-panel.png)

- **Content Moderation:**
  - Maintain platform integrity and security by overseeing user-generated content and activities including user session management based on Django all-auth settings.

### Responsive Design

- **Cross-Device Compatibility:**
  - Ensures optimal user experience across desktops, tablets, and mobile devices with a mobile-first approach.

  ![Responsive Design on Multiple Devices](./docs/images/responsive-image-multiple-devices.png)

- **Dynamic Components:**
  - Enhanced user interactions through JavaScript-powered elements like modals and autocomplete fields.

### Dark Mode

- **User-Toggleable Dark Mode:**
  - Provides a sleek, modern look for enhanced readability in low-light environments.

  ![Dark Mode Toggle Button](./docs/images/dark-mode-button.png)  
  ![Dark Mode View](./docs/images/dark-mode-responsive-view.png)

### Features Testing

| **Test Name**                          | **Description**                                                    | **Expected Output**                                                 | **Test Result** |
|----------------------------------------|--------------------------------------------------------------------|---------------------------------------------------------------------|-----------------|
| **User Registration**                  | Register a new user with valid credentials.                        | User is successfully registered and redirected.                     | Pass            |
| **Login with Correct Credentials**     | Log in using valid email and password.                             | User is authenticated and taken to the dashboard.                   | Pass            |
| **Login with Incorrect Credentials**   | Attempt to log in with invalid password.                           | Error message indicating invalid credentials.                       | Pass            |
| **Profile Update**                     | Update profile information and upload a new profile picture.       | Profile information is updated, and picture is changed.             | Pass            |
| **Shift Creation**                     | Agency admin creates a new shift with all required details.        | Shift is created and visible in the shift list.                     | Pass            |
| **Shift Assignment**                   | Assign a shift to an employee.                                     | Employee receives a notification about the shift assignment.        | Pass            |
| **Shift Completion**                   | Employee completes a shift by submitting location and signature.   | Shift status is updated to completed with submission details.       | Pass            |
| **Subscription Payment**               | Successfully pay for a subscription plan.                          | Payment is processed, and subscription is active.                   | Pass            |
| **Subscription Cancellation**          | Cancel an active subscription.                                     | Subscription is canceled, and user is notified via email.           | Pass            |
| **Notification Emails**                | Registered emails relating to shift assignments.                   | Shift assignment status notifications are sent to the assigned staff.| Pass            |
| **Access Control**                     | Attempt to access admin panel as a regular user.                   | Access is denied with an appropriate error message.                 | Pass            |
| **Superuser Access**                   | Superuser accesses all platform features and admin panels.         | Superuser has full access to all features and admin functionalities.| Pass            |
| **Shift Assignment Notification**      | Shift is assigned to an employee.                                  | Employee receives an email notification about the shift assignment. | Pass            |
| **Profile Picture Upload and Resize**  | Upload a profile picture and ensure it resizes correctly.          | Profile picture is uploaded and resized without errors.             | Pass            |
| **API Shift Details Retrieval**        | Retrieve via API via permitted permitted user frontend interface.                                    | API link displays correctly in frontend UI.                    | Pass            |
| **Worker Assignment and Unassignment** | Assign and unassign workers to shifts.                              | Workers are successfully assigned and unassigned with notifications.| Pass            |

---

## Technologies Used

ShiftWise leverages a combination of modern technologies to deliver a robust and scalable platform.

### Backend

[Python Validation Results](./docs/images/python-validation-forms-linter.png)  
[Python Validation Results](./docs/images/black-isort-python-validate-one.png)  
[Python Validation Results](./docs/images/black-isort-python-validate.png)  

- **Framework:** Django version 5.1.2
- **Database:** PostgreSQL (deployed with SSL for enhanced security)
- **Storage:** AWS S3 for media and static files using `django-storages`

### Frontend

[HTML Validation Results](./docs/images/html-validation.png) - ***includes syntax errors due to tags (e.g., static files etc.)***
[CSS Validation Results](./docs/images/css-validation.png)  
[JS Validation Results](./docs/images/jshint-js-validation.png)

- **HTML5 & CSS3:** Structuring and styling the web pages.
- **Bootstrap 4:** For responsive design and pre-built UI components.
- **JavaScript:** Enhancing interactivity and dynamic content updates.
- **jQuery:** Simplifying DOM manipulation and event handling.
- **Font Awesome:** Providing scalable vector icons.
- **Favicon:** Favicon image and ShiftWise logo components.

### Third-Party Integrations

- **Stripe:** Manages subscription-based billing and payment processing.
- **Google Places API:** Provides address autocomplete and suggestions for enhanced user experience.
- **OpenStreetMap:** Used for capturing geo location data when a shift is being completed yo verify the location of the staff.
- **Signature Pad (JavaScript):** Enables digital signature capture for shift completion.
- **Pillow:** For image processing capabilities.

### DevOps

- **Heroku:** For deploying and hosting the application.
- **Git & GitHub:** Version control and repository management.
- **Docker (Optional):** For containerization and consistent development environments.

### Security

- **Django's Built-in Security Features:** Including CSRF protection, XSS protection, and secure password storage. (Additionally, includes setting of field encryption keys)
- **SSL/TLS:** Ensures secure data transmission.
- **MFA Implementation:** Using TOTP for multi-factor authentication.

---

## Bugs and Fixes

### 1. **Google Maps Autocomplete Console Errors**
#### **Description**
The following errors were encountered while implementing the Google Maps Autocomplete functionality:
- `Uncaught ReferenceError: google is not defined`
- `InvalidValueError: initAutocomplete is not a function`
- Warning about loading the Google Maps API without `async` and `defer`.

#### **Root Cause**
1. The `initAutocomplete` function was not globally accessible.
2. The Google Maps API script was not properly loaded in `async` and `defer` mode.
3. The Google Maps API script was being referenced before it was fully loaded.

#### **Fix**
- The `initAutocomplete` function was explicitly assigned to the `window` object to make it globally accessible:
  ```javascript
  window.initAutocomplete = function () {
      // Function code here
  };
  ```
- Updated the Google Maps API script tag in `base.html` to include `async` and `defer` attributes:
  ```html
  <script async defer type="application/javascript" src="{% url 'core:google_maps_proxy' %}?libraries=places&callback=initAutocomplete"></script>
  ```
- Ensured that the script loading order was correct (jQuery → Google Maps API → custom JavaScript).

### 2. **jQuery Dependency Error**
#### **Description**
`Uncaught ReferenceError: $ is not defined` error occurred because jQuery was not loaded before running the script.

#### **Root Cause**
The `address_autocomplete.js` script depended on jQuery, but jQuery was not loaded before executing the script.

#### **Fix**
- Ensured jQuery was loaded first in `base.html`:
  ```html
  <script src="https://code.jquery.com/jquery-3.5.1.min.js"></script>
  ```
- Wrapped the autocomplete logic in a `$(document).ready()` block to ensure the DOM and jQuery were fully loaded:
  ```javascript
  $(document).ready(function () {
      if (typeof google !== "undefined" && typeof google.maps !== "undefined") {
          initAutocomplete();
      } else {
          console.error("Google Maps API is not loaded.");
      }
  });
  ```

### 3. **Proxy Endpoint Not Found (404 Error)**
#### **Description**
Requests to the Google Maps API proxy (`/proxy/google-maps-api.js`) resulted in a 404 Page Not Found error.

#### **Root Cause**
The Django URL route for the proxy endpoint was missing from `urls.py`.

#### **Fix**
- Added the following route in the `core/urls.py`:
  ```python
  from django.urls import path
  from . import views

  urlpatterns = [
      path('proxy/google-maps-api.js', views.google_maps_proxy, name='google_maps_proxy'),
  ]
  ```
- Verified that the `GOOGLE_PLACES_API_KEY` was correctly configured in the `settings.py` file and passed through the proxy.

### 4. **General Performance Warnings**
#### **Description**
The console displayed warnings about loading the Google Maps API directly without `async` and `defer`.

#### **Root Cause**
Google Maps API was blocking the page load by not utilizing the `async` and `defer` attributes.

#### **Fix**
- Updated the `<script>` tag for the Google Maps API to use `async` and `defer`:
  ```html
  <script async defer type="application/javascript" src="{% url 'core:google_maps_proxy' %}?libraries=places&callback=initAutocomplete"></script>
  ```

### 5. **Suboptimal Map API Loading**
#### **Description**
The console displayed the following warning: "Google Maps JavaScript API has been loaded directly without loading=async."

#### **Fix**
- The warning was resolved by properly using `async` and `defer` attributes as shown above. This ensures that the Google Maps API is loaded asynchronously without blocking other resources.

### **Verification and Deployment**
After applying these fixes:
- All autocomplete functionality works correctly without console errors.
- The Google Maps API loads efficiently with no blocking issues.
- Bugs and warnings related to jQuery, Google Maps, and script loading have been resolved.

---

## Important Note
These warnings/errors are cosmetic in nature and do not affect the functionality of the autocomplete feature or the overall application. They can safely be ignored during development. However, for production deployment:
- Verify proper loading of the scripts.
- Resolve any critical performance warnings.

## Setup and Deployment

Deploying ShiftWise ensures that care home agencies can access the platform reliably and securely. Follow the steps below to set up and deploy ShiftWise both locally and to Heroku.

### Prerequisites

Before setting up ShiftWise, ensure you have the following installed:

- **Python 3.9+**
- **Git:** Version control and cloning the repository.
- **Virtual Environment:** Recommended for managing project dependencies.
- **PostgreSQL 14+:** Database management system.
- **Heroku CLI:** For deploying the application to Heroku.
- **AWS Account:** For S3 storage of media and static files.
- **Google Cloud:** For setting up Google Places API for address autocomplete services.

### Installation Steps

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/shiftwise.git
   cd shiftwise
   ```
2. **Create a Virtual Environment**

   It's recommended to use a virtual environment to manage dependencies.

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**

   Create a `.env` file in the root directory and add the following configurations:

   ```env
DEBUG=True
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1,https://your-heroku-app.herokuapp.com

# Database Configuration
DATABASE_URL=postgres://your_db_user:your_db_password@localhost:5432/shiftwise_db

# Stripe Configuration
STRIPE_SECRET_KEY=your-stripe-secret-key
STRIPE_PUBLISHABLE_KEY=your-stripe-publishable-key
STRIPE_WEBHOOK_SECRET=your-stripe-webhook-secret

# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_STORAGE_BUCKET_NAME=your-s3-bucket-name
AWS_S3_REGION_NAME=your-region

# Email Configuration

DEFAULT_FROM_EMAIL=your-email@example.com

# MFA Configuration
MFA_TOTP_ISSUER=your-prefered-issuer-name
MFA_TOTP_PERIOD=set-the-value

# CSRF Trusted Origins
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
   ```

   Note: Replace placeholder values with your actual credentials and API keys.

5. **Apply Migrations**

   Ensure that your database schema is up-to-date.

   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create a Superuser**

   To access the Django admin interface, create a superuser account.

   ```bash
   python manage.py createsuperuser
   ```

7. **Collect Static Files**

   ```bash
   python manage.py collectstatic
   ```

8. **Run the Development Server**

   ```bash
   python manage.py runserver
   ```

9. **Access the Admin Interface**

   Open your browser and navigate to [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/) to log in with your superuser credentials.

### Deploying to Heroku

1. **Log in to Heroku**

   ```bash
   heroku login
   ```

2. **Create a Heroku App**

   ```bash
   heroku create shiftwise-app
   ```

3. **Set Environment Variables on Heroku**

```bash
heroku config:set SECRET_KEY=your_secret_key
heroku config:set DEBUG=False
heroku config:set DATABASE_URL=your_postgresql_database_url
heroku config:set USE_AWS=True
heroku config:set SITE_URL=https://yourdomain.com
heroku config:set MEDIAFILES_LOCATION=media
heroku config:set STATICFILES_LOCATION=static
heroku config:set FIELD_ENCRYPTION_KEY=your_field_encryption_key
heroku config:set STRIPE_SECRET_KEY=your-stripe-secret-key
heroku config:set STRIPE_PUBLISHABLE_KEY=your-stripe-publishable-key
heroku config:set STRIPE_WEBHOOK_SECRET=your-stripe-webhook-secret
heroku config:set STRIPE_PRICE_BASIC=price_id_for_basic
heroku config:set STRIPE_PRICE_PRO=price_id_for_pro
heroku config:set STRIPE_PRICE_ENTERPRISE=price_id_for_enterprise
heroku config:set DEFAULT_FROM_EMAIL=your-email@example.com
heroku config:set MFA_TOTP_ISSUER=ShiftWise
heroku config:set MFA_TOTP_PERIOD=30
heroku config:set CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

4. **Add Heroku Remote**

   (If not already added during app creation)

   ```bash
   heroku git:remote -a shiftwise-app
   ```

5. **Deploy the Application**

   ```bash
   git add .
   git commit -m "Deploy ShiftWise to Heroku"
   git push heroku main
   ```

6. **Apply Migrations on Heroku**

   ```bash
   heroku run python manage.py migrate
   ```

7. **Create Superuser on Heroku**

   ```bash
   heroku run python manage.py createsuperuser
   ```

8. **Open the Application**

   ```bash
   heroku open
   ```

**Important Notes**

- **Static Files**: Ensure AWS is configured in `settings.py` for serving static files on Heroku.
- **Procfile**: Ensure the `Procfile` is correctly set up to run the Django application and Celery workers if applicable.
- **SSL Configuration**: Heroku automatically provides SSL for custom domains. Ensure that `SECURE_SSL_REDIRECT` and related security settings are enabled in `settings.py`.

---

## Database Structure

ShiftWise utilizes a relational database (PostgreSQL) to manage and store data efficiently. Below is an overview of the primary models and their relationships.

### Models

- **User**

  - **Fields:**
    - `id` (Primary Key)
    - `username` (Unique)
    - `email` (Unique)
    - `password` (Hashed)
    - `role` (Choices: Employee, Admin)
    - `profile_picture` (ImageField)
    - `country` (ForeignKey to Country)
    - `totp_secret` (For MFA)
    - `recovery_codes` (For MFA)
    - `monthly_view_count` (Integer)
  - **Description**: Represents both employees and administrators within the platform.

- **Agency**

  - **Fields:**
    - `id` (Primary Key)
    - `name` (Unique)
    - `address_line1`
    - `address_line2`
    - `city`
    - `country` (ForeignKey to Country)
    - `agency_code` (Unique)
    - `stripe_customer_id`
    - `owner` (ForeignKey to User)
  - **Description**: Represents agencies that manage shifts and their respective employees.

- **Shift**

  - **Fields:**
    - `id` (Primary Key)
    - `name`
    - `shift_date`
    - `start_time`
    - `end_time`
    - `agency` (ForeignKey to Agency)
    - `is_active` (Boolean)
    - `is_overnight` (Boolean)
    - `shift_code` (Unique)
    - `shift_role` (ForeignKey to Role)
  - **Description**: Represents individual shifts that can be assigned to employees.

- **ShiftAssignment**

  - **Fields:**
    - `id` (Primary Key)
    - `shift` (ForeignKey to Shift)
    - `employee` (ForeignKey to User)
    - `is_completed` (Boolean)
    - `completion_latitude`
    - `completion_longitude`
    - `attendance_status` (Choices: Present, Absent, Late)
    - `signature` (ImageField)
  - **Description**: Tracks the assignment of shifts to employees and their completion status.

- **Subscription**

  - **Fields:**
    - `id` (Primary Key)
    - `agency` (ForeignKey to Agency)
    - `plan` (ForeignKey to Plan)
    - `stripe_subscription_id`
    - `status` (Choices: Active, Canceled, Past Due)
  - **Description**: Manages agency subscriptions to different plans offering various features.

- **Plan**

  - **Fields:**
    - `id` (Primary Key)
    - `name` (Unique)
    - `billing_cycle` (Choices: Monthly, Yearly)
    - `description`
    - `stripe_product_id`
    - `stripe_price_id`
    - `price`
    - `notifications_enabled (Boolean)`
    - `advanced_reporting (Boolean)`
    - `priority_support (Boolean)`
    - `shift_management (Boolean)`
    - `staff_performance (Boolean)`
    - `custom_integrations (Boolean)`
    - `is_active (Boolean)`
    - `shift_limit (Integer)`
```
  - **Description**: Defines the available subscription plans with corresponding features.

- **Notification**
  - **Fields:**
    - `id` (Primary Key)
    - `user` (ForeignKey to User)
    - `message`
    - `is_read` (Boolean)
    - `created_at` (DateTime)
  - **Description**: Stores notifications for users regarding shift updates and other relevant information.

### Relationships

- **User to Agency**: One-to-Many. A user (admin) can own multiple agencies, but each agency has only one owner.
- **Agency to Shift**: One-to-Many. An agency can have multiple shifts.
- **Shift to ShiftAssignment**: One-to-Many. Each shift can be assigned to multiple employees.
- **User to ShiftAssignment**: One-to-Many. A user can have multiple shift assignments.
- **Agency to Subscription**: One-to-One. Each agency can have one active subscription.
- **Plan to Subscription**: One-to-Many. A plan can be subscribed to by multiple agencies.

### Entity Relationship Diagram (ERD)

![ERD](docs/images/erd.png)

---

## Usage

ShiftWise leverages Django's powerful admin interface for managing shifts, assignments, and staff performance. Below is a guide to navigating and utilizing the features effectively.

### User Registration and Authentication

- **Registration**:

  - Users can sign up by providing their email and password.
  - An email confirmation process ensures the validity of the email address.

- **Login**:
  - Secure login with options for MFA adds an extra layer of security.

### Profile Management

- **Updating Information**:

  - Users can update their profile details, including changing their email and uploading a new profile picture.

- **Changing Passwords**:

  - Secure password change functionality ensures account security.

- **Multi-Factor Authentication (MFA)**:
  - Users can enable MFA for enhanced security during login.

### Shift Management

- **Creating Shifts**:

  - Agency admins can create new shifts specifying details like name, date, time, and role.

- **Assigning Shifts**:

  - Admins can assign shifts to employees based on availability and role requirements.

- **Managing Shifts**:
  - Shifts can be edited or deleted as needed. Status updates (active/inactive) help in tracking ongoing shift assignments.

### Notifications (Provisioned but not fully configured - Needs to be setup using Django channels or Celery and Redis etc.)

- **Real-Time Alerts**:

  - Users receive notifications for new shift assignments, updates, and reminders for upcoming shifts.

- **Customization**:
  - Notification preferences can be adjusted in user settings to control the type and frequency of alerts.

### Reporting Dashboard

- **Analytics**:

  - Visual representations of shift activities, attendance rates, and employee performance metrics..

- **Export Options**:
  - Generate reports in CSV for offline analysis and record-keeping.

### Subscriptions

- **Plan Selection**:

  - Agencies can choose from multiple subscription plans tailored to different needs.

- **Payment Integration**:

  - Secure payment processing through Stripe facilitates easy subscription management.

- **Plan Features**:
  - Higher-tier plans offer advanced features like unlimited shifts, detailed reporting, and priority support.

---

## Security Features

![MFA-Enabled Pre-Login Verification](.docs/images/mfa-login-verification-page.png)

ShiftWise prioritizes security to protect user data and ensure platform integrity. Below are key security measures implemented:

### Environment Configuration

- **Environment Variables**:

  - Sensitive information like `SECRET_KEY`, `DATABASE_URL`, and API keys are stored securely using environment variables.

- **Django Settings**:
  - Configured to prevent debug information from being exposed in production.

### User Authentication and Authorization

- **Password Hashing**:

  - Utilizes Django's built-in password hashing mechanisms to securely store user credentials.

- **Role-Based Access Control (RBAC)**:

  - Differentiates access levels between Superusers, Agency Owners, Agency Managers, and Agency Staff.

![MFA User Setup](.docs/images/mfa-enabled.png)
- **Multi-Factor Authentication (MFA)**: 
  - Adds an additional security layer during user login using TOTP.

### Data Validation and Sanitization

- **Form Validation**:

  - All user inputs are validated on both client and server sides to prevent malicious data entry.

- **Sanitization**:
  - Inputs are sanitized to guard against SQL injection, XSS, and other common vulnerabilities.

### File Upload Handling

- **Secure Uploads**:

  - Profile pictures and signatures are handled securely, restricting file types and sizes to prevent attacks.

- **Storage**:
  - Uploaded files are stored in secure directories with appropriate access controls.

### Session Management

- **Secure Sessions**:

  - Django's session framework manages user sessions securely, with session cookies marked as `HttpOnly` and `Secure`.

- **Session Expiry**:
  - Sessions expire after a period of inactivity to minimize unauthorized access risks.

### Access Control

- **Permissions**:

  - Granular permissions ensure users can only access resources they're authorized to view or modify.

- **Admin Controls**:
  - Superusers have full access to manage all aspects of the platform, while agency admins have scoped permissions.

### Error Handling

- **Graceful Degradation**:

  - Errors are handled gracefully with user-friendly messages, avoiding the exposure of sensitive information.

- **Logging**:
  - Critical errors and suspicious activities are logged for monitoring and auditing purposes.

### HTTPS and SSL

- **Secure Communication**:
  - The platform enforces HTTPS to ensure data transmitted between the server and clients is encrypted.

---

## API Integration

ShiftWise integrates with several external APIs to enhance functionality and user experience.

- **Google Places API, Geopy and Haverstine Function**

  - **Address Autocomplete**: Enables address autocomplete and geocoding for accurate shift location mapping.
  - **Proximity-Based Assignments**: Book or Assign shifts based on the geographical proximity of employees to the shift location.

- **Stripe API**

  - **Payment Processing**: Handles subscription payments securely, managing billing cycles and transaction records.

- **Signature Pad**
  - **Digital Signatures**: Captures employee signatures during shift completions, storing them securely for verification purposes.

---

## Testing

Ensuring the reliability and robustness of ShiftWise is paramount. The project employs comprehensive testing strategies to validate functionality, performance, and security.

### Testing Methodologies

[Tests/Debug Images](.docs/images/agency-account-test-creation.png)
[Tests/Debug Images](.docs/images/debugging-errors-testing.png)
[Tests/Debug Images](.docs/images/debug-error-sample.png)
[Tests/Debug Images](.docs/images/docs/images/test-email-contact-form.png)
[Tests/Debug Images](.docs/images/debug-error-sample.png)
[Commit Validation](.docs/images/commits-validation-for-clarity-and-consistency-git-lens.png)

- **Unit Testing**: Unit Testing: Components from apps like shifts, accounts, etc., were tested and debugged to verify correct behavior.
- **Integration Testing**: Ensures that different modules interact seamlessly. 
- **End-to-End Testing**: Simulates real user scenarios to validate the complete workflow. Used Django management commands across accounts app, subscriptions etc.
- **Security Testing**: Identifies and mitigates potential vulnerabilities in the application.
- **Responsive Testing**: Verifies that the platform maintains usability and aesthetics across various devices and screen sizes.

### Testing Tools

[Coverage](.docs/images/automated-tests-setup.png)
[Django Debug Toolbar - DJDT](.docs/images/django-debug-toolbar.png)
[Django Debug Toolbar - DJDT](.docs/images/django-debug-toolbar.png)

- **Django Debug Toolbar**: For debugging errors and SQL queries.
- **PyTest**: For writing and running test cases.
- **Developer Tools**: For debugging and performance testing.
- **Django's Test Framework**: Utilized for testing Django-specific functionalities.
- **Coverage.py**: Measures code coverage to validate test coverage.

### Running Tests

1. **Activate the Virtual Environment**

   ```bash
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Run the Test Suite**

   ```bash
   python manage.py test
   ```

3. **Generate Coverage Report**

   ```bash
   coverage run --source='.' manage.py test
   coverage report
   coverage html  # Generates an HTML report in the 'htmlcov' directory
   ```


---

## Credits and Acknowledgements

- **Contributors**

  - [Temitope Akingbala](https://github.com/topesoul) - Developer

- **References**

  - **Django Documentation**: For comprehensive guidance on Django functionalities.
 Additional Resources
  - **Bootstrap Documentation**: Assisted in implementing responsive design elements.
  - **Font Awesome**: Supplied scalable icons enhancing the UI.
  - **Stack Overflow**: Offered solutions to various development challenges.
  - **Heroku**: Facilitated seamless deployment and hosting of the application.

- **Images**

  - **Pexels**: For high-quality stock images used in a collage decorating the home page.
  - **FontAwesome**: For iconography.
  - **IconScout**: Provided 3D illustration for user default profile image.

- **Code Resources**

  - **Code Institute's Learning Management Resources**: For overall project development tutorials, key source code and setup instructions e.g., AWS S3, Heroku
  - **Django**: The primary framework used for backend development.
  - **Bootstrap**: For responsive frontend design.
  - **Stripe Integration Guides**: For setting up payment processing.
  - **Django all-auth Documentation**: For implemtation of user sessions mgt and MFA
  - **Django Documentation on Custom User Models**
  - **Django Docs - Customizing Authentication**
  - **Django Documentation on Management Commands: For developing stripe subscriptions sync scripts**
  - **Google Places & Maps API Documentation**
  - **Django Docs - Writing Custom django-admin Commands**
  - **Factory Boy Documentation**
  - **Django Seed Documentation**

- **Acknowledgements**
  - **Code Institute**: For the structured curriculum and invaluable support throughout the project.
  - **My Mentor, Student Care Staff and Peers**: For their feedback, support, encouragement, and collaboration.

---

## Future Development

While ShiftWise is feature-complete, the following enhancements are planned for future iterations:

- **Mobile Application**: Develop native mobile apps for iOS and Android to offer on-the-go shift management.
- **Advanced Reporting**: Introduce more in-depth analytics and customizable reports.
- **AI-Powered Scheduling**: Utilize machine learning to optimize shift assignments based on employee performance and preferences.
- **Integration with Calendar Apps**: Allow users to sync shifts with Google Calendar, Outlook, etc.
- **Enhanced Security Features**: Implement biometric authentication and advanced encryption methods.
- **API for Third-Party Integrations**: Enable other applications to integrate with ShiftWise via a public API.
- **Multi-Language Support**: Expand the platform's accessibility by supporting multiple languages.
- **Customizable Dashboards**: Allow users to personalize their dashboard views based on preferences.

---

## Conclusion

ShiftWise stands as a comprehensive solution for businesses (e.g.,care home agencies) and their employees seeking efficient shift management. It combines robust backend functionalities with an intuitive frontend, ShiftWise ensures that scheduling, tracking, and reporting are streamlined and user-friendly. The platform's has been developed to feature so a number of key components while embedding; security, responsiveness, and scalability so it can serve as a reliable web application tool for modern workforce management.
