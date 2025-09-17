# 🌱 Soil Agent Notification System

A real-time notification system that allows soil agents to receive immediate alerts when farmers request soil analysis services.

## 🚀 Features

### For Farmers
- **Easy Request Form**: Simple form to submit soil analysis requests
- **Agent Selection**: Choose from available soil agents in their district
- **Real-time Updates**: Get notified when agents respond to requests
- **Status Tracking**: Monitor the progress of their soil analysis requests

### For Soil Agents
- **Instant Notifications**: Receive immediate alerts for new requests
- **Detailed Information**: View complete farmer details and contact information
- **Quick Actions**: Accept, contact, schedule visits, or start processing requests
- **Dashboard Management**: Organize and track all soil analysis requests
- **Auto-refresh**: Dashboard updates every 30 seconds for new notifications

## 🏗️ System Architecture

### Database Collections
- `users`: Farmer and user account information
- `agentdetails`: Soil agent profiles and credentials
- `soil_requests`: Pending and active soil analysis requests
- `notifications`: Real-time notification system
- `soil_reports`: Completed soil analysis reports

### Key Routes
- `/request-soil-analysis`: Submit new soil analysis requests
- `/soilagent`: Agent dashboard with notifications
- `/fill-soil-report`: Create soil analysis reports
- `/mark-notification-read`: Mark notifications as read
- `/respond-to-soil-request`: Agent responses to farmer requests

## 🔧 Setup Instructions

### 1. Prerequisites
- Python 3.7+
- MongoDB
- Flask
- Required Python packages (see requirements.txt)

### 2. Database Setup
```bash
# Start MongoDB service
mongod

# Create database and collections
# The application will create them automatically on first run
```

### 3. Install Dependencies
```bash
pip install flask flask-bcrypt pymongo
```

### 4. Create Agent Accounts
```bash
python add_agents.py
```
This creates 33 soil agent accounts with default credentials:
- Username: email prefix (e.g., "ramesh.adilabad")
- Password: "all1234"
- Type: "soil_agent"

### 5. Start Application
```bash
python convert_crops.py
```

## 📱 How to Use

### Farmer Workflow
1. **Sign up/Login** as a farmer
2. **Navigate to Farmer Dashboard** (`/farmer`)
3. **Fill Soil Analysis Request Form**:
   - Enter personal details (name, phone, address)
   - Select district
   - Choose soil agent from available options
   - Specify intended crop
4. **Submit Request** - Agent receives immediate notification

### Agent Workflow
1. **Login** with agent credentials
2. **View Dashboard** (`/soilagent`) with real-time notifications
3. **Review New Requests** in the notifications section
4. **Take Action**:
   - Accept request
   - Contact farmer
   - Schedule visit
   - Start processing
5. **Fill Soil Report** when ready
6. **Update Status** as request progresses

## 🔔 Notification System Details

### Notification Types
- **soil_analysis_request**: New farmer requests
- **soil_request_response**: Agent responses to farmers
- **soil_report_completed**: Completed analysis reports

### Priority Levels
- **High**: New soil analysis requests (marked as URGENT)
- **Medium**: Processing requests
- **Low**: Completed requests

### Auto-refresh
- Dashboard checks for new notifications every 30 seconds
- Real-time updates without manual page refresh
- Notification badges show unread count

## 🎨 UI Features

### Dashboard Components
- **Statistics Cards**: Pending requests, completed reports, notifications count
- **Quick Actions**: Start new reports, view all reports, check notifications
- **Notification Cards**: Detailed farmer information with action buttons
- **Request Management**: Filter by status, search functionality
- **Responsive Design**: Works on desktop and mobile devices

### Visual Indicators
- **Color-coded Status**: Pending (yellow), Processing (blue), Completed (green)
- **Priority Badges**: URGENT labels for new requests
- **Hover Effects**: Interactive cards with smooth animations
- **Status Tabs**: Easy filtering of requests by status

## 🧪 Testing the System

### 1. Create Test Data
```bash
# Run the sample data creation route
# This creates sample farmers for testing
```

### 2. Test Notification Flow
1. Login as a farmer
2. Submit a soil analysis request
3. Login as an agent (use credentials from add_agents.py)
4. Check dashboard for new notification
5. Test various action buttons
6. Verify farmer receives agent responses

### 3. Test Multiple Requests
- Create multiple farmer accounts
- Submit requests to different agents
- Verify notifications are agent-specific
- Test concurrent requests

## 🔒 Security Features

- **Session Management**: Secure user authentication
- **Agent Isolation**: Agents only see their own notifications
- **Input Validation**: Form data validation and sanitization
- **Access Control**: Route protection based on user type

## 📊 Monitoring and Analytics

### Dashboard Metrics
- Total pending requests
- Completed reports count
- Unread notifications
- Response time tracking

### Performance Features
- Efficient database queries
- Pagination for large datasets
- Search and filter capabilities
- Real-time updates

## 🚨 Troubleshooting

### Common Issues
1. **Notifications not appearing**: Check MongoDB connection and agent type field
2. **Login failures**: Verify agent credentials and database setup
3. **Missing data**: Ensure all required collections exist
4. **Auto-refresh not working**: Check JavaScript console for errors

### Debug Steps
1. Check MongoDB logs
2. Verify Flask application logs
3. Test database connections
4. Validate agent account setup

## 🔮 Future Enhancements

- **Push Notifications**: Browser push notifications
- **Email Alerts**: Email notifications for urgent requests
- **SMS Integration**: Text message alerts
- **Advanced Analytics**: Detailed reporting and insights
- **Mobile App**: Native mobile application
- **API Endpoints**: RESTful API for external integrations

## 📞 Support

For technical support or questions about the notification system:
- Check the system logs
- Verify database connectivity
- Test with sample data
- Review the code documentation

---

**Note**: This system is designed for agricultural soil analysis services and can be customized for other similar notification workflows.
