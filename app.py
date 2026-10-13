import streamlit as st
import json
import os
from datetime import datetime, date

# ==========================================
# BACKEND MANAGER
# ==========================================

class Expense:
    def __init__(self, description, amount, paid_by, category, expense_id=None, date_added=None):
        self.expense_id = expense_id if expense_id else str(datetime.now().timestamp())
        self.description = description
        self.amount = float(amount)
        self.paid_by = paid_by
        self.category = category
        self.date_added = date_added if date_added else datetime.now().strftime("%Y-%m-%d %H:%M")

    def to_dict(self):
        return {
            "expense_id": self.expense_id,
            "description": self.description,
            "amount": self.amount,
            "paid_by": self.paid_by,
            "category": self.category,
            "date_added": self.date_added
        }

class PlannedBill:
    def __init__(self, name, target_amount, bill_id=None):
        self.bill_id = bill_id if bill_id else str(datetime.now().timestamp())
        self.name = name
        self.target_amount = float(target_amount)

    def to_dict(self):
        return {
            "bill_id": self.bill_id,
            "name": self.name,
            "target_amount": self.target_amount
        }

class UserManager:
    def __init__(self, filename="users.json"):
        self.filename = filename
        self.users = {}
        self.load_users()

    def register_user(self, username, password):
        username = username.strip()
        if not username or not password:
            return False, "Username and password cannot be empty."
        if username in self.users:
            return False, "Username already exists."
        self.users[username] = password
        self.save_users()
        return True, "Account created successfully!"

    def authenticate(self, username, password):
        username = username.strip()
        return self.users.get(username) == password

    def save_users(self):
        with open(self.filename, "w") as f:
            json.dump(self.users, f, indent=4)

    def load_users(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r") as f:
                    self.users = json.load(f)
            except Exception:
                self.users = {}
        else:
            self.users = {"admin": "dorm123"}
            self.save_users()

class DormManager:
    def __init__(self, filename="dorm_data.json"):
        self.filename = filename
        self.roommates = []
        self.planned_bills = []
        self.expenses = []
        self.archives = {}
        self.due_date = ""
        self.load_data()

    def add_roommate(self, name):
        name = name.strip()
        if name != "" and name not in self.roommates:
            self.roommates.append(name)
            self.save_data()
            return True
        return False

    def remove_roommate(self, name):
        if name in self.roommates:
            self.roommates.remove(name)
            self.save_data()
            return True
        return False

    def add_planned_bill(self, name, target_amount):
        if float(target_amount) <= 0:
            raise ValueError("Amount must be greater than zero.")
        bill = PlannedBill(name, target_amount)
        self.planned_bills.append(bill)
        self.save_data()

    def delete_planned_bill(self, bill_id):
        self.planned_bills = [b for b in self.planned_bills if str(b.bill_id) != str(bill_id)]
        self.save_data()

    def add_expense(self, description, amount, paid_by, category):
        if float(amount) <= 0:
            raise ValueError("Amount must be greater than zero.")
        exp = Expense(description, amount, paid_by, category)
        self.expenses.append(exp)
        self.save_data()

    def delete_expense(self, expense_id):
        self.expenses = [e for e in self.expenses if str(e.expense_id) != str(expense_id)]
        self.save_data()

    def set_due_date(self, date_str):
        self.due_date = date_str
        self.save_data()

    def archive_current_month(self):
        if not self.expenses and not self.planned_bills:
            return False
        archive_key = datetime.now().strftime("%B %Y (%Y-%m-%d)")
        self.archives[archive_key] = {
            "roommates": list(self.roommates),
            "planned_bills": [b.to_dict() for b in self.planned_bills],
            "expenses": [e.to_dict() for e in self.expenses]
        }
        self.expenses = []
        self.planned_bills = []
        self.save_data()
        return True

    def calculate_balances(self):
        if not self.roommates:
            return {}
        balances = {r: 0.0 for r in self.roommates}
        num_people = len(self.roommates)
        for exp in self.expenses:
            split_amount = exp.amount / num_people
            for r in self.roommates:
                if r == exp.paid_by:
                    balances[r] += (exp.amount - split_amount)
                else:
                    balances[r] -= split_amount
        return balances

    def calculate_settlements(self):
        balances = self.calculate_balances()
        debtors = []
        creditors = []
        for name, bal in balances.items():
            if bal < -0.01:
                debtors.append([name, abs(bal)])
            elif bal > 0.01:
                creditors.append([name, bal])

        debtors.sort(key=lambda x: x[1], reverse=True)
        creditors.sort(key=lambda x: x[1], reverse=True)

        settlements = []
        d_idx = 0
        c_idx = 0
        while d_idx < len(debtors) and c_idx < len(creditors):
            debtor_name, debtor_amt = debtors[d_idx]
            creditor_name, creditor_amt = creditors[c_idx]
            pay_amount = min(debtor_amt, creditor_amt)
            settlements.append({"from": debtor_name, "to": creditor_name, "amount": pay_amount})
            debtors[d_idx][1] -= pay_amount
            creditors[c_idx][1] -= pay_amount
            if debtors[d_idx][1] < 0.01:
                d_idx += 1
            if creditors[c_idx][1] < 0.01:
                c_idx += 1
        return settlements

    def save_data(self):
        data = {
            "roommates": self.roommates,
            "planned_bills": [b.to_dict() for b in self.planned_bills],
            "expenses": [e.to_dict() for e in self.expenses],
            "archives": self.archives,
            "due_date": self.due_date
        }
        with open(self.filename, "w") as f:
            json.dump(data, f, indent=4)

    def load_data(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r") as f:
                    data = json.load(f)
                    self.roommates = data.get("roommates", [])
                    self.archives = data.get("archives", {})
                    self.due_date = data.get("due_date", "")
                    
                    raw_bills = data.get("planned_bills", [])
                    self.planned_bills = [PlannedBill(b["name"], b["target_amount"], b.get("bill_id")) for b in raw_bills]
                    
                    raw_exp = data.get("expenses", [])
                    self.expenses = [
                        Expense(item["description"], item["amount"], item["paid_by"], item["category"], item.get("expense_id"), item.get("date_added"))
                        for item in raw_exp
                    ]
            except Exception:
                self.roommates = []
                self.planned_bills = []
                self.expenses = []
                self.archives = {}
                self.due_date = ""

# ==========================================
# STREAMLIT UI DESIGN
# ==========================================

st.set_page_config(page_title="Dorm Expense Splitter", page_icon="🌸", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #FFF0F5 0%, #E6F3FF 100%);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    h1, h2, h3 {
        color: #4A4E69 !important;
    }
    div[data-testid="stMetric"], .stForm {
        background-color: rgba(255, 255, 255, 0.85) !important;
        padding: 18px !important;
        border-radius: 15px !important;
        border: 1px solid #E0C3FC !important;
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.03);
    }
    .stButton > button {
        border-radius: 10px !important;
        background-color: #F8EDEB !important;
        color: #4A4E69 !important;
        border: 1px solid #FEC5BB !important;
        font-weight: 600 !important;
    }
    .stButton > button:hover {
        background-color: #E8AEB7 !important;
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

user_mgr = UserManager()

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "current_user" not in st.session_state:
    st.session_state.current_user = ""

def auth_screen():
    st.title("🌸 Dorm Expense Tracker")
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Create Account"])
    with tab1:
        st.subheader("Login to Your Account")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("🔓 Login", use_container_width=True):
                if user_mgr.authenticate(username, password):
                    st.session_state.authenticated = True
                    st.session_state.current_user = username
                    st.success(f"Welcome back, {username}!")
                    st.rerun()
                else:
                    st.error("Invalid Username or Password!")
    with tab2:
        st.subheader("Register New Account")
        with st.form("register_form"):
            new_user = st.text_input("Choose Username")
            new_pass = st.text_input("Choose Password", type="password")
            confirm_pass = st.text_input("Confirm Password", type="password")
            if st.form_submit_button("✨ Create Account", use_container_width=True):
                if new_pass != confirm_pass:
                    st.error("Passwords do not match!")
                else:
                    success, msg = user_mgr.register_user(new_user, new_pass)
                    if success: st.success(msg)
                    else: st.error(msg)

if not st.session_state.authenticated:
    auth_screen()
    st.stop()

manager = DormManager()

st.title("🌸 Dorm Expense Splitter & Utility Tracker")
st.caption(f"Logged in as: *{st.session_state.current_user}*")

# Sidebar
st.sidebar.header("⚙️ Management")
if st.sidebar.button("🚪 Logout", use_container_width=True):
    st.session_state.authenticated = False
    st.session_state.current_user = ""
    st.rerun()

st.sidebar.write("---")
st.sidebar.subheader("👥 Roommates")
new_name = st.sidebar.text_input("Add Roommate:", placeholder="e.g. Maria")
if st.sidebar.button("➕ Add Person", use_container_width=True):
    if manager.add_roommate(new_name):
        st.sidebar.success(f"Added {new_name}")
        st.rerun()
    else:
        st.sidebar.error("Invalid or duplicate name.")

if manager.roommates:
    st.sidebar.write("---")
    st.sidebar.write("Current Roommates:")
    for name in manager.roommates:
        col_r1, col_r2 = st.sidebar.columns([3, 1])
        col_r1.write(f"• *{name}*")
        if col_r2.button("❌", key=f"del_rm_{name}"):
            manager.remove_roommate(name)
            st.rerun()

st.sidebar.write("---")
st.sidebar.subheader("📅 Monthly Due Date")
selected_due = st.sidebar.date_input("Set Bill Due Date", value=datetime.now().date())
if st.sidebar.button("Save Due Date", use_container_width=True):
    manager.set_due_date(selected_due.strftime("%Y-%m-%d"))
    st.sidebar.success("Due date saved!")
    st.rerun()

st.sidebar.write("---")
st.sidebar.subheader("📦 End of Month Action")
if st.sidebar.button("📁 Archive Month & Reset", use_container_width=True):
    if manager.archive_current_month():
        st.sidebar.success("Archived successfully!")
        st.rerun()
    else:
        st.sidebar.warning("No data to archive.")

# Main Layout
col1, col2 = st.columns([1.7, 1.3], gap="large")

with col1:
    # 1. Planned Bills (Total Target Amount & Exact Equal Split per person)
    st.subheader("📋 1. Planned Bills & Exact Share per Person")
    with st.form("planned_bill_form", clear_on_submit=True):
        b_name = st.text_input("Bill Name", placeholder="e.g. Food Budget, Meralco Bill, Rent")
        b_amount = st.number_input("Total Amount (PHP)", min_value=0.0, step=100.0)
        
        if st.form_submit_button("📌 Add Planned Bill", use_container_width=True):
            try:
                manager.add_planned_bill(b_name, b_amount)
                st.success("Planned bill added successfully!")
                st.rerun()
            except ValueError as err:
                st.error(str(err))

    if manager.planned_bills:
        st.write("List of Expected Bills & Exact Split:")
        total_planned = sum(b.target_amount for b in manager.planned_bills)
        num_roommates = len(manager.roommates) if manager.roommates else 1
        
        for b in manager.planned_bills:
            share_per_person = b.target_amount / num_roommates
            b_col1, b_col2, b_col3, b_col4 = st.columns([2.5, 1.5, 1.8, 0.8])
            b_col1.write(f"• *{b.name}*")
            b_col2.write(f"₱{b.target_amount:,.2f}")
            b_col3.caption(f"Exact Share: ₱{share_per_person:,.2f}")
            if b_col4.button("🗑️", key=f"del_pb_{b.bill_id}"):
                manager.delete_planned_bill(b.bill_id)
                st.rerun()
                
        total_share_per_person = total_planned / num_roommates
        st.info(f"💡 *Total Planned Bills:* ₱{total_planned:,.2f} | *Exact Total Share per Person:* ₱{total_share_per_person:,.2f}")
    else:
        st.caption("No planned bills added yet.")

    st.write("---")

    # 2. Actual Expenses (Who Paid)
    st.subheader("📝 2. Record Who Paid (Actual Expenses)")
    if not manager.roommates:
        st.warning("Please add roommates in the sidebar first.")
    else:
        with st.form("expense_form", clear_on_submit=True):
            desc = st.text_input("Payment Description", placeholder="e.g. Paid Meralco bill at center")
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                amount = st.number_input("Amount Paid (PHP)", min_value=0.0, step=50.0)
            with f_col2:
                paid_by = st.selectbox("Paid By", manager.roommates)
                
            category = st.selectbox("Category", [
                "Food & Groceries", 
                "Electricity (Meralco)", 
                "Water Bill / Refill", 
                "Cooking Gas (LPG)", 
                "Internet / Wi-Fi", 
                "House Rent", 
                "Others"
            ])
            
            if st.form_submit_button("💖 Save Payment", use_container_width=True):
                try:
                    manager.add_expense(desc, amount, paid_by, category)
                    st.success("Payment recorded successfully!")
                    st.rerun()
                except ValueError as err:
                    st.error(str(err))

    st.subheader("📜 Payment History")
    if manager.expenses:
        for idx, exp in enumerate(manager.expenses):
            e_col1, e_col2, e_col3 = st.columns([3.5, 2, 1])
            with e_col1:
                st.write(f"*{exp.description}* ({exp.category})")
                st.caption(f"Paid by: *{exp.paid_by}* | Date: {exp.date_added}")
            with e_col2:
                st.write(f"💵 *₱{exp.amount:,.2f}*")
            with e_col3:
                if st.button("🗑️", key=f"del_exp_{exp.expense_id}_{idx}"):
                    manager.delete_expense(exp.expense_id)
                    st.rerun()
            st.divider()
    else:
        st.info("No payments recorded yet.")

    # 🧮 MINI CALCULATOR
    st.write("---")
    st.subheader("🧮 Mini Calculator")
    calc_input = st.text_input("Type math expression here (e.g. 3500 + 3000 / 3):", placeholder="Enter math formula")
    if calc_input:
        try:
            allowed_chars = set("0123456789+-*/(). ")
            if all(c in allowed_chars for c in calc_input):
                result = eval(calc_input)
                st.success(f"Result: *{result:,.2f}*")
            else:
                st.error("Only numbers and basic math operators are allowed.")
        except Exception:
            st.error("Invalid math expression format.")

with col2:
    st.subheader("💳 Balances & Settlements")
    total_paid_actual = sum(e.amount for e in manager.expenses)
    st.metric(label="💰 Total Amount Paid So Far", value=f"₱{total_paid_actual:,.2f}")
    
    balances = manager.calculate_balances()
    if balances:
        st.write("---")
        
        # 👑 DITO ANG HIWALAY NA TABLE PARA SA MGA SAKTO MAGBAYAD (EXACT / FULLY SETTLED TABLE)
        st.subheader("✨ Exact Payers Table (Fully Settled)")
        exact_payers = [name for name, bal in balances.items() if abs(bal) <= 0.01]
        
        if exact_payers:
            # Gumawa tayo ng magandang structured table gamit ang dataframe para mukhang table talaga
            table_data = [{"Roommate Name": name, "Status": "Fully Settled (Exact Share)"} for name in exact_payers]
            st.dataframe(table_data, use_container_width=True)
        else:
            st.info("No roommates have fully settled their exact share yet.")
            
        st.write("---")
        st.subheader("📊 Other Balances")
        for name, bal in balances.items():
            if abs(bal) > 0.01:
                if bal > 0.01:
                    st.metric(label=f"👑 {name} (Overpaid / To Receive)", value=f"₱{bal:,.2f}", delta="To Receive")
                else:
                    st.metric(label=f"🔴 {name} (Underpaid / Needs to Pay)", value=f"₱{abs(bal):,.2f}", delta=f"-₱{abs(bal):,.2f}", delta_color="inverse")
        
        st.write("---")
        st.subheader("💸 Suggested Settlements")
        settlements = manager.calculate_settlements()
        if settlements:
            for s in settlements:
                st.markdown(f"👉 *{s['from']}* pay *{s['to']}* ➔ *₱{s['amount']:,.2f}*")
        else:
            st.success("✨ Everything is balanced and settled!")
    else:
        st.info("Add roommates to compute balances.")

    st.write("---")
    st.subheader("🗂️ Archived Records")
    if manager.archives:
        sel_month = st.selectbox("Select Past Month:", list(manager.archives.keys()))
        if sel_month:
            archived_data = manager.archives[sel_month]
            past_list = [{"Date": i.get("date_added"), "Details": i["description"], "Amount": f"₱{i['amount']:,.2f}", "Paid By": i["paid_by"]} for i in archived_data.get("expenses", [])]
            if past_list:
                st.dataframe(past_list, use_container_width=True)
    else:
        st.caption("No archives found.")