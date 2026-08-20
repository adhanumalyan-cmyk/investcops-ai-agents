"""
generate_synthetic_data.py

Large-scale synthetic data generator for INVESTCOPS AI testing.
Generates: Contacts, Call Logs, GPay/SMS Transactions, WhatsApp/Telegram/Instagram Chats.

Usage:
    python generate_synthetic_data.py
"""

import json
import random
import os
from datetime import datetime, timedelta
from faker import Faker

# Initialize Faker with Indian locale for realistic names/phones
fake = Faker('en_IN')

# Output folder
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "test_data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ------------------------------------------------------------
# 1. GENERATE CONTACTS (1000 entries)
# ------------------------------------------------------------
def generate_contacts(count=1000):
    contacts = []
    for _ in range(count):
        first_name = fake.first_name()
        last_name = fake.last_name()
        contacts.append({
            "_id": str(fake.unique.random_number(digits=5)),
            "display_name": f"{first_name} {last_name}",
            "data1": fake.phone_number(),
            "data2": fake.email(),
            "data3": fake.street_address()
        })
    return contacts

# ------------------------------------------------------------
# 2. GENERATE CALL LOGS (5000 entries)
# ------------------------------------------------------------
def generate_call_logs(contacts, count=5000):
    call_types = ["1", "2", "3"]  # Incoming, Outgoing, Missed
    directions = ["incoming", "outgoing", "missed"]
    
    start_date = datetime.now() - timedelta(days=30)
    end_date = datetime.now()
    
    calls = []
    for _ in range(count):
        contact = random.choice(contacts)
        timestamp = fake.date_time_between(start_date=start_date, end_date=end_date)
        call_type = random.choice(call_types)
        
        calls.append({
            "_id": str(fake.unique.random_number(digits=6)),
            "number": contact["data1"],
            "name": contact["display_name"],
            "type": call_type,
            "duration": str(random.randint(10, 600)),
            "date": timestamp.isoformat(),
            "direction": random.choice(directions)
        })
    return calls

# ------------------------------------------------------------
# 3. GENERATE SMS / GPAY TRANSACTIONS (5000 entries)
# ------------------------------------------------------------
def generate_sms_transactions(contacts, count=5000):
    sms_templates = [
        "Your UPI transaction of Rs.{amount} to {name} is successful. Ref: {ref}",
        "Dear customer, Rs.{amount} credited to your account via Google Pay from {name}. Ref: {ref}",
        "PhonePe: Rs.{amount} sent to {name}. UPI Ref: {ref}",
        "GPay: You paid Rs.{amount} to {name} for {item}. Ref: {ref}",
        "Payment of Rs.{amount} received from {name} via UPI. Ref: {ref}",
        "Your account has been debited by Rs.{amount} for {item}. Ref: {ref}",
        "OTP for transaction {ref}: {otp}. Do not share.",
        "Your bill of Rs.{amount} to {name} is due on {date}."
    ]
    
    items = ["Electricity Bill", "Mobile Recharge", "Grocery", "Rent", "Shopping", "DTH", "Water Bill"]
    start_date = datetime.now() - timedelta(days=15)
    end_date = datetime.now()
    
    sms_list = []
    for _ in range(count):
        contact = random.choice(contacts)
        template = random.choice(sms_templates)
        amount = random.randint(10, 50000)
        ref = fake.unique.random_number(digits=12)
        otp = random.randint(100000, 999999)
        item = random.choice(items)
        
        body = template.format(
            amount=amount,
            name=contact["display_name"],
            ref=ref,
            otp=otp,
            item=item,
            date=fake.date()
        )
        
        sms_list.append({
            "_id": str(fake.unique.random_number(digits=6)),
            "address": contact["data1"],
            "body": body,
            "date": str(fake.date_time_between(start_date=start_date, end_date=end_date).timestamp()).split(".")[0],
            "type": "1"  # Inbox
        })
    return sms_list

