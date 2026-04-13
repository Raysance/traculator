# Traculator - Minimalist Group Bookkeeping & Expense Splitting Service

Traculator is a pure, lightweight multi-user bookkeeping tool. With a simple 6-digit code, you can quickly create or join a shared ledger. It features automatic expense splitting and intelligent settlement, making it perfect for scenarios like dining with friends, splitting rent with roommates, or group travel where AA calculation or complex bookkeeping is needed.

**🌍 Try it now:** [zhdxlz.top/traculator](https://zhdxlz.top/traculator)

## ✨ Core Features

- **Minimalist Access**: No tedious registration process or account binding. Simply enter a 6-digit code to enter your exclusive ledger (it's automatically created upon the first entry).
- **Intelligent Settlement (Middleman)**: Any member can be set as the "Payment/Collection Center". Once enabled, the system automatically simplifies complex, cross-cutting point-to-point debts among multiple people into single-line payments to/from the "Middleman". See at a glance who owes how much or should receive how much!
- **Multi-dimensional Billing**:
  - Fine-grained management of various expenses, with freedom to choose the payer.
  - Supports precise AA splitting; you can manually select "who actually participated in the cost sharing".
  - **Geotagging**: Built-in one-click real-time positioning. Just click "Get Location" when recording an entry, and it will record your current street address, leaving a footprint for every transaction.
- **Data Control**: Supports one-click full export of the ledger to a local file for backup.
- **Superior Experience**: A fully responsive modern interface provides a smooth, App-like experience on any mobile or desktop browser.

## 📖 User Guide

**1. Start Your Exclusive Ledger**
Enter an agreed 6-digit password (e.g., `123456`) on the homepage to enter the shared ledger space with your friends.

**2. Add Group Members**
After entering the app, click [Settings] in the top navigation bar to enter and add the names of all friends participating in the activity (dining/travel, etc.).

**3. Streamline Settlement (Set a Middleman)**
In the [Settings] panel, select a member as the "Middleman" (usually the record keeper or the primary payer).
Once set, you no longer have to worry about "A transfers to B, and C pays back A". The system will consolidate all messy accounts and calculate the final balance for everyone relative to the middleman!

**4. Record an Expense**
Click the ➕ floating button at the bottom right to record a bill:
* Enter the description (e.g., "Japanese Dinner", "Hotel Accommodation") and the total amount.
* Select who originally paid for this item.
* Check the members who are actually sharing this cost. If someone is not involved, simply uncheck them.
* Click **"Get Location"**, and the system will intelligently identify your current street to document the memory.
* Confirm and save the record.

**5. Clear the Balance**
In the "Settlement Results" panel at the bottom of the main screen, you can view the final splitting results of the group at any time.
* **Green (Positive)**: Represents "You need to transfer this amount to the middleman".
* **Red (Negative)**: Represents "You have overpaid, and the middleman needs to refund the amount you advanced".

---

## 🛠️ Self-Hosting (Developer Guide)

If you wish to run Traculator on your own server, follow these steps for quick installation and startup:

**1. Environment Preparation**
* Install Python 3.8 or above.
* Install and start [Redis](https://redis.io/) (default connection `127.0.0.1:6379`).

**2. Install Dependencies**
After cloning the project, run the following command in the root directory to install the required Python dependencies:
```bash
pip install -r requirements.txt
```

**3. Start the Service**
Start the FastAPI service:
```bash
python server.py
# Or use uvicorn directly: uvicorn server:app --host 0.0.0.0 --port 8001
```
Once the service is running, access `http://localhost:8001/traculator/` in your browser.
