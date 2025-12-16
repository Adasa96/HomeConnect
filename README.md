# HomeConnect

**HomeConnect** is a web application that allows homeowners to connect with qualified service providers efficiently and securely. The platform provides a seamless experience for homeowners to browse, select, and hire services, while service providers can manage their offerings and profiles. The admin oversees the platform content and manages users.

---

## Roles

### Homeowner
- Browse available services  
- Select and request services required  
- Edit and manage their profile  

### Service Provider
- Register as a service provider  
- Upload and share services  
- Update profile and manage contact information  
- Dashboard to track service requests  

### Admin
- Oversee all platform content  
- Manage users (homeowners and service providers)  
- Moderate platform activity

---

## Tools Used

- **Django** – Web framework  
- **Python Libraries** – Ready-made snippets for specific tasks  
- **Pillow** – Image handling for service uploads and profile images  
- **Cloudinary** – Cloud storage for profile and service images, with URL access  
- **Python-Decouple** – Manage environment variables and configuration  

---

## Features

### Homeowners
- User registration and login  
- View and edit personal profile  
- Search for service providers by category or location  
- View detailed service provider profiles  
- Contact service providers (optional)

### Service Providers
- Register as a service provider  
- Create and manage service profile (business name, category, description, logo)  
- Update profile and contact information  
- View dashboard for managing requests

### Admin
- Django admin panel for managing users and service providers  

---

## Technologies Used

- **Backend:** Django 5.2  
- **Frontend:** HTML, CSS, Bootstrap  
- **Database:** SQLite (development), can be switched to PostgreSQL for production  
- **Authentication:** Django built-in authentication system  
- **File Handling:** Django `ImageField` and Cloudinary for images  

---

## Installation

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/HomeConnect.git
cd HomeConnect
