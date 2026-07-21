import os
import markdown
from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

# Directory containing your markdown files
input_dir = './'
output_dir = './templates/'

# HTML template for each crop
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{crop_name} Crop Guide</title>
  <style>
    body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f4f8fb; color: #222; margin: 0; }}
    .card {{ background: #fff; border-radius: 14px; box-shadow: 0 6px 32px rgba(42,122,226,0.13), 0 2px 8px rgba(0,0,0,0.07); margin: 40px auto; max-width: 900px; padding: 0 0 32px 0; border: 1.5px solid #d2e3f7; }}
    .card h1 {{ margin: 0; padding: 24px 32px 16px 32px; font-size: 2em; background: linear-gradient(90deg, #e3f0ff 0%, #f4f8fb 100%); border-bottom: 1px solid #e3eaf3; border-radius: 14px 14px 0 0; }}
    .back {{ display: block; margin: 24px 32px 0 32px; color: #2a7ae2; text-decoration: none; font-weight: bold; }}
    .back:hover {{ text-decoration: underline; }}
    .content {{ margin: 24px 32px 0 32px; }}
    @media (max-width: 600px) {{
      .card h1, .content, .back {{ margin: 0 4px; padding: 0 4px; }}
    }}
  </style>
</head>
<body>
  <div class="card">
    <a class="back" href="crops.html">&larr; Back to All Crops</a>
    <h1>{crop_name}</h1>
    <div class="content">
      {content}
    </div>
  </div>
</body>
</html>
"""

def crop_name_from_filename(filename):
    # Remove _Growing_Guide.markdown or .markdown and capitalize
    name = filename.replace('_Growing_Guide.markdown', '').replace('.markdown', '').replace('_', ' ')
    return name.title()

app = Flask(__name__)
app.secret_key = 'your_secret_key'
bcrypt = Bcrypt(app)

client = MongoClient('mongodb://localhost:27017/')
db = client['your_db']
users = db.userdetails
crops = db.crops
notifications = db.notifications
soil_requests = db.soil_requests
soil_reports = db.soil_reports

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        user_type = request.form['type']
        if users.find_one({'username': username}):
            flash('Username already exists')
            return redirect('/signup')
        users.insert_one({'username': username, 'password': password, 'type': user_type})
        flash('Signup successful! Please login.')
        return redirect('/login')
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_or_email = request.form['username']
        password = request.form['password']
        user = users.find_one({'username': username_or_email})
        if user and bcrypt.check_password_hash(user['password'], password):
            session['username'] = username_or_email
            session['type'] = user['type']
            # Redirect based on stored type
            if user['type'] == 'farmer':
                return redirect('/farmer')
            elif user['type'] == 'seller':
                return redirect('/seller')
            elif user['type'] == 'buyer':
                return redirect('/buyer')
            elif user['type'] == 'company':
                return redirect('/company')
        # Check agentdetails by username or email
        agent = db.agentdetails.find_one({
            '$or': [
                {'username': username_or_email},
                {'email': username_or_email}
            ]
        })
        try:
            if agent and bcrypt.check_password_hash(agent['password'], password):
                session['username'] = agent['username']
                session['type'] = 'agent'
                session['email'] = agent['email']
                return redirect('/agenthome')
        except ValueError:
            flash('Corrupted password hash for agent. Please reset your password or contact support.')
            return redirect('/login')
        flash('Invalid credentials')
        return redirect('/login')
    return render_template('login.html')

@app.route('/agentlogin', methods=['GET', 'POST'])
def agent_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        agent = db.agentdetails.find_one({'email': email})
        if agent and bcrypt.check_password_hash(agent['password'], password):
            session['username'] = agent['username']
            session['type'] = 'agent'
            session['email'] = agent['email']
            return redirect('/agenthome')
        flash('Invalid credentials')
        return redirect('/login')
    return render_template('login.html')

# Example protected routes
@app.route('/farmer')
def farmer():
    if session.get('type') == 'farmer':
        farmer_username = session.get('username')
        # Get soil analysis requests for this farmer
        soil_requests_list = list(soil_requests.find({'farmer_username': farmer_username}))
        # Get completed soil reports for this farmer
        soil_reports_list = list(soil_reports.find({'farmer_username': farmer_username}).sort('created_at', -1))
        latest_recommended = []
        if soil_reports_list:
            latest = soil_reports_list[0]
            rec_str = latest.get('recommended_crops')
            if rec_str:
                latest_recommended = [c.strip() for c in rec_str.split(',') if c.strip()]
        return render_template('farmer.html', 
                             soil_requests=soil_requests_list,
                             soil_reports=soil_reports_list,
                             latest_recommended_crops=latest_recommended)
    return redirect('/login')

@app.route('/save-recommended-crops', methods=['POST'])
def save_recommended_crops():
    """Allow a farmer to select and save preferred crops from recommendations."""
    if session.get('type') != 'farmer':
        return redirect('/login')

    farmer_username = session.get('username')
    report_id = request.form.get('report_id')
    selected_crops = request.form.getlist('selected_crops')

    if not report_id:
        flash('Invalid request: missing report id')
        return redirect('/farmer')

    try:
        report = soil_reports.find_one({'_id': ObjectId(report_id), 'farmer_username': farmer_username})
        if not report:
            flash('Report not found')
            return redirect('/farmer')

        soil_reports.update_one(
            {'_id': ObjectId(report_id)},
            {'$set': {'farmer_selected_crops': selected_crops}}
        )

        flash('Your crop selections have been saved.')
    except Exception as e:
        flash(f'Failed to save selections: {str(e)}')

    return redirect('/farmer')

@app.route('/soilreport')
def soilreport():
    return render_template('soilreport.html')

@app.route('/selectagent')
def select_agent():
    return render_template('agent.html')

@app.route('/addcrop', methods=['GET', 'POST'])
def add_crop():
    agents = list(db.agentdetails.find({}, {"name": 1, "email": 1, "district": 1, "_id": 0}))
    if request.method == 'POST':
        cropname = request.form.get('cropname')
        quantity = request.form.get('quantity')
        price = request.form.get('price')
        seller_username = session.get('username')
        place = request.form.get('place')
        phone = request.form.get('phone')
        seller_email = request.form.get('seller_email')
        agent_email = request.form.get('agent_email')

        # Save crop details
        crops.insert_one({
            'cropname': cropname,
            'quantity': quantity,
            'price': price,
            'seller_name': seller_username,
            'seller_username': seller_username,
            'place': place,
            'phone': phone,
            'seller_email': seller_email,
            'agent_email': agent_email,
            'status': 'pending'
        })

        # Create notification for agent with full details and timestamp
        notifications.insert_one({
            'agent_email': agent_email,
            'message': f"New crop listing from {seller_username} ({place}): {cropname} ({quantity}kg, ₹{price}) | Phone: {phone} | Email: {seller_email}",
            'cropname': cropname,
            'quantity': quantity,
            'price': price,
            'seller_name': seller_username,
            'seller_username': seller_username,
            'place': place,
            'phone': phone,
            'seller_email': seller_email,
            'seen': False,
            'created_at': datetime.now()
        })

        return '<h2>Crop details submitted successfully!</h2><a href="/seller">Back to Seller Home</a>'
    return render_template('addcrop.html', agents=agents)

@app.route('/agenthome')
def agent_home():
    if session.get('type') == 'agent':
        agent_email = session.get('email')
        # Get all notifications for this specific agent only
        all_notifications = list(notifications.find({'agent_email': agent_email}).sort('created_at', -1))
        # Get unread notifications count
        unread_count = notifications.count_documents({'agent_email': agent_email, 'is_read': False})
        # Get soil analysis requests specifically
        soil_requests = list(notifications.find({
            'agent_email': agent_email, 
            'notification_type': 'soil_analysis_request'
        }).sort('created_at', -1))
        # Get farmer notifications specifically
        farmer_notifications = list(notifications.find({
            'agent_email': agent_email, 
            'notification_type': 'farmer_request'
        }).sort('created_at', -1))
        
        return render_template('agenthome.html', 
                             notifications=all_notifications,
                             unread_count=unread_count,
                             soil_requests=soil_requests,
                             farmer_notifications=farmer_notifications)
    return redirect('/login')

@app.route('/profile')
def agent_profile():
    if session.get('type') == 'agent':
        agent = db.agentdetails.find_one({'email': session.get('email')})
        return render_template('agent_profile.html', agent=agent)
    flash('You must be logged in as an agent to view your profile.')
    return redirect('/login')

# Repeat for /seller, /buyer, /company...

@app.route('/seller')
def seller():
    if session.get('type') == 'seller':
        seller_username = session.get('username')
        notifications_list = list(notifications.find({'seller_username': seller_username}))
        return render_template('seller.html', notifications=notifications_list)
    return redirect('/login')

@app.route('/buyer')
def buyer():
    if session.get('type') == 'buyer':
        buyer_username = session.get('username')
        notifications_list = list(notifications.find({'buyer_username': buyer_username}))
        return render_template('buyer.html', notifications=notifications_list)
    return redirect('/login')

@app.route('/')
def homepage():
    return render_template('homepage.html')

@app.route('/notification-demo')
def notification_demo():
    return render_template('notification_demo.html')

@app.route('/crop/<name>')
def crop_page(name):
    try:
        return render_template(f'{name}.html')
    except Exception:
        return "Crop not found", 404

@app.route('/accept_crop/<notification_id>', methods=['POST'])
def accept_crop(notification_id):
    notification = notifications.find_one({'_id': ObjectId(notification_id)})
    if notification:
        # Find the most recent pending crop for this agent
        crop = crops.find_one({'agent_email': notification['agent_email'], 'status': 'pending'})
        if crop:
            crops.update_one(
                {'_id': crop['_id']},
                {'$set': {
                    'status': 'accepted',
                    'accepted_by_agent': notification['agent_email']
                }}
            )
        notifications.update_one({'_id': ObjectId(notification_id)}, {'$set': {'seen': True, 'response': 'accepted'}})
    return redirect('/agenthome')

@app.route('/reject_crop/<notification_id>', methods=['POST'])
def reject_crop(notification_id):
    notifications.update_one({'_id': ObjectId(notification_id)}, {'$set': {'seen': True, 'response': 'rejected'}})
    return redirect('/agenthome')

@app.route('/viewcrops')
def viewcrops():
    all_crops = list(crops.find())
    return render_template('viewcrop.html', crops=all_crops)

@app.route('/buy_crop/<crop_id>', methods=['GET', 'POST'])
def buy_crop(crop_id):
    crop = crops.find_one({'_id': ObjectId(crop_id)})
    if request.method == 'POST':
        quantity = request.form.get('quantity')
        buyer_username = session.get('username')
        seller_username = crop.get('seller_username')
        if not seller_username:
            return '<h2>Error: Seller username not found for this crop. Please contact support.</h2><a href="/viewcrops">Back to Crops</a>'
        notifications.insert_one({
            'seller_username': seller_username,
            'message': f"Buyer {buyer_username} wants to buy {quantity} kg of {crop['cropname']}.",
            'cropname': crop['cropname'],
            'quantity': quantity,
            'buyer_username': buyer_username,
            'status': 'buy_request',
            'created_at': datetime.now()
        })
        return '<h2>Purchase request sent to seller!</h2><a href="/viewcrops">Back to Crops</a>'
    return render_template('buy_crop.html', crop=crop)

@app.route('/accept_sale/<notification_id>', methods=['POST'])
def accept_sale(notification_id):
    note = notifications.find_one({'_id': ObjectId(notification_id)})
    notifications.update_one({'_id': ObjectId(notification_id)}, {'$set': {'status': 'sale_accepted'}})
    # Notify the buyer
    notifications.insert_one({
        'buyer_username': note['buyer_username'],
        'cropname': note['cropname'],
        'quantity': note['quantity'],
        'status': 'sale_accepted',
        'message': f"Your request to buy {note['quantity']} kg of {note['cropname']} was accepted by the seller.",
        'created_at': datetime.now()
    })
    return redirect('/seller')

@app.route('/reject_sale/<notification_id>', methods=['POST'])
def reject_sale(notification_id):
    note = notifications.find_one({'_id': ObjectId(notification_id)})
    notifications.update_one({'_id': ObjectId(notification_id)}, {'$set': {'status': 'sale_rejected'}})
    # Notify the buyer
    notifications.insert_one({
        'buyer_username': note['buyer_username'],
        'cropname': note['cropname'],
        'quantity': note['quantity'],
        'status': 'sale_rejected',
        'message': f"Your request to buy {note['quantity']} kg of {note['cropname']} was rejected by the seller.",
        'created_at': datetime.now()
    })
    return redirect('/seller')

@app.route('/mark-notification-read/<notification_id>', methods=['POST'])
def mark_notification_read(notification_id):
    if session.get('type') == 'agent':
        agent_email = session.get('email')
        # Only allow agents to mark their own notifications as read
        notifications.update_one(
            {'_id': ObjectId(notification_id), 'agent_email': agent_email}, 
            {'$set': {'is_read': True}}
        )
    return redirect('/agenthome')

@app.route('/respond-to-soil-request/<notification_id>', methods=['POST'])
def respond_to_soil_request(notification_id):
    if session.get('type') == 'agent':
        agent_email = session.get('email')
        response_type = request.form.get('response_type')  # 'accepted', 'contacted', 'scheduled'
        
        # Get the notification details
        notification = notifications.find_one({'_id': ObjectId(notification_id), 'agent_email': agent_email})
        
        if notification:
            # Update notification with response
            notifications.update_one(
                {'_id': ObjectId(notification_id)},
                {'$set': {
                    'agent_response': response_type,
                    'responded_at': datetime.now(),
                    'is_read': True
                }}
            )
            
            # Notify farmer about agent response
            if notification.get('farmer_username'):
                response_messages = {
                    'accepted': f"✅ Agent {session.get('username')} has accepted your soil analysis request and will contact you soon.",
                    'contacted': f"📞 Agent {session.get('username')} has contacted you regarding your soil analysis request.",
                    'scheduled': f"📅 Agent {session.get('username')} has scheduled your soil analysis visit."
                }
                
                notifications.insert_one({
                    'farmer_username': notification['farmer_username'],
                    'message': response_messages.get(response_type, "Agent has responded to your soil analysis request."),
                    'status': 'agent_response',
                    'notification_type': 'soil_request_response',
                    'is_read': False,
                    'created_at': datetime.now()
                })
        
        flash(f'Response sent to farmer successfully!')
        return redirect('/soilagent')
    
    return redirect('/login')

@app.route('/delete-soil-request/<notification_id>', methods=['POST'])
def delete_soil_request(notification_id):
    if session.get('type') == 'agent':
        agent_email = session.get('email')
        
        try:
            # Get the notification details
            notification = notifications.find_one({'_id': ObjectId(notification_id), 'agent_email': agent_email})
            
            if notification:
                # Delete the notification
                result = notifications.delete_one({'_id': ObjectId(notification_id)})
                
                # Also delete associated soil request if it exists
                soil_requests.delete_many({
                    'farmer_name': notification.get('farmer_name'),
                    'agent_email': agent_email,
                    'status': 'pending'
                })
                
                # Notify farmer about deletion
                if notification.get('farmer_username'):
                    notifications.insert_one({
                        'farmer_username': notification['farmer_username'],
                        'message': f"❌ Your soil analysis request has been cancelled by agent {session.get('username')}. Please contact the agent for more information.",
                        'status': 'request_cancelled',
                        'notification_type': 'soil_request_cancelled',
                        'is_read': False,
                        'created_at': datetime.now()
                    })
                
                flash(f'Soil analysis request deleted successfully! (Deleted {result.deleted_count} notification)')
            else:
                flash('Soil analysis request not found!')
                
        except Exception as e:
            flash(f'Error deleting soil request: {str(e)}')
        
        return redirect('/agenthome')
    
    return redirect('/login')

@app.route('/bulk-delete-soil-requests', methods=['POST'])
def bulk_delete_soil_requests():
    if session.get('type') == 'agent':
        agent_email = session.get('email')
        request_ids = request.form.getlist('request_ids')
        
        try:
            if request_ids:
                # Convert string IDs to ObjectId
                object_ids = [ObjectId(req_id) for req_id in request_ids]
                
                # Get notifications to notify farmers
                notifications_to_delete = list(notifications.find({
                    '_id': {'$in': object_ids},
                    'agent_email': agent_email
                }))
                
                # Delete notifications
                result = notifications.delete_many({
                    '_id': {'$in': object_ids},
                    'agent_email': agent_email
                })
                
                # Notify farmers about bulk deletion
                for notification in notifications_to_delete:
                    if notification.get('farmer_username'):
                        notifications.insert_one({
                            'farmer_username': notification['farmer_username'],
                            'message': f"❌ Your soil analysis request has been cancelled by agent {session.get('username')}. Please contact the agent for more information.",
                            'status': 'request_cancelled',
                            'notification_type': 'soil_request_cancelled',
                            'is_read': False,
                            'created_at': datetime.now()
                        })
                
                flash(f'{result.deleted_count} soil analysis requests deleted successfully!')
            else:
                flash('No requests selected for deletion!')
                
        except Exception as e:
            flash(f'Error deleting soil requests: {str(e)}')
        
        return redirect('/agenthome')
    
    return redirect('/login')

@app.route('/test-delete-soil-request/<notification_id>')
def test_delete_soil_request(notification_id):
    """Test route to verify delete functionality"""
    if session.get('type') == 'agent':
        agent_email = session.get('email')
        
        # Get the notification details
        notification = notifications.find_one({'_id': ObjectId(notification_id), 'agent_email': agent_email})
        
        if notification:
            return f"""
            <h2>Found Notification:</h2>
            <p><strong>ID:</strong> {notification['_id']}</p>
            <p><strong>Farmer:</strong> {notification.get('farmer_name', 'N/A')}</p>
            <p><strong>Agent Email:</strong> {notification.get('agent_email', 'N/A')}</p>
            <p><strong>Type:</strong> {notification.get('notification_type', 'N/A')}</p>
            <p><strong>Is Read:</strong> {notification.get('is_read', 'N/A')}</p>
            <br>
            <form action="/delete-soil-request/{notification_id}" method="post">
                <button type="submit">Delete This Notification</button>
            </form>
            """
        else:
            return f"<h2>Notification not found!</h2><p>ID: {notification_id}</p><p>Agent: {agent_email}</p>"
    
    return redirect('/login')

@app.route('/debug-soil-requests')
def debug_soil_requests():
    """Debug route to see all soil requests for current agent"""
    if session.get('type') == 'agent':
        agent_email = session.get('email')
        
        # Get all soil analysis notifications for this agent
        soil_notifications = list(notifications.find({
            'agent_email': agent_email,
            'notification_type': 'soil_analysis_request'
        }).sort('created_at', -1))
        
        html = f"""
        <h2>Debug: Soil Requests for Agent {agent_email}</h2>
        <p><strong>Total Notifications:</strong> {len(soil_notifications)}</p>
        <hr>
        """
        
        for i, notification in enumerate(soil_notifications):
            html += f"""
            <div style="border: 1px solid #ccc; margin: 10px; padding: 10px;">
                <h3>Notification {i+1}</h3>
                <p><strong>ID:</strong> {notification['_id']}</p>
                <p><strong>Farmer:</strong> {notification.get('farmer_name', 'N/A')}</p>
                <p><strong>Phone:</strong> {notification.get('farmer_phone', 'N/A')}</p>
                <p><strong>Address:</strong> {notification.get('farmer_address', 'N/A')}</p>
                <p><strong>Is Read:</strong> {notification.get('is_read', 'N/A')}</p>
                <p><strong>Created:</strong> {notification.get('created_at', 'N/A')}</p>
                <p><strong>Agent Response:</strong> {notification.get('agent_response', 'N/A')}</p>
                <form action="/delete-soil-request/{notification['_id']}" method="post" style="display:inline;">
                    <button type="submit">🗑️ Delete</button>
                </form>
                <a href="/test-delete-soil-request/{notification['_id']}" style="margin-left: 10px;">🔍 Test</a>
            </div>
            """
        
        return html
    
    return redirect('/login')

@app.route('/check-new-notifications')
def check_new_notifications():
    if session.get('type') == 'agent':
        agent_email = session.get('email')
        # Count unread soil analysis notifications for this agent
        unread_count = notifications.count_documents({
            'agent_email': agent_email, 
            'notification_type': 'soil_analysis_request',
            'is_read': False
        })
        return {'new_notifications': unread_count}
    return {'new_notifications': 0}

@app.route('/create-sample-request')
def create_sample_request():
    """Create a sample soil analysis request for testing purposes"""
    if session.get('type') != 'agent':
        return redirect('/login')
    
    # Create a sample soil analysis request
    sample_request = {
        'farmer_username': 'shashi_kumar',
        'farmer_name': 'Shashi Kumar',
        'farmer_phone': '6301691012',
        'farmer_address': 'ndbdfsnmbn',
        'agent_district': 'Adilabad',
        'agent_email': session.get('email'),
        'agent_name': session.get('username'),
        'crop_intention': 'Not specified',
        'status': 'pending',
        'created_at': datetime.now()
    }
    
    # Insert the sample request
    soil_requests.insert_one(sample_request)
    
    # Create notification for the agent
    notifications.insert_one({
        'agent_email': session.get('email'),
        'message': f"🌱 URGENT: NEW SOIL ANALYSIS REQUEST\n\nFarmer: Shashi Kumar\nDistrict: Adilabad\nPhone: 6301691012\nAddress: ndbdfsnmbn\nIntended Crop: Not specified\n\nPlease contact the farmer immediately to schedule soil sampling.",
        'farmer_name': 'Shashi Kumar',
        'farmer_phone': '6301691012',
        'farmer_address': 'ndbdfsnmbn',
        'agent_district': 'Adilabad',
        'crop_intention': 'Not specified',
        'status': 'soil_request',
        'notification_type': 'soil_analysis_request',
        'is_read': False,
        'priority': 'high',
        'urgency': 'immediate',
        'created_at': datetime.now()
    })
    
    flash('Sample soil analysis request created successfully! Check your notifications.')
    return redirect('/soilagent')

@app.route('/schedule-soil-visit/<notification_id>', methods=['POST'])
def schedule_soil_visit(notification_id):
    if session.get('type') == 'agent':
        agent_email = session.get('email')
        visit_date = request.form.get('visit_date')
        visit_time = request.form.get('visit_time')
        visit_notes = request.form.get('visit_notes', '')
        
        # Get the notification details
        notification = notifications.find_one({'_id': ObjectId(notification_id), 'agent_email': agent_email})
        
        if notification:
            # Update notification with scheduled visit
            notifications.update_one(
                {'_id': ObjectId(notification_id)},
                {'$set': {
                    'visit_scheduled': True,
                    'visit_date': visit_date,
                    'visit_time': visit_time,
                    'visit_notes': visit_notes,
                    'scheduled_by': session.get('username'),
                    'scheduled_at': datetime.now(),
                    'is_read': True
                }}
            )
            
            # Notify farmer about scheduled visit
            if notification.get('farmer_username'):
                visit_datetime = f"{visit_date} at {visit_time}"
                notifications.insert_one({
                    'farmer_username': notification['farmer_username'],
                    'message': f"📅 Your soil sampling visit has been scheduled!\n\nAgent: {session.get('username')}\nDate & Time: {visit_datetime}\nNotes: {visit_notes if visit_notes else 'No additional notes'}\n\nPlease be available at the scheduled time.",
                    'status': 'visit_scheduled',
                    'notification_type': 'soil_visit_scheduled',
                    'is_read': False,
                    'created_at': datetime.now()
                })
            
            flash(f'Visit scheduled successfully for {visit_date} at {visit_time}!')
            return redirect('/soilagent')
    
    return redirect('/login')

# Soil Analysis Routes
@app.route('/request-soil-analysis', methods=['POST'])
def request_soil_analysis():
    if session.get('type') != 'farmer':
        flash('Only farmers can request soil analysis')
        return redirect('/farmer')
    
    farmer_name = request.form.get('farmer_name')
    farmer_phone = request.form.get('farmer_phone')
    farmer_address = request.form.get('farmer_address')
    agent_district = request.form.get('agent_district')
    agent_email = request.form.get('agent_email')  # Get selected agent email
    crop_intention = request.form.get('crop_intention')
    farmer_username = session.get('username')
    
    # Validate that agent email is provided
    if not agent_email:
        flash('Please select a soil agent from your district.')
        return redirect('/farmer')
    
    # Find soil agent details
    soil_agent = db.agentdetails.find_one({'email': agent_email, 'type': 'soil_agent'})
    
    if not soil_agent:
        flash(f'Selected agent not found. Please try again.')
        return redirect('/farmer')
    
    # Create soil analysis request
    soil_requests.insert_one({
        'farmer_username': farmer_username,
        'farmer_name': farmer_name,
        'farmer_phone': farmer_phone,
        'farmer_address': farmer_address,
        'agent_district': agent_district,
        'agent_email': agent_email,
        'agent_name': soil_agent['name'],
        'crop_intention': crop_intention,
        'status': 'pending',
        'created_at': datetime.now()
    })
    
    # Notify ONLY the selected soil agent with enhanced details
    notifications.insert_one({
        'agent_email': agent_email,  # Only the selected agent receives this notification
        'message': f"🌱 URGENT: NEW SOIL ANALYSIS REQUEST\n\nFarmer: {farmer_name}\nDistrict: {agent_district}\nPhone: {farmer_phone}\nAddress: {farmer_address}\nIntended Crop: {crop_intention or 'Not specified'}\n\nPlease contact the farmer immediately to schedule soil sampling.",
        'farmer_name': farmer_name,
        'farmer_phone': farmer_phone,
        'farmer_address': farmer_address,
        'crop_intention': crop_intention,
        'status': 'soil_request',
        'notification_type': 'soil_analysis_request',
        'is_read': False,
        'priority': 'high',
        'urgency': 'immediate',
        'created_at': datetime.now()
    })
    
    # Also notify the farmer that their request was sent successfully
    notifications.insert_one({
        'farmer_username': farmer_username,
        'message': f"✅ Your soil analysis request has been sent to {soil_agent['name']} in {agent_district}. They will contact you soon.",
        'status': 'request_confirmation',
        'notification_type': 'soil_request_sent',
        'is_read': False,
        'created_at': datetime.now()
    })
    
    flash('Soil analysis request submitted successfully! Agent will contact you soon.')
    return redirect('/farmer')

@app.route('/soilagent')
def soil_agent_dashboard():
    if session.get('type') == 'agent':
        agent_email = session.get('email')
        # Get soil analysis requests for this specific agent only
        soil_requests_list = list(soil_requests.find({'agent_email': agent_email}).sort('created_at', -1))
        # Get completed soil reports for this agent only
        soil_reports_list = list(soil_reports.find({'agent_email': agent_email}).sort('created_at', -1))
        # Get unread soil analysis notifications
        unread_soil_notifications = notifications.count_documents({
            'agent_email': agent_email, 
            'notification_type': 'soil_analysis_request',
            'is_read': False
        })
        
        # Get all notifications for this agent
        all_notifications = list(notifications.find({
            'agent_email': agent_email,
            'notification_type': 'soil_analysis_request'
        }).sort('created_at', -1))
        
        # Get today's date for the scheduling modal
        today_date = datetime.now().strftime('%Y-%m-%d')
        
        return render_template('soilagent.html', 
                             soil_requests=soil_requests_list, 
                             soil_reports=soil_reports_list,
                             unread_notifications=unread_soil_notifications,
                             notifications=all_notifications,
                             today_date=today_date)
    return redirect('/login')

@app.route('/update-soil-report/<request_id>', methods=['GET', 'POST'])
def update_soil_report(request_id):
    if session.get('type') != 'agent':
        flash('Only agents can update soil reports')
        return redirect('/login')
    
    soil_request = soil_requests.find_one({'_id': ObjectId(request_id)})
    if not soil_request:
        flash('Soil request not found')
        return redirect('/soilagent')
    
    if request.method == 'POST':
        # Get soil analysis data
        nitrogen = request.form.get('nitrogen')
        phosphorus = request.form.get('phosphorus')
        potassium = request.form.get('potassium')
        ph_level = request.form.get('ph_level')
        soil_texture = request.form.get('soil_texture')
        organic_matter = request.form.get('organic_matter')
        recommendations = request.form.get('recommendations')
        recommended_crops = request.form.get('recommended_crops')
        
        # Create soil report
        soil_reports.insert_one({
            'request_id': ObjectId(request_id),
            'farmer_username': soil_request['farmer_username'],
            'farmer_name': soil_request['farmer_name'],
            'agent_email': session.get('email'),
            'nitrogen': nitrogen,
            'phosphorus': phosphorus,
            'potassium': potassium,
            'ph_level': ph_level,
            'soil_texture': soil_texture,
            'organic_matter': organic_matter,
            'recommendations': recommendations,
            'recommended_crops': recommended_crops,
            'status': 'completed',
            'created_at': datetime.now()
        })
        
        # Update soil request status
        soil_requests.update_one(
            {'_id': ObjectId(request_id)},
            {'$set': {'status': 'completed'}}
        )
        
        # Notify farmer
        notifications.insert_one({
            'farmer_username': soil_request['farmer_username'],
            'message': f"Your soil analysis report is ready! Agent has completed the analysis.",
            'status': 'soil_report_ready',
            'created_at': datetime.now()
        })
        
        flash('Soil report updated successfully!')
        return redirect('/soilagent')
    
    return render_template('update_soil_report.html', soil_request=soil_request)

@app.route('/view-soil-report/<report_id>')
def view_soil_report(report_id):
    if session.get('type') not in ['farmer', 'agent']:
        flash('Access denied')
        return redirect('/login')
    
    soil_report = soil_reports.find_one({'_id': ObjectId(report_id)})
    if not soil_report:
        flash('Soil report not found')
        return redirect('/farmer' if session.get('type') == 'farmer' else '/soilagent')
    
    # Check if user has access to this report
    if session.get('type') == 'farmer' and soil_report['farmer_username'] != session.get('username'):
        flash('Access denied')
        return redirect('/farmer')
    elif session.get('type') == 'agent' and soil_report['agent_email'] != session.get('email'):
        flash('Access denied')
        return redirect('/soilagent')
    
    return render_template('view_soil_report.html', soil_report=soil_report)

@app.route('/farmer-soil-reports')
def farmer_soil_reports():
    if session.get('type') != 'farmer':
        flash('Only farmers can access this page')
        return redirect('/login')
    
    farmer_username = session.get('username')
    # Get all soil reports for this farmer
    soil_reports_list = list(soil_reports.find({'farmer_username': farmer_username}).sort('created_at', -1))
    # Get pending soil requests
    soil_requests_list = list(soil_requests.find({'farmer_username': farmer_username, 'status': 'pending'}))
    
    return render_template('farmer_soil_reports.html', 
                         soil_reports=soil_reports_list,
                         soil_requests=soil_requests_list)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully')
    return redirect('/login')

@app.route('/create-sample-agents')
def create_sample_agents():
    # Create Telangana district soil agents for testing
    sample_agents = [
        {
            'name': 'Ramesh Yadav',
            'email': 'ramesh.adilabad@agri.com',
            'username': 'ramesh_adilabad',
            'password': bcrypt.generate_password_hash('password123').decode('utf-8'),
            'district': 'Adilabad',
            'type': 'soil_agent',
            'phone': '9876543201',
            'experience': '8 years',
            'specialization': 'Soil Testing & Analysis'
        },
        {
            'name': 'Sushma Reddy',
            'email': 'sushma.kothagudem@agri.com',
            'username': 'sushma_kothagudem',
            'password': bcrypt.generate_password_hash('password123').decode('utf-8'),
            'district': 'Bhadradri Kothagudem',
            'type': 'soil_agent',
            'phone': '9876543202',
            'experience': '10 years',
            'specialization': 'Soil Fertility Management'
        },
        {
            'name': 'Praveen Kumar',
            'email': 'praveen.hanamkonda@agri.com',
            'username': 'praveen_hanamkonda',
            'password': bcrypt.generate_password_hash('password123').decode('utf-8'),
            'district': 'Hanamkonda',
            'type': 'soil_agent',
            'phone': '9876543203',
            'experience': '12 years',
            'specialization': 'Soil Chemistry'
        },
        {
            'name': 'Kavitha Laxmi',
            'email': 'kavitha.hyderabad@agri.com',
            'username': 'kavitha_hyderabad',
            'password': bcrypt.generate_password_hash('password123').decode('utf-8'),
            'district': 'Hyderabad',
            'type': 'soil_agent',
            'phone': '9876543204',
            'experience': '15 years',
            'specialization': 'Precision Agriculture'
        },
        {
            'name': 'Sandeep Naik',
            'email': 'sandeep.jagtial@agri.com',
            'username': 'sandeep_jagtial',
            'password': bcrypt.generate_password_hash('password123').decode('utf-8'),
            'district': 'Jagtial',
            'type': 'soil_agent',
            'phone': '9876543205',
            'experience': '9 years',
            'specialization': 'Soil Health Management'
        }
    ]
    
    # Check if agents already exist
    existing_agents = list(db.agentdetails.find({'type': 'soil_agent'}))
    if existing_agents:
        return "Sample agents already exist! Use these credentials:<br><br>" + \
               "<br>".join([f"<strong>{agent['name']}</strong> ({agent['district']}): {agent['email']} / password123" for agent in existing_agents])
    
    # Insert sample agents
    for agent in sample_agents:
        db.agentdetails.insert_one(agent)
    
    return "Telangana soil agents created successfully!<br><br>" + \
           "<br>".join([f"<strong>{agent['name']}</strong> ({agent['district']}): {agent['email']} / password123" for agent in sample_agents])

@app.route('/create-sample-farmers')
def create_sample_farmers():
    # Create sample farmers for testing
    sample_farmers = [
        {
            'username': 'farmer1',
            'password': bcrypt.generate_password_hash('password123').decode('utf-8'),
            'type': 'farmer',
            'name': 'Rajesh Kumar',
            'phone': '9876543210',
            'address': 'Adilabad District, Telangana'
        },
        {
            'username': 'farmer2',
            'password': bcrypt.generate_password_hash('password123').decode('utf-8'),
            'type': 'farmer',
            'name': 'Lakshmi Devi',
            'phone': '9876543211',
            'address': 'Hyderabad District, Telangana'
        },
        {
            'username': 'farmer3',
            'password': bcrypt.generate_password_hash('password123').decode('utf-8'),
            'type': 'farmer',
            'name': 'Venkatesh Reddy',
            'phone': '9876543212',
            'address': 'Karimnagar District, Telangana'
        }
    ]
    
    # Check if farmers already exist
    existing_farmers = list(users.find({'type': 'farmer'}))
    if existing_farmers:
        return "Sample farmers already exist! Use these credentials:<br><br>" + \
               "<br>".join([f"<strong>{farmer['name']}</strong>: {farmer['username']} / password123" for farmer in existing_farmers])
    
    # Insert sample farmers
    for farmer in sample_farmers:
        users.insert_one(farmer)
    
    return "Sample farmers created successfully!<br><br>" + \
           "<br>".join([f"<strong>{farmer['name']}</strong>: {farmer['username']} / password123" for farmer in sample_farmers])

@app.route('/fill-soil-report')
def fill_soil_report():
    if session.get('type') != 'agent':
        return redirect('/login')
    
    agent_email = session.get('email')
    
    # Get pending soil requests for this agent
    pending_requests = list(soil_requests.find({
        'agent_email': agent_email,
        'status': 'pending'
    }))
    
    # Get URL parameters for auto-selection
    request_id = request.args.get('request_id')
    farmer_name = request.args.get('farmer')
    
    # Find the specific request if parameters are provided
    selected_request = None
    if request_id and farmer_name:
        # Try to find the request by ID first
        try:
            selected_request = soil_requests.find_one({
                '_id': ObjectId(request_id),
                'agent_email': agent_email,
                'status': 'pending'
            })
        except:
            # If ObjectId fails, try to find by farmer name
            selected_request = soil_requests.find_one({
                'farmer_name': farmer_name,
                'agent_email': agent_email,
                'status': 'pending'
            })
    
    return render_template('fill_soil_report.html', 
                         pending_requests=pending_requests,
                         selected_request=selected_request,
                         auto_select_farmer=farmer_name)

@app.route('/submit-soil-report', methods=['POST'])
def submit_soil_report():
    if session.get('type') != 'agent':
        return redirect('/login')
    
    agent_email = session.get('email')
    agent_name = session.get('username')
    
    # Get form data
    farmer_username = request.form.get('farmer_username')
    nitrogen = request.form.get('nitrogen')
    phosphorus = request.form.get('phosphorus')
    potassium = request.form.get('potassium')
    ph_level = request.form.get('ph_level')
    soil_texture = request.form.get('soil_texture')
    organic_matter = request.form.get('organic_matter')
    recommended_crops = request.form.get('recommended_crops')
    fertilizer_recommendations = request.form.get('fertilizer_recommendations')
    additional_notes = request.form.get('additional_notes')
    
    # Get farmer details
    farmer = users.find_one({'username': farmer_username})
    if not farmer:
        flash('Farmer not found!')
        return redirect('/fill-soil-report')
    
    # Create soil report
    soil_report = {
        'farmer_username': farmer_username,
        'farmer_name': farmer.get('name', farmer_username),
        'agent_email': agent_email,
        'agent_name': agent_name,
        'nitrogen': nitrogen,
        'phosphorus': phosphorus,
        'potassium': potassium,
        'ph_level': ph_level,
        'soil_texture': soil_texture,
        'organic_matter': organic_matter,
        'recommended_crops': recommended_crops,
        'fertilizer_recommendations': fertilizer_recommendations,
        'additional_notes': additional_notes,
        'created_at': datetime.now(),
        'status': 'completed'
    }
    
    # Insert soil report
    soil_reports.insert_one(soil_report)
    
    # Update soil request status
    soil_requests.update_one(
        {'farmer_username': farmer_username, 'agent_email': agent_email, 'status': 'pending'},
        {'$set': {'status': 'completed'}}
    )
    
    # Notify farmer about completed report with detailed information
    report_summary = f"""🌱 Your soil analysis report is ready!

Agent: {agent_name}
Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}

📊 Soil Analysis Results:
• Nitrogen: {nitrogen}
• Phosphorus: {phosphorus}
• Potassium: {potassium}
• pH Level: {ph_level}
• Soil Texture: {soil_texture}
• Organic Matter: {organic_matter}

🌾 Recommended Crops: {recommended_crops}
💧 Fertilizer Recommendations: {fertilizer_recommendations}

📝 Additional Notes: {additional_notes if additional_notes else 'None'}

You can view your complete soil analysis report in your dashboard."""
    
    notifications.insert_one({
        'farmer_username': farmer_username,
        'message': report_summary,
        'status': 'report_completed',
        'notification_type': 'soil_report_completed',
        'is_read': False,
        'created_at': datetime.now()
    })
    
    flash('Soil report submitted successfully! Farmer has been notified.')
    return redirect('/soilagent')

@app.route('/start-processing/<request_id>', methods=['POST'])
def start_processing(request_id):
    if session.get('type') != 'agent':
        return redirect('/login')
    
    agent_email = session.get('email')
    
    # Update soil request status to processing
    result = soil_requests.update_one(
        {'_id': ObjectId(request_id), 'agent_email': agent_email},
        {'$set': {
            'status': 'processing',
            'processing_started': datetime.now()
        }}
    )
    
    if result.modified_count > 0:
        # Get the request details
        request = soil_requests.find_one({'_id': ObjectId(request_id)})
        
        # Notify farmer that processing has started
        notifications.insert_one({
            'farmer_username': request['farmer_username'],
            'message': f"🔄 Your soil analysis is now being processed!\n\nAgent: {session.get('username')}\n\nWe have started analyzing your soil sample. You will be notified when the report is ready.",
            'status': 'processing_started',
            'notification_type': 'soil_processing_started',
            'is_read': False,
            'created_at': datetime.now()
        })
        
        return {'success': True, 'message': 'Processing started successfully'}
    else:
        return {'success': False, 'message': 'Request not found or already processed'}

@app.route('/update-soil-report/<request_id>', methods=['GET', 'POST'])
def update_soil_report_form(request_id):
    if session.get('type') != 'agent':
        return redirect('/login')
    
    agent_email = session.get('email')
    
    # Get the soil request
    soil_request = soil_requests.find_one({'_id': ObjectId(request_id), 'agent_email': agent_email})
    if not soil_request:
        flash('Soil request not found')
        return redirect('/soilagent')
    
    # Get existing soil report if any
    existing_report = soil_reports.find_one({'request_id': ObjectId(request_id)})
    
    if request.method == 'POST':
        # Get form data
        nitrogen = request.form.get('nitrogen')
        phosphorus = request.form.get('phosphorus')
        potassium = request.form.get('potassium')
        ph_level = request.form.get('ph_level')
        soil_texture = request.form.get('soil_texture')
        organic_matter = request.form.get('organic_matter')
        recommended_crops = request.form.get('recommended_crops')
        fertilizer_recommendations = request.form.get('fertilizer_recommendations')
        additional_notes = request.form.get('additional_notes')
        
        if existing_report:
            # Update existing report
            soil_reports.update_one(
                {'_id': existing_report['_id']},
                {'$set': {
                    'nitrogen': nitrogen,
                    'phosphorus': phosphorus,
                    'potassium': potassium,
                    'ph_level': ph_level,
                    'soil_texture': soil_texture,
                    'organic_matter': organic_matter,
                    'recommended_crops': recommended_crops,
                    'fertilizer_recommendations': fertilizer_recommendations,
                    'additional_notes': additional_notes,
                    'updated_at': datetime.now()
                }}
            )
        else:
            # Create new report
            soil_reports.insert_one({
                'request_id': ObjectId(request_id),
                'farmer_username': soil_request['farmer_username'],
                'farmer_name': soil_request['farmer_name'],
                'agent_email': agent_email,
                'agent_name': session.get('username'),
                'nitrogen': nitrogen,
                'phosphorus': phosphorus,
                'potassium': potassium,
                'ph_level': ph_level,
                'soil_texture': soil_texture,
                'organic_matter': organic_matter,
                'recommended_crops': recommended_crops,
                'fertilizer_recommendations': fertilizer_recommendations,
                'additional_notes': additional_notes,
                'created_at': datetime.now(),
                'status': 'completed'
            })
        
        # Update request status to completed
        soil_requests.update_one(
            {'_id': ObjectId(request_id)},
            {'$set': {
                'status': 'completed',
                'completed_at': datetime.now()
            }}
        )
        
        # Notify farmer about completed/updated report
        notifications.insert_one({
            'farmer_username': soil_request['farmer_username'],
            'message': f"🌱 Your soil analysis report is ready!\n\nAgent: {session.get('username')}\n\nYou can view your detailed soil analysis and crop recommendations in your dashboard.",
            'status': 'report_completed',
            'notification_type': 'soil_report_completed',
            'is_read': False,
            'created_at': datetime.now()
        })
        
        flash('Soil report updated successfully! Farmer has been notified.')
        return redirect('/soilagent')
    
    return render_template('update_soil_report.html', soil_request=soil_request, existing_report=existing_report)

@app.route('/send-notification-to-agent', methods=['GET', 'POST'])
def send_notification_to_agent():
    if session.get('type') != 'farmer':
        flash('Only farmers can send notifications to agents')
        return redirect('/farmer')
    
    if request.method == 'POST':
        farmer_username = session.get('username')
        agent_email = request.form.get('agent_email')
        message = request.form.get('message')
        notification_type = request.form.get('notification_type', 'farmer_request')
        
        if not agent_email or not message:
            flash('Please select an agent and enter a message')
            return redirect('/send-notification-to-agent')
        
        # Verify agent exists
        agent = db.agentdetails.find_one({'email': agent_email})
        if not agent:
            flash('Selected agent not found')
            return redirect('/send-notification-to-agent')
        
        # Create notification for agent
        notifications.insert_one({
            'agent_email': agent_email,
            'farmer_username': farmer_username,
            'message': message,
            'notification_type': notification_type,
            'status': 'pending',
            'is_read': False,
            'created_at': datetime.now()
        })
        
        # Notify farmer that notification was sent
        notifications.insert_one({
            'farmer_username': farmer_username,
            'message': f"✅ Your notification has been sent to {agent['name']}. They will respond soon.",
            'notification_type': 'notification_sent',
            'is_read': False,
            'created_at': datetime.now()
        })
        
        flash('Notification sent to agent successfully!')
        return redirect('/farmer')
    
    # Get available agents for the farmer's district
    agents = list(db.agentdetails.find({}, {"name": 1, "email": 1, "district": 1, "_id": 0}))
    return render_template('send_notification_to_agent.html', agents=agents)

@app.route('/update-notification-status/<notification_id>', methods=['POST'])
def update_notification_status(notification_id):
    if session.get('type') != 'agent':
        return redirect('/login')
    
    agent_email = session.get('email')
    new_status = request.form.get('status')  # 'update', 'pending', 'complete'
    
    # Verify the notification belongs to this agent
    notification = notifications.find_one({
        '_id': ObjectId(notification_id), 
        'agent_email': agent_email
    })
    
    if notification:
        # Update notification status
        notifications.update_one(
            {'_id': ObjectId(notification_id)},
            {'$set': {
                'status': new_status,
                'updated_at': datetime.now(),
                'is_read': True
            }}
        )
        
        # Notify farmer about status update
        if notification.get('farmer_username'):
            status_messages = {
                'update': f"🔄 Agent {session.get('username')} has updated your request and is working on it.",
                'pending': f"⏳ Agent {session.get('username')} has marked your request as pending.",
                'complete': f"✅ Agent {session.get('username')} has completed your request."
            }
            
            notifications.insert_one({
                'farmer_username': notification['farmer_username'],
                'message': status_messages.get(new_status, f"Agent has updated your request status to {new_status}."),
                'notification_type': 'status_update',
                'is_read': False,
                'created_at': datetime.now()
            })
        
        flash(f'Notification status updated to {new_status.title()} successfully!')
    
    return redirect('/agenthome')

if __name__ == '__main__':
    app.run(debug=True)


for filename in os.listdir(input_dir):
    if filename.endswith('.markdown'):
        with open(os.path.join(input_dir, filename), 'r', encoding='utf-8') as f:
            md_content = f.read()
        html_content = markdown.markdown(md_content, extensions=['extra', 'tables'])
        crop_name = crop_name_from_filename(filename)
        html = HTML_TEMPLATE.format(crop_name=crop_name, content=html_content)
        output_file = os.path.join(output_dir, f"{crop_name.lower().replace(' ', '_')}.html")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"Generated {output_file}")

print("All crop guides converted to HTML!")