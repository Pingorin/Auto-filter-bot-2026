# Dockerfile

# Base Image: Python ki light-weight image use karenge
FROM python:3.10-slim

# Working directory set karte hain
WORKDIR /app

# Requirements file ko container mein copy karte hain
COPY requirements.txt .

# Dependencies install karte hain
RUN pip install --no-cache-dir -r requirements.txt

# Baaki saara code copy karte hain
COPY . .

# Bot ko run karne ka command:
# CMD [ "python", "bot.py" ]
# Lekin Railway/Render mein hum CMD ki jagah seedha Start Command denge.
# Hum yahan sirf entry point define karte hain.
ENTRYPOINT [ "python", "bot.py" ]
