from umongo import Document, fields
from umongo.frameworks.motor import MotorCollection
from info import Config

# User Document Model
@Config.db_instance.register
class User(Document):
    # MongoDB mein collection ka naam 'users' hoga
    collection = MotorCollection(Config.DATABASE_NAME, "users") 
    
    # User ka Telegram ID
    id = fields.IntField(attribute="_id", required=True) 
    
    # User ka naam/first_name
    name = fields.StrField(required=True) 
    
    # User jab joda gaya tha
    joined_date = fields.DateTimeField(required=True, default=lambda: fields.datetime.datetime.utcnow())
    
    # Future mein aur fields yahan jod sakte hain

# Database Class jismein functions honge
class Database:
    def __init__(self):
        self.User = User

    async def add_user(self, id: int, name: str):
        """Database mein naye user ko jodein."""
        try:
            # User Model ka naya instance banayein aur save karein
            await self.User(id=id, name=name).commit()
        except Exception as e:
            # Agar user pehle se exist karta hai toh koi action na lein
            if "E11000 duplicate key" not in str(e):
                print(f"Error adding user {id}: {e}")

    async def is_user_exist(self, id: int) -> bool:
        """Check karein ki user database mein hai ya nahi."""
        # find_one_or_404 se check karein ki document exist karta hai ya nahi
        user = await self.User.find_one({"_id": id})
        return bool(user)

# Bot ko access karne ke liye instance
db = Database() 
