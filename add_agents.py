
from convert_crops import app, bcrypt
from pymongo import MongoClient

# Setup
client = MongoClient('mongodb://localhost:27017/')
db = client['your_db']
agentdetails = db.agentdetails

# List of agents (from agent.html)
agents = [
    {"name": "Ramesh Yadav", "email": "ramesh.adilabad@agri.com", "phone": "9876543201", "district": "Adilabad"},
    {"name": "Sushma Reddy", "email": "sushma.kothagudem@agri.com", "phone": "9876543202", "district": "Bhadradri Kothagudem"},
    {"name": "Praveen Kumar", "email": "praveen.hanamkonda@agri.com", "phone": "9876543203", "district": "Hanamkonda"},
    {"name": "Kavitha Laxmi", "email": "kavitha.hyderabad@agri.com", "phone": "9876543204", "district": "Hyderabad"},
    {"name": "Sandeep Naik", "email": "sandeep.jagtial@agri.com", "phone": "9876543205", "district": "Jagtial"},
    {"name": "Divya Chary", "email": "divya.jangaon@agri.com", "phone": "9876543206", "district": "Jangaon"},
    {"name": "Srikanth Goud", "email": "srikanth.bhupalapally@agri.com", "phone": "9876543207", "district": "Jayashankar Bhupalapally"},
    {"name": "Bhavana Patil", "email": "bhavana.gadwal@agri.com", "phone": "9876543208", "district": "Jogulamba Gadwal"},
    {"name": "Rafiuddin Shaik", "email": "rafi.kamareddy@agri.com", "phone": "9876543209", "district": "Kamareddy"},
    {"name": "Venu Madhav", "email": "venu.karimnagar@agri.com", "phone": "9876543210", "district": "Karimnagar"},
    {"name": "Swapna Rao", "email": "swapna.khammam@agri.com", "phone": "9876543211", "district": "Khammam"},
    {"name": "Rajeshwar Goud", "email": "rajeshwar.kb@agri.com", "phone": "9876543212", "district": "Komaram Bheem Asifabad"},
    {"name": "Anjali Sharma", "email": "anjali.mahabubabad@agri.com", "phone": "9876543213", "district": "Mahabubabad"},
    {"name": "Srinivas Rao", "email": "srinivas.mbnr@agri.com", "phone": "9876543214", "district": "Mahabubnagar"},
    {"name": "Farida Begum", "email": "farida.mancherial@agri.com", "phone": "9876543215", "district": "Mancherial"},
    {"name": "Ganesh Reddy", "email": "ganesh.medak@agri.com", "phone": "9876543216", "district": "Medak"},
    {"name": "Chandana Das", "email": "chandana.medchal@agri.com", "phone": "9876543217", "district": "Medchal-Malkajgiri"},
    {"name": "Vijay Singh", "email": "vijay.mulugu@agri.com", "phone": "9876543218", "district": "Mulugu"},
    {"name": "Laxman B", "email": "laxman.nagarkurnool@agri.com", "phone": "9876543219", "district": "Nagarkurnool"},
    {"name": "Padma S", "email": "padma.nalgonda@agri.com", "phone": "9876543220", "district": "Nalgonda"},
    {"name": "Naresh P", "email": "naresh.narayanpet@agri.com", "phone": "9876543221", "district": "Narayanpet"},
    {"name": "Sai Teja", "email": "saiteja.nirmal@agri.com", "phone": "9876543222", "district": "Nirmal"},
    {"name": "Lavanya K", "email": "lavanya.nizamabad@agri.com", "phone": "9876543223", "district": "Nizamabad"},
    {"name": "Sruthi V", "email": "sruthi.peddapalli@agri.com", "phone": "9876543224", "district": "Peddapalli"},
    {"name": "Nagaraju T", "email": "nagaraju.sircilla@agri.com", "phone": "9876543225", "district": "Rajanna Sircilla"},
    {"name": "Meena Kumari", "email": "meena.rangareddy@agri.com", "phone": "9876543226", "district": "Rangareddy"},
    {"name": "Kiran R", "email": "kiran.sangareddy@agri.com", "phone": "9876543227", "district": "Sangareddy"},
    {"name": "Tejaswini D", "email": "tejaswini.siddipet@agri.com", "phone": "9876543228", "district": "Siddipet"},
    {"name": "Akhil M", "email": "akhil.suryapet@agri.com", "phone": "9876543229", "district": "Suryapet"},
    {"name": "Harsha V", "email": "harsha.vikarabad@agri.com", "phone": "9876543230", "district": "Vikarabad"},
    {"name": "Deepthi J", "email": "deepthi.wanaparthy@agri.com", "phone": "9876543231", "district": "Wanaparthy"},
    {"name": "Anand Rao", "email": "anand.warangal@agri.com", "phone": "9876543232", "district": "Warangal"},
    {"name": "Shalini B", "email": "shalini.yadadri@agri.com", "phone": "9876543233", "district": "Yadadri Bhuvanagiri"},
]

with app.app_context():
    agentdetails.delete_many({})  # Clear old records
    for agent in agents:
        username = agent["email"].split("@")[0]
        password = bcrypt.generate_password_hash("all1234").decode('utf-8')
        agent_record = {
            "username": username,
            "password": password,
            "name": agent["name"],
            "email": agent["email"],
            "phone": agent["phone"],
            "district": agent["district"],
            "type": "soil_agent"
        }
        agentdetails.insert_one(agent_record)

print("All agent credentials added to the database.") 

