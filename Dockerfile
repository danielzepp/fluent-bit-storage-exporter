FROM python:3.6-slim-buster
LABEL maintainer="Dan kim <dan@hpcnt.com>"

RUN adduser --disabled-password worker
USER worker
WORKDIR /home/worker
ENV PATH="/home/worker/.local/bin/:${PATH}"

COPY --chown=worker:worker requirements.txt ./
RUN pip install -r requirements.txt --user
COPY --chown=worker:worker . .

ENTRYPOINT ["/home/worker/run.sh"]
EXPOSE 8080