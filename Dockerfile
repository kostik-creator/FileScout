FROM python:3.12
WORKDIR /app
COPY . .
RUN pip install --upgrade setuptools
RUN pip install --no-cache-dir -r requirements.txt
ENTRYPOINT [ "python" , "main.py" ]