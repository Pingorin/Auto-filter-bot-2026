# Dockerfile

# Base Image: Python ki latest stable version ka upyog
FROM python:3.11-slim

# Working Directory set karna
WORKDIR /usr/src/app

# requirements.txt file ko container mein copy karna
COPY requirements.txt .

# Dependencies install karna
# --no-cache-dir: Disk space aur build time bachane ke liye
RUN pip install --no-cache-dir -r requirements.txt

# Baaki saara code (bot.py aur config.py) ko container mein copy karna
COPY . .

# Bot ko run karne ke liye default command.
# CMD command Docker container shuru hone par run hoti hai.
CMD ["python", "bot.py"]
