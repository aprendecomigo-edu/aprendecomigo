# Test Accounts - Development Environment

**Created**: 2025-08-02  
**Environment**: Clean development database  

## 🔑 Test Account Credentials

### Django Admin Account
- **Email**: `admin@aprendecomigo.com`
- **Password**: `admin123!`
- **Role**: Django superuser
- **User ID**: 1
- **Access**: Full admin panel access
- **Login URL**: http://localhost:8000/admin/

### Individual Tutor Account  
- **Name**: `Ana Silva`
- **Email**: `ana.silva@example.com`
- **Password**: `tutorpass123`
- **Phone**: `+351 912 345 678`
- **User ID**: 2
- **Username**: `ana.silva` (auto-generated)
- **Role**: Tutor (both School Owner + Teacher)
- **Practice Name**: "Ana Silva Tutoring"
- **Primary Contact**: email
- **School ID**: 1
- **Memberships**: Owner (ID: 1) + Teacher (ID: 2)

## 🌐 Environment Details
- **Backend**: http://localhost:8000
- **Frontend**: http://localhost:8081
- **Database**: Fresh SQLite with clean migrations
- **Status**: All servers operational

## 📝 Notes
- Both accounts created via Django backend
- Multi-role system verified working
- Ready for frontend authentication testing
- Individual tutor has dual School Owner + Teacher permissions