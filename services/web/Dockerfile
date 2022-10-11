# pull official base image
FROM python:3.9.5-slim-buster

# set work directory
WORKDIR /usr/src/app
COPY . .

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONBUFFERED 1

# install system dependencies
RUN apt-get update && apt-get install -y netcat

# install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy environment file
RUN chmod +x entrypoint.sh

# Expose port
EXPOSE 5001
EXPOSE 8080

# run entrypoint
# CMD ["python", "manage.py", "run", "-h", "0.0.0.0"]
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]