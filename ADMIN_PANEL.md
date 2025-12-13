# ClockWork Admin Panel

This project includes an integrated admin panel powered by SQLAdmin with authentication.

## Access

Once the application is running, access the admin panel at:

```
http://localhost:8000/admin
```

## Authentication

The admin panel is **protected with authentication** and is **completely separate from regular user authentication**.

### Login Method
Use the admin credentials (can be changed in `.env`):
- **Username**: `admin` (default)
- **Password**: `changeme` (default)

**⚠️ IMPORTANT**: 
- Change these credentials in production by setting environment variables
- Regular users (including supervisors and clerks) **cannot** access the admin panel with their JWT tokens
- Admin access is restricted to dedicated admin credentials only

**Setting custom credentials:**
```bash
ADMIN_USERNAME=your_secure_username
ADMIN_PASSWORD=your_secure_password
```

## Features

The admin panel provides CRUD operations for all database models:

### 1. **Petitions** 📄
- View all petition requests
- Search by student username, supervisor email, or status
- Sort by date and status
- Fields displayed:
  - ID, Student Username, Status
  - Start/End dates, Minutes
  - Supervisor Email, Org Unit

### 2. **Employees** 👤
- Manage employee records
- Search by username, first name, or last name
- Fields displayed:
  - ID, Username, Name
  - Date of Birth, Address, Postal Code
  - Nationality

### 3. **Budget Positions** 💰
- Manage budget position approvals
- Search by budget approver or position
- Track approval status and percentages
- Fields displayed:
  - ID, Petition ID
  - Budget Position, Approver
  - Approval Status, Percentage

### 4. **Student Documents** 📁
- View uploaded student documents
- Track document URLs
- Fields displayed:
  - ID, Employee ID
  - ELStAM URL, Study Certificate URL
  - Insurance Certificate URL
  - Social Security Form URL

## Security

✅ **Authentication Required**: All admin routes are protected
- Session-based authentication with username/password
- Admin authentication is completely separate from regular user JWT tokens
- Only dedicated admin credentials will grant access

## Environment Variables

Add these to your `.env` file to customize admin credentials:

```env
# Admin Panel Credentials (CHANGE IN PRODUCTION!)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=changeme
```

## Customization

The admin panel can be customized in `api/admin.py`:

- Modify `column_list` to change displayed columns
- Update `column_searchable_list` for search functionality
- Adjust `column_sortable_list` for sorting options
- Change icons using Font Awesome classes
- Customize authentication logic in `AdminAuth` class
