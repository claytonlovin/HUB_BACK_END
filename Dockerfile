FROM python:3.12

WORKDIR /back_api

COPY /back_api .
COPY /requirements.txt .

RUN pip install virtualenv
RUN python -m virtualenv venv
RUN /bin/bash -c "source venv/bin/activate"

RUN pip install -r requirements.txt


EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