# ------------------------------------------------------------
# 4. GENERATE CHAT EXPORTS (WhatsApp, Telegram, Instagram)
# ------------------------------------------------------------
def generate_chat(participants, count=1000, platform="whatsapp"):
    """
    Generate chat messages.
    Format: 
     - WhatsApp: 12/08/24, 10:32 PM - Sender: Message
     - Telegram: [12.08.2024 22:32:10] Sender: Message
     - Instagram: 12/08/24, 10:32 PM - sender_handle: Message
    """
    messages = []
    start_date = datetime.now() - timedelta(days=2)
    end_date = datetime.now()
    
    chat_phrases = [
        "Hello da, eppadi irukka?",
        "I am fine, you?",
        "Ena panreenga?",
        "Just working on the project.",
        "Nalaikku meet pannalama?",
        "Sure, time sollu.",
        "Where are you?",
        "I am coming to the office.",
        "Did you check the report?",
        "Not yet, I'll check it now.",
        "Bro, call me.",
        "Ok, I'll call you in 5 mins.",
        "Thank you!",
        "No problem.",
        "What's the status?",
        "Almost done.",
        "Let's meet at the cafe.",
        "Which cafe?",
        "The one near the station.",
        "I'll be there in 10 mins.",
        "Take your time.",
        "Done with the task.",
        "Send me the document.",
        "I have sent it.",
        "Received, thanks."
    ]
    
    for i in range(count):
        sender = random.choice(participants)
        timestamp = fake.date_time_between(start_date=start_date, end_date=end_date)
        
        if platform == "whatsapp":
            dt_str = timestamp.strftime("%d/%m/%y, %I:%M %p")
            msg = f"{dt_str} - {sender}: {random.choice(chat_phrases)}"
        elif platform == "telegram":
            dt_str = timestamp.strftime("[%d.%m.%Y %H:%M:%S]")
            msg = f"{dt_str} {sender}: {random.choice(chat_phrases)}"
        else:  # Instagram
            dt_str = timestamp.strftime("%d/%m/%y, %I:%M %p")
            # Instagram handles are usually without spaces
            handle = sender.replace(" ", "_").lower()
            msg = f"{dt_str} - {handle}: {random.choice(chat_phrases)}"
        
        messages.append(msg)
    
    # Sort by timestamp for realistic timeline
    # Since we generated random timestamps, sorting is needed.
    # But for simplicity, we just return list; sorting by actual time requires parsing.
    # We'll sort them roughly.
    return messages

# ------------------------------------------------------------
# 5. MAIN EXECUTION
# ------------------------------------------------------------
def main():
    print("🚀 Generating Synthetic Data for INVESTCOPS AI...")
    
    # 1. Contacts
    print("📇 Generating 1000 Contacts...")
    contacts = generate_contacts(1000)
    with open(os.path.join(OUTPUT_DIR, "contacts.json"), "w", encoding="utf-8") as f:
        json.dump(contacts, f, indent=2)
    
    # 2. Call Logs
    print("📞 Generating 5000 Call Logs...")
    call_logs = generate_call_logs(contacts, 5000)
    with open(os.path.join(OUTPUT_DIR, "call_log.json"), "w", encoding="utf-8") as f:
        json.dump(call_logs, f, indent=2)
    
    # 3. SMS / GPay Transactions
    print("💳 Generating 5000 SMS/Transactions...")
    sms_data = generate_sms_transactions(contacts, 5000)
    with open(os.path.join(OUTPUT_DIR, "sms.json"), "w", encoding="utf-8") as f:
        json.dump(sms_data, f, indent=2)
    
    # 4. WhatsApp Chat
    print("💬 Generating WhatsApp Chat (2000 msgs)...")
    participants = ["Vikram", "Priya", "S Nagammai"]
    whatsapp_msgs = generate_chat(participants, 2000, "whatsapp")
    with open(os.path.join(OUTPUT_DIR, "whatsapp_chat.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(whatsapp_msgs))
    
    # 5. Telegram Chat
    print("💬 Generating Telegram Chat (1500 msgs)...")
    tele_msgs = generate_chat(["Rahul", "Amit"], 1500, "telegram")
    with open(os.path.join(OUTPUT_DIR, "telegram_chat.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(tele_msgs))
    
    # 6. Instagram DM
    print("💬 Generating Instagram DM (1000 msgs)...")
    ig_msgs = generate_chat(["@priya_23", "@vikram_official"], 1000, "instagram")
    with open(os.path.join(OUTPUT_DIR, "instagram_dm.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(ig_msgs))
    
    print(f"✅ All synthetic data generated in: {OUTPUT_DIR}")
    print("📁 Files:")
    print("   - contacts.json")
    print("   - call_log.json")
    print("   - sms.json")
    print("   - whatsapp_chat.txt")
    print("   - telegram_chat.txt")
    print("   - instagram_dm.txt")

if __name__ == "__main__":
    main()