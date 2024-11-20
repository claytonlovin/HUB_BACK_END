FROM python:3.12

WORKDIR /backend

COPY /backend .

RUN pip install virtualenv
RUN python -m virtualenv venv

RUN /bin/bash -c "source venv/bin/activate"

RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -

RUN curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list

RUN apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql17 unixodbc-dev unixodbc && \
    ldconfig

RUN pip install -r requirements.txt

EXPOSE 8000

CMD ["gunicorn", "app:app", "--workers", "2", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
